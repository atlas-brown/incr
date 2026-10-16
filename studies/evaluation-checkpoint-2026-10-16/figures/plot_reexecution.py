"""Plot saved three-repetition re-execution totals; never executes benchmarks."""
import csv
import hashlib
import json
from pathlib import Path
import statistics

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
MODES = ('bash', 'original', 'observe')
LABELS = ('Original Bash', 'Original Incr', 'Observe Incr')
COLORS = ('#9099A2', '#D68A32', '#227C9D')


def main():
    source = ROOT / 'family-statistics.json'
    records = json.loads(source.read_text())
    image_source = ROOT / 'image-family-statistics.json'
    records += json.loads(image_source.read_text())
    selected = [r for r in records if
                (r['cohort'] == 'new-full' and r['benchmark'] != 'dpt') or
                (r['cohort'] == 'final-targeted' and r['benchmark'] == 'dpt') or
                r['cohort'] == 'image-api-final']
    assert len(selected) == 14
    rows = []
    for record in selected:
        times = {}
        for mode in MODES:
            data = record['modes'][mode]
            assert data['complete_repetitions'] == 3
            samples = data['samples']
            assert {s['repetition'] for s in samples} == {0, 1, 2}
            value = statistics.median(s['edited_seconds'] for s in samples)
            assert value > 0 and value == data['median_edited_seconds']
            times[mode] = value
        for mode in MODES:
            rows.append(dict(benchmark=record['benchmark'], cohort=record['cohort'],
                             mode=mode, repetitions=3, median_reexecution_seconds=times[mode],
                             speedup_over_bash=times['bash'] / times[mode]))
    with (OUT / 'reexecution-data.csv').open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    plt.rcParams.update({'font.size': 10, 'svg.fonttype': 'none', 'pdf.fonttype': 42})
    names = [r['benchmark'] + (' †' if r['benchmark'] == 'dpt' else ' ‡' if r['benchmark'] == 'image-annotation' else '') for r in selected]
    y = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(10, 8))
    for i, (mode, label, color) in enumerate(zip(MODES, LABELS, COLORS)):
        values = [r['speedup_over_bash'] for r in rows if r['mode'] == mode]
        position = y + (i - 1) * .24
        ax.barh(position, values, height=.21, color=color, label=label, zorder=3)
        if mode != 'bash':
            for pos, value in zip(position, values):
                ax.text(value * 1.045, pos, f'{value:.2f}×', va='center', fontsize=8)
    ax.set_xscale('log', base=2)
    ax.set_xlim(.25, 32)
    ticks = [.25, .5, 1, 2, 4, 8, 16, 32]
    ax.set_xticks(ticks, [f'{t:g}×' for t in ticks])
    ax.axvline(1, color='#333333', linewidth=1, linestyle='--', zorder=4)
    ax.set_yticks(y, names)
    ax.invert_yaxis()
    ax.set_xlabel('Re-execution speedup over Bash (log scale; higher is faster)')
    ax.set_title('Application benchmarks: re-execution speedup', loc='left', fontweight='bold')
    ax.grid(axis='x', alpha=.2, zorder=0)
    ax.legend(loc='lower right', frameon=False)
    ax.spines[['top', 'right']].set_visible(False)
    fig.text(.02, .015, 'First execution excluded per repetition; ratio of median sequence totals, n = 3. Annotations off.\n'
             '† DPT: same-binary targeted run. ‡ Image: live API, image-payload validation. Others: new full run; no pooling.', fontsize=9)
    fig.tight_layout(rect=(0, .06, 1, 1))
    save(fig, 'reexecution-speedup')
    # Absolute-time small multiples follow the historical perf-bars presentation,
    # with an independent linear seconds axis for each benchmark and all three modes.
    fig, axes = plt.subplots(2, 7, figsize=(17, 6))
    for ax, record, name in zip(axes.flat, selected, names):
        values = [next(r['median_reexecution_seconds'] for r in rows
                       if r['benchmark'] == record['benchmark'] and r['mode'] == mode) for mode in MODES]
        ax.bar(range(3), values, color=COLORS, width=.7)
        for i, value in enumerate(values):
            ax.text(i, value, f'{value:.1f}', ha='center', va='bottom', fontsize=8)
        ax.set_title(name, fontsize=10)
        ax.set_ylim(0, max(values) * 1.22)
        ax.set_xticks(range(3), ['Bash', 'Incr', 'Observe'], rotation=35, fontsize=8)
        ax.spines[['top', 'right']].set_visible(False)
    for unused in list(axes.flat)[len(selected):]:
        unused.axis('off')
    fig.suptitle('Median cumulative re-execution time (seconds; first execution excluded)', fontsize=13)
    fig.text(.02, .01, 'Three repetitions per mode; annotations off. Each panel has its own linear seconds axis.\n'
             '† DPT: same-binary targeted run. ‡ Image: live API, image-payload validation. Others: new full run.', fontsize=9)
    fig.tight_layout(rect=(0, .07, 1, .96))
    save(fig, 'reexecution-times')
    (OUT / 'provenance.json').write_text(json.dumps({
        'source': '../family-statistics.json',
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'image_source_sha256': hashlib.sha256(image_source.read_bytes()).hexdigest(),
        'historical_reference': '15d749a:evaluation/scripts/perf-bars-color.py (drop first execution)',
        'aggregation': 'Per repetition sum excluding first execution; median of three sums per mode; Bash median divided by mode median.',
        'uncertainty': 'Descriptive medians; no confidence intervals or significance claims.',
        'matplotlib_version': matplotlib.__version__,
        'outputs': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in OUT.iterdir() if p.name == 'reexecution-data.csv' or (p.stem in ('reexecution-speedup', 'reexecution-times') and p.suffix in ('.png', '.pdf', '.svg'))},
    }, indent=2) + '\n')


def save(fig, name):
    for extension in ('png', 'pdf', 'svg'):
        target = OUT / f'{name}.{extension}'
        fig.savefig(target, dpi=180)
        if extension == 'svg':
            target.write_text('\n'.join(line.rstrip() for line in target.read_text().splitlines())+'\n')
    plt.close(fig)


if __name__ == '__main__':
    main()
