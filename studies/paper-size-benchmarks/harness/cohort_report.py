"""Combine complete, fingerprint-matched serial runs; preserve paired samples."""
import argparse
from collections import defaultdict
import json
import hashlib
import math
from pathlib import Path
import statistics

def require(condition, message):
    if not condition:
        raise ValueError(message)

def read(path):
    return json.loads(path.read_text())

def stats(values):
    return dict(samples=values, n=len(values), mean=statistics.mean(values), median=statistics.median(values), min=min(values), max=max(values), stdev=statistics.stdev(values) if len(values) > 1 else None)

def fingerprint(run):
    (config, build, env) = (read(run / name) for name in ('configuration.json', 'frozen-build.json', 'environment.json'))
    keys = ('suite', 'profile', 'only', 'native_transform', 'assume_directory_access', 'content_validated_inputs', 'annotations', 'manifest_sha256', 'harness_sha256')
    return dict(config={k: config.get(k) for k in keys}, revisions=build['revisions'], frozen_files=build['sha256'], sources=env['source_fingerprints'], baseline_patch=env['original_baseline_patch'], packages=env['packages'], tools=env['tool_versions'], dictionary=env['dictionary_sha256'], inputs={p.name: read(p) for p in sorted((run / 'inputs').glob('*.json'))})

def combine(paths):
    runs = [r.resolve() for r in paths]
    require(bool(runs), 'No runs supplied')
    require(len(set(runs)) == len(runs), 'Duplicate run')
    canonical = fingerprint(runs[0])
    (by_version, by_family) = (defaultdict(dict), defaultdict(lambda : defaultdict(float)))
    by_edited = defaultdict(lambda : defaultdict(float))
    scripts = {b['name']: b['scripts'] for b in read(runs[0] / 'manifest.json')['benchmarks']}
    pairs = []
    for run in runs:
        require(fingerprint(run) == canonical, f'Fingerprint mismatch: {run}')
        (config, summary) = (read(run / 'configuration.json'), read(run / 'summary.json'))
        require(set(config['modes']) == {'bash', 'original', 'observe'}, 'Invalid cohort evidence')
        require(read(run / 'status.json')['state'] == 'complete', 'Invalid cohort evidence')
        require(summary['complete'] and (not summary['failed_sequences']), 'Invalid cohort evidence')
        require(summary['invocations'] == summary['expected_invocations'] == summary['valid_invocations'], 'Invalid cohort evidence')
        monitor = read(run / 'monitor.json')
        require(monitor['health'] == 'ok' and monitor['run_state'] == 'complete'
                and not monitor['failed_samples'] and not monitor['monitor_issues']
                and monitor['recorded'] == monitor['valid'] == summary['expected_invocations'],
                f'Missing or incomplete final monitor audit: {run}')
        require(hashlib.sha256((run / 'manifest.json').read_bytes()).hexdigest()
                == config['manifest_sha256'], f'Manifest hash mismatch: {run}')
        rows = [read(p) for p in sorted((run / 'sequences').glob('*/[0-9][0-9].*.json')) if '.interrupted.' not in p.parent.name]
        require(len(rows) == summary['expected_invocations'], 'Invalid cohort evidence')
        expected = {(family, script, mode, rep) for family in config['only'].split(',') for script in scripts[family] for mode in config['modes'] for rep in range(config['repetitions'])}
        require({(r['benchmark'], r['script'], r['mode'], r['repetition']) for r in rows} == expected, 'Invalid cohort evidence')
        for row in rows:
            require(row['valid'] and (not row['failure']) and (not row['remaining_descendants']), 'Invalid cohort evidence')
            require(row['returncode'] == 0, 'Nonzero execution marked valid')
            require(isinstance(row['elapsed_sec'], (int, float))
                    and math.isfinite(row['elapsed_sec']) and row['elapsed_sec'] > 0,
                    'Invalid timing value')
            reference = read(run / 'references' / row['benchmark'] / f"{row['repetition']}.{row['script']}.json")
            require(all((row['validation'][k] == reference[k] for k in ('returncode', 'stdout_sha256', 'normalized_stderr_sha256', 'outputs'))), 'Invalid cohort evidence')
            key = (row['benchmark'], row['script'], run.name, row['repetition'])
            require(row['mode'] not in by_version[key], 'Invalid cohort evidence')
            by_version[key][row['mode']] = row['elapsed_sec']
            by_family[row['benchmark'], run.name, row['repetition']][row['mode']] += row['elapsed_sec']
            require(row['index'] == scripts[row['benchmark']].index(row['script']), 'Invalid cohort evidence')
            if row['index'] > 0:
                by_edited[row['benchmark'], run.name, row['repetition']][row['mode']] += row['elapsed_sec']
        pairs.extend(((run.name, rep) for rep in range(config['repetitions'])))
    require(len(pairs) >= 3, 'At least three paired repetitions required')
    (version_stats, family_stats) = (defaultdict(list), defaultdict(list))
    for ((family, script, run, rep), times) in by_version.items():
        require(set(times) == {'bash', 'original', 'observe'}, 'Invalid cohort evidence')
        version_stats[family, script].append(dict(run=run, repetition=rep, seconds=times))
    for ((family, run, rep), times) in by_family.items():
        family_stats[family].append(dict(run=run, repetition=rep, seconds=dict(times)))

    def summarize(label, samples):
        require(len(samples) == len(pairs), f'Missing paired samples: {label}')
        return dict(label=label, paired_samples=samples, seconds={m: stats([s['seconds'][m] for s in samples]) for m in ('bash', 'original', 'observe')}, paired_speedup={m + '_over_observe': stats([s['seconds'][m] / s['seconds']['observe'] for s in samples]) for m in ('bash', 'original')}, paired_bash_over_original=stats([s['seconds']['bash'] / s['seconds']['original'] for s in samples]))
    version_output = []
    for ((family, script), samples) in sorted(version_stats.items()):
        row = summarize([family, script], samples)
        row['cold'] = scripts[family].index(script) == 0
        version_output.append(row)
    edited_stats = defaultdict(list)
    for ((family, run, rep), times) in by_edited.items():
        edited_stats[family].append(dict(run=run, repetition=rep, seconds=dict(times)))
    output = dict(runs=[str(r) for r in runs], paired_repetitions=len(pairs), scope='One matched implementation/input cohort. Family totals include cold execution; per-version results retain every slowdown.', uncertainty='Report individual paired observations and spread; three repetitions do not justify broad significance claims.', versions=version_output, families=[summarize(k, v) for (k, v) in sorted(family_stats.items())], edited_families=[summarize(k, v) for (k, v) in sorted(edited_stats.items())])
    return output

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runs', nargs='+', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    output = combine(args.runs)
    args.output.write_text(json.dumps(output, indent=2) + '\n')
if __name__ == '__main__':
    main()
