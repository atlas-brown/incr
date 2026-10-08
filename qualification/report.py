#!/usr/bin/env python3
"""Aggregate saved measurements; never turn missing or invalid runs into passes."""
import argparse
from collections import Counter, defaultdict
import csv
import json
import math
from pathlib import Path
import statistics

from benchmarks import stderr_key


def geomean(values):
    return math.exp(statistics.mean(math.log(x) for x in values)) if values else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', type=Path)
    args = parser.parse_args()
    records = []
    for directory in ['final-ordinary', 'final-dpt']:
        summary = args.results / directory / 'summary.json'
        if not summary.exists():
            continue
        for record in json.loads(summary.read_text()):
            record['source'] = directory
            records.append(record)
    groups = defaultdict(list)
    for r in records:
        groups[(r['benchmark'], r['script'], r['mode'], r['phase'])].append(r)
    stats = []
    for (family, script, mode, phase), samples in sorted(groups.items()):
        valid = [r['elapsed_sec'] for r in samples if r['valid']]
        expected = 1 if family == 'dpt' else 3
        stats.append(dict(benchmark=family, script=script, mode=mode, phase=phase,
                          samples=len(samples), valid_samples=len(valid), expected_samples=expected,
                          complete=len(samples) == expected and len(valid) == expected,
                          median_sec=statistics.median(valid) if valid else None,
                          min_sec=min(valid) if valid else None, max_sec=max(valid) if valid else None))
    if stats:
        with (args.results / 'aggregate-timings.csv').open('w') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(stats[0]), lineterminator="\n"); writer.writeheader(); writer.writerows(stats)
    lookup = {(r['benchmark'], r['script'], r['mode'], r['phase']): r for r in stats}
    ratios = defaultdict(list)
    paired_times = defaultdict(list)
    for r in stats:
        if r['mode'] != 'observe' or not r['complete']:
            continue
        for mode in ['try', 'main', 'bash']:
            other = lookup.get((r['benchmark'], r['script'], mode, r['phase']))
            if other and other['complete']:
                ratio = other['median_sec'] / r['median_sec']
                for family in ['all', r['benchmark']]:
                    key = (mode, r['phase'], family)
                    ratios[key].append(ratio)
                    paired_times[key].append((other['median_sec'], r['median_sec']))
    comparisons = [dict(reference=mode, phase=phase, benchmark=family, matched_cases=len(values),
                        speedup=geomean(values),
                        reference_sum_sec=sum(v[0] for v in paired_times[(mode, phase, family)]),
                        observe_sum_sec=sum(v[1] for v in paired_times[(mode, phase, family)]),
                        summed_time_speedup=sum(v[0] for v in paired_times[(mode, phase, family)]) /
                                            sum(v[1] for v in paired_times[(mode, phase, family)]))
                   for (mode, phase, family), values in sorted(ratios.items())]
    (args.results / 'aggregate-comparisons.json').write_text(json.dumps(comparisons, indent=2) + '\n')
    policies = sorted({record.get('effect_policy', 'live') for record in records if record['mode'] == 'observe'})
    counts = Counter((r['mode'], r['valid']) for r in records)
    failures = [r for r in records if not r['valid']]
    for r in failures:
        directory = args.results / r['source'] / r['benchmark']
        raw = json.loads((directory / f"{r['script']}.{r['mode']}.{r['repetition']}.{r['phase']}.json").read_text())
        baseline = json.loads((directory / f"{r['script']}.bash.0.cold.json").read_text())
        reasons = []
        if raw['timeout']: reasons.append('timeout')
        if raw['leaked_descendants'] or raw['remaining_descendants']: reasons.append('descendant cleanup required')
        if raw['returncode'] != 0: reasons.append('nonzero status')
        if raw['stdout_sha256'] != baseline['stdout_sha256']: reasons.append('stdout mismatch')
        if stderr_key(raw['stderr'], r['benchmark']) != stderr_key(baseline['stderr'], r['benchmark']): reasons.append('stderr mismatch')
        if raw.get('effects') != baseline.get('effects'): reasons.append('filesystem mismatch')
        if 'validation_error' in raw: reasons.append(raw['validation_error'])
        r['failure_reasons'] = reasons or ['reference/validation error; inspect raw record']
    expected_total = 86 * 4 * 3 * 2 + 10 * 4 * 2
    inventory = json.loads((args.results / 'inventory.json').read_text())
    required = {(r['family'], r['script']) for r in inventory if r['classification'] == 'benchmark'}
    seen = {(r['benchmark'], r['script']) for r in records}
    missing = sorted(required - seen)
    qualified = (len(policies) == 1 and len(records) == expected_total and not missing and len(lookup) == 96 * 4 * 2
                 and all(r['complete'] for r in stats if r['mode'] in ['bash', 'try', 'observe']))
    summary = dict(effect_policies=policies, qualified=qualified, records=len(records), expected_records=expected_total,
                   cases=len(seen), missing_cases=missing, invalid_records=failures,
                   comparisons=comparisons)
    (args.results / 'qualification-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    lines = ['# Minimum-input benchmark measurements', '',
             '**' + ('Complete candidate qualification' if qualified else 'Incomplete qualification') + '**', '',
             f'{len(records)}/{expected_total} scheduled measurements; {len(seen)}/96 benchmark entrypoints.', '',
             'Observe effect policy: ' + ', '.join(policies) + '.', '',
             'Image annotation is excluded at the user’s request. Ordinary cases use three cold/warm pairs; '
             'DPT uses one pair with the real models and one image. DPT timings are single samples. '
             'Weather plotting uses one city-year; web search uses one real page. Other inputs use the supplied minimum.', '',
             '| Mode | Valid measurements | Invalid measurements |', '|---|---:|---:|']
    for mode in ['bash', 'main', 'try', 'observe']:
        lines.append(f'| {mode} | {counts[(mode, True)]} | {counts[(mode, False)]} |')
    lines += ['', 'Speedup is reference time divided by Observe time. Values above 1 favor Observe. '
              'Geometric means use only cases with all scheduled samples valid in both modes; '
              'invalid main runs are excluded, never counted as fast results.', '',
              '| Reference | Phase | Matched cases | Geometric mean speedup | Sum-of-medians speedup |', '|---|---|---:|---:|---:|']
    for r in comparisons:
        if r['benchmark'] == 'all':
            lines.append(f"| {r['reference']} | {r['phase']} | {r['matched_cases']} | {r['speedup']:.3f}× | {r['summed_time_speedup']:.3f}× |")
    lines += ['', 'Raw invocation JSON includes stdout/stderr hashes, return status, timeout and descendant '
              'cleanup evidence, filesystem effects and cache-entry counts. `aggregate-timings.csv` includes '
              'sample counts, medians and ranges. `aggregate-comparisons.json` includes per-family comparisons.', '',
              'The filesystem comparison covers file content, modes, link targets/groups, empty directories '
              'and deletions. It does not claim timestamp/ownership identity. Encrypted/compressed archives '
              'are compared by decoded payload. Diagnostic timestamps and source locations are normalized narrowly. '
              'DPT uses eight OpenMP threads and two TensorFlow threads on this 16-CPU host. '
              'Matplotlib font caches are initialized once during fixture setup and copied identically to each mode. '
              'Cold means an empty Incr cache, not a flushed operating-system page cache. Warm runs restore '
              'the fixture in place while preserving unchanged input inode/ctime. Measurements run serially '
              'on a shared development machine; small timings include wrapper and parser startup overhead.', '',
              '## Invalid measurements', '']
    failed_counts = Counter((r['benchmark'], r['script'], r['mode']) for r in failures)
    lines += [f'- {family}/{script}, {mode}: {count} invalid measurement(s).' for (family, script, mode), count in sorted(failed_counts.items())]
    if not failures: lines.append('None recorded.')
    if missing: lines += ['', 'Missing cases: ' + ', '.join('/'.join(v) for v in missing)]
    (args.results / 'MEASUREMENTS.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({k: summary[k] for k in ['qualified', 'records', 'expected_records', 'cases', 'missing_cases']}, indent=2))


if __name__ == '__main__':
    main()
