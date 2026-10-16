"""Validate completed cohorts and derive final tables without running benchmarks."""
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
import tarfile

OUT = Path(__file__).resolve().parent
STUDIES = OUT.parent
APPLICATION = STUDIES/'evaluation-checkpoint-2026-10-16'
IMAGE = STUDIES/'image-annotation-api-2026-10-16'
MICRO = STUDIES/'observe-strengths-microbench/measurements/final-01'
MODES = ('bash', 'original', 'observe')


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')


def write_csv(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader();writer.writerows(rows)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    run = IMAGE/'measurements/paper-02'
    image_catalog = json.loads((IMAGE/'measurements/catalog.json').read_text())
    image_archive = IMAGE/'measurements/detailed-evidence.tar.gz'
    assert sha(image_archive) == image_catalog['archive_sha256']
    with tarfile.open(image_archive) as source:
        verified_image = {}
        for member in source:
            assert member.isfile() and member.name not in verified_image
            verified_image[member.name] = hashlib.sha256(source.extractfile(member).read()).hexdigest()
    assert verified_image == image_catalog['members']
    assert json.loads((run/'status.json').read_text())['state'] == 'complete'
    configuration = json.loads((run/'configuration.json').read_text())
    assert configuration['repetitions'] == 3 and not configuration['annotations']
    manifest = json.loads((run/'manifest.json').read_text())
    scripts = manifest['benchmarks'][0]['scripts']
    rows = [json.loads(line) for line in (run/'samples.jsonl').read_text().splitlines()]
    expected = {(mode, rep, i) for mode in MODES for rep in range(3) for i in range(7)}
    assert len(rows) == 63 and {(r['mode'], r['repetition'], r['index']) for r in rows} == expected
    inputs = json.loads((run/'inputs/image-annotation.json').read_text())
    payloads = {p['sha256'] for p in inputs['files']}
    references = {(r['repetition'],r['index']):r for r in rows if r['mode']=='bash'}
    for row in rows:
        assert row['valid'] and row['returncode']==0 and not row['failure']
        assert not row['remaining_descendants'] and math.isfinite(row['elapsed_sec']) and row['elapsed_sec']>0
        assert row['script']==scripts[row['index']]
        validation = row['validation']
        assert not validation['problems'] and set(validation['comparison_outputs'])==payloads
        assert {v['content'] for v in validation['outputs'].values() if v['kind']=='file'} == payloads
        reference = references[row['repetition'],row['index']]['validation']
        for key in ('returncode','stdout_sha256','normalized_stderr_sha256','comparison_policy','comparison_outputs'):
            assert reference[key]==validation[key], (row['mode'],key)
    image = dict(cohort='image-api-final', benchmark='image-annotation', expected_versions=7, modes={})
    for mode in MODES:
        samples = []
        for rep in range(3):
            subset = [r for r in rows if r['mode']==mode and r['repetition']==rep]
            samples.append(dict(repetition=rep,seconds=sum(r['elapsed_sec'] for r in subset),
                                edited_seconds=sum(r['elapsed_sec'] for r in subset if r['index']>0)))
        image['modes'][mode] = dict(complete_repetitions=3,samples=samples,
            median_seconds=statistics.median(s['seconds'] for s in samples),
            median_edited_seconds=statistics.median(s['edited_seconds'] for s in samples))
    write_json(APPLICATION/'image-family-statistics.json',[image])
    image_rows = []
    resources = []
    for row in rows:
        image_rows.append(dict(benchmark=row['benchmark'],mode=row['mode'],repetition=row['repetition'],
            script=row['script'],index=row['index'],elapsed_sec=row['elapsed_sec'],valid=row['valid'],
            returncode=row['returncode'],cohort='image-api-final'))
        resources.append(dict(image_rows[-1], **{k:row.get(k) for k in
            ('peak_cache_bytes','peak_work_bytes','cache_bytes','cache_entries_before','cache_entries_after')},
            **row['resources']))
    write_csv(APPLICATION/'image-invocations.csv',image_rows)
    write_csv(OUT/'image-resources.csv',resources)
    old = json.loads((APPLICATION/'family-statistics.json').read_text())
    selected = [r for r in old if (r['cohort']=='new-full' and r['benchmark']!='dpt') or
                (r['cohort']=='final-targeted' and r['benchmark']=='dpt')] + [image]
    assert len(selected)==14
    write_json(OUT/'application-statistics.json',selected)
    chosen = {(r['cohort'],r['benchmark']) for r in selected}
    with (APPLICATION/'invocations.csv').open() as stream:
        application_invocations = [r for r in csv.DictReader(stream) if (r['cohort'],r['benchmark']) in chosen]
    application_invocations += [dict(row, resources_json=json.dumps(resource)) for row,resource in zip(image_rows,resources)]
    assert len(application_invocations) == sum(r['expected_versions'] * 9 for r in selected)
    assert all(str(r['valid']) == 'True' for r in application_invocations)
    write_csv(OUT/'application-invocations.csv',application_invocations)
    application_rows = []
    for case in selected:
        for mode in MODES:
            record=case['modes'][mode]
            assert record['complete_repetitions']==3
            application_rows.append(dict(benchmark=case['benchmark'],cohort=case['cohort'],mode=mode,
                repetitions=3,median_total_seconds=record['median_seconds'],
                median_reexecution_seconds=record['median_edited_seconds']))
    write_csv(OUT/'application-results.csv',application_rows)
    # Verify every raw microbenchmark member against its retained SHA catalog.
    catalog=json.loads((MICRO/'raw-catalog.json').read_text())
    assert sha(MICRO/'raw-evidence.tar.gz')==catalog['archive_sha256']
    seen={};micro=[]
    with tarfile.open(MICRO/'raw-evidence.tar.gz') as archive:
        for member in archive:
            assert member.isfile() and member.name not in seen
            data=archive.extractfile(member).read()
            seen[member.name]=hashlib.sha256(data).hexdigest()
            if member.name.startswith('samples/') and len(Path(member.name).parts)==6 and member.name.endswith('.json'):
                micro.append(json.loads(data))
    assert seen==catalog['members']
    assert len(micro)==2754 and all(r['valid'] for r in micro)
    comparisons=json.loads((MICRO/'summary.json').read_text())['comparisons']
    micro_rows=[]
    for case in comparisons:
        for mode in MODES:
            record=case['modes'][mode]
            assert record['complete_repetitions']==3
            micro_rows.append(dict(scenario=case['scenario'],scale=case['scale'],mode=mode,repetitions=3,
                median_total_seconds=record['total_sec'],median_cold_seconds=record['cold_sec'],
                median_unchanged_seconds=record['unchanged_sec'],median_edited_seconds=record['edited_sec']))
    assert len(micro_rows)==153
    write_csv(OUT/'microbenchmark-results.csv',micro_rows)
    counters=('user_sec','system_sec','max_process_rss_kib','fs_input_blocks','fs_output_blocks',
              'voluntary_context_switches','involuntary_context_switches')
    resource_rows=[]
    for row in micro:
        values=row['resource_raw'].splitlines()[-1].split()
        assert len(values)==len(counters)
        resource_rows.append(dict({k:row[k] for k in ('scenario','scale','repetition','mode','phase',
            'elapsed_sec','cache_bytes','cache_entries','peak_cache_bytes','peak_work_bytes')},
            **dict(zip(counters,map(float,values)))))
    write_csv(OUT/'microbenchmark-resources.csv',resource_rows)
    binaries=json.loads((MICRO/'provenance.json').read_text())['binaries']
    image_binaries=json.loads((run/'frozen-build.json').read_text())['sha256']
    for mode,relative in [('candidate','candidate/target/release/incr'),('original','original/target/release/incr'),
                          ('observe','observe/target/release/observe')]:
        assert binaries[mode]['sha256']==image_binaries[relative]
    write_json(OUT/'verification.json',dict(image_invocations=63,image_valid=63,
        micro_invocations=2754,micro_valid=2754,micro_archive_members_verified=len(seen),
        application_families=14,application_invocations=len(application_invocations),micro_scenario_scale_comparisons=51,
        binary_hashes={k:v['sha256'] for k,v in binaries.items()},
        qualification='Image title text is nondeterministic; image validation preserves payloads. Micro zero-cache artifact samples have a separately reproduced extended-attribute replay barrier; original audit is retained.',
        source_hashes={str(p.relative_to(STUDIES)):sha(p) for p in
            [APPLICATION/'family-statistics.json',APPLICATION/'image-family-statistics.json',
             MICRO/'summary.json',MICRO/'raw-catalog.json',run/'summary.json']}))
    lines=['# Final application and synthetic measurements','',
        'All measurement jobs are complete. Application medians use three repetitions per mode; re-execution excludes the first execution within each repetition. Annotations are off. Cohorts remain explicit: twelve new-full families, completed same-binary targeted DPT, and the separately labelled live image API study. Do not pool them or the earlier historical checkpoints.','',
        '| Benchmark | Cohort | Bash total / re-execution (s) | Original total / re-execution (s) | Observe total / re-execution (s) |',
        '|---|---|---:|---:|---:|']
    for case in selected:
        cells=[f"{case['modes'][m]['median_seconds']:.3f} / {case['modes'][m]['median_edited_seconds']:.3f}" for m in MODES]
        lines.append('| '+case['benchmark']+' | '+case['cohort']+' | '+' | '.join(cells)+' |')
    lines += ['', '## Synthetic workloads','',
        'All 17 scenarios × three scales × three repetitions × three modes × six phases completed: **2,754 output-validated timings**. [Full 51-comparison table](../observe-strengths-microbench/measurements/final-01/REPORT.md) and verified raw evidence remain in their original study. `microbenchmark-results.csv` contains all mode medians; `microbenchmark-resources.csv` contains all 2,754 named resource records. These synthetic strengths and controls are not representative application claims. Observe does not win every case or phase; all results are retained.', '',
        '## Evidence and limits','',
        '- [Canonical application evidence](../evaluation-checkpoint-2026-10-16/README.md) retains all historical and current cohorts and figures.',
        '- [Live image study](../image-annotation-api-2026-10-16/README.md) completed 63/63 with image-payload validation. Generated titles/filenames may differ, and latency depends on the remote service. A shared filename-prefix repair prevents title collisions. These are not strict deterministic-output results.',
        '- [Micro instrumentation diagnosis](../observe-strengths-microbench/measurements/final-01/instrumentation-review.json) explains zero retained cache metadata for artifact installation: extended attributes prevent replay. The original failed cache-presence audit is preserved; all native-output/capture/coverage checks passed. No runtime shortcut was added.',
        '- `application-invocations.csv` collects all selected completed application samples with their original resource records. `application-statistics.json` retains each of the three per-mode repetition totals; CSVs are derived projections. `verification.json` records source and runtime hashes. Three repetitions provide descriptive comparisons, not significance claims.',
        '- GNU time RSS is maximum single-process RSS, not aggregate concurrent memory; filesystem counters are blocks; cache/work peaks are sampled allocations.', '',
        'Regenerate these tables with `python3 studies/final-results-2026-10-16/collect.py` from the Incr root. Collection reads saved evidence and never executes benchmarks.']
    (OUT/'README.md').write_text('\n'.join(lines)+'\n')
    print('Verified image 63/63; micro 2754/2754;',len(seen),'archive members. Exported 14 application and 51 micro comparisons.')


if __name__=='__main__':
    main()
