"""Read completed family evidence without modifying the frozen measurement harness."""
import csv
import datetime
import json
from pathlib import Path
import statistics
import sys

run = Path(sys.argv[1]).resolve()
study = run.parent.parent
manifest = json.loads((run / 'manifest.json').read_text())
history = {}
for row in csv.DictReader((study / 'reference/historical-timings.csv').open()):
    history.setdefault((row['benchmark'], row['script'], row['mode']), []).append(float(row['elapsed_sec']))
families = []
for bench in manifest['benchmarks']:
    name = bench['name']
    totals = {}
    samples = []
    for mode in ('bash', 'original', 'observe'):
        seq = run / 'sequences' / f'{name}.{mode}.0'
        marker = seq / 'complete.json'
        if not marker.is_file():
            continue
        complete = json.loads(marker.read_text())
        records = [json.loads(p.read_text()) for p in sorted(seq.glob('[0-9][0-9].*.json'))]
        assert complete['valid'] and len(records) == len(bench['scripts'])
        assert all(r['valid'] for r in records)
        totals[mode] = sum(r['elapsed_sec'] for r in records)
        samples.extend(records)
    if len(totals) != 3:
        continue
    comparisons = []
    for r in samples:
        old = history.get((name, r['script'], {'bash': 'bash', 'original': 'incr'}.get(r['mode'])))
        if old:
            factor = r['elapsed_sec'] / statistics.mean(old)
            comparisons.append(dict(mode=r['mode'], script=r['script'], current_sec=r['elapsed_sec'], historical_mean_sec=statistics.mean(old), current_over_historical=factor, needs_review=factor < .5 or factor > 2))
    versions = []
    for index, script in enumerate(bench['scripts']):
        times = {x['mode']: x['elapsed_sec'] for x in samples if x['script'] == script}
        assert set(times) == {'bash', 'original', 'observe'}
        versions.append(dict(script=script, cold=index == 0, seconds=times,
                             original_over_observe=times['original']/times['observe'],
                             bash_over_observe=times['bash']/times['observe'],
                             bash_over_original=times['bash']/times['original']))
    edited = {mode: sum(v['seconds'][mode] for v in versions if not v['cold']) for mode in totals}
    families.append(dict(benchmark=name, sequence_seconds=totals, edited_seconds=edited,
                         versions=versions, original_over_observe=totals['original']/totals['observe'],
                         bash_over_observe=totals['bash']/totals['observe'],
                         bash_over_original=totals['bash']/totals['original'], historical_comparisons=comparisons))
result = dict(reviewed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), scope='First repetition only; incomplete matrix. Historical differences are flags, not explained causal effects.', families=families)
(run / 'live-family-review.json').write_text(json.dumps(result, indent=2)+'\n')
for f in families:
    print(f['benchmark'], {k: round(v, 3) for k, v in f['sequence_seconds'].items()}, 'original/observe', round(f['original_over_observe'], 3), 'bash/observe', round(f['bash_over_observe'], 3), 'historical_flags', sum(x['needs_review'] for x in f['historical_comparisons']))
