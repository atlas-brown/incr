"""Historical stacked edit chart, extended to Bash / original Incr / Observe."""
import csv
import json
from pathlib import Path
import statistics

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, PathPatch, Rectangle
from matplotlib.path import Path as MplPath
import numpy as np

OUT = Path(__file__).resolve().parent
COLORS = {'add': '#a1e2a1', 'mod': '#ecebb2', 'del': '#ecb5b2',
          'adddel': ('#a1e2a1', '#ecb5b2'),
          'addmod': ('#a1e2a1', '#ecebb2'),
          'delmod': ('#ecb5b2', '#ecebb2')}
MODES = ('bash', 'original', 'observe')


def curve(points):
    t = np.linspace(0, 1, 100)[:, None]
    p0, p1, p2, p3 = np.asarray(points)
    return (1-t)**3*p0 + 3*(1-t)**2*t*p1 + 3*(1-t)*t**2*p2 + t**3*p3


def band(ax, left, right, bot_left, top_left, bot_right, top_right, color):
    mid = (left + right) / 2
    top = curve([(left, top_left), (mid-.10, top_left*1.03),
                 (mid+.10, top_right*1.03), (right, top_right)])
    bottom = curve([(left, bot_left), (mid-.10, bot_left*1.03),
                    (mid+.10, bot_right*1.03), (right, bot_right)])
    points = np.vstack((top, bottom[::-1]))
    ax.add_patch(PathPatch(MplPath(points, [MplPath.MOVETO] +
                                  [MplPath.LINETO]*(len(points)-1)),
                           facecolor=color, edgecolor=color, alpha=.25, lw=.6, zorder=1))
    for line in (top, bottom):
        ax.plot(line[:, 0], line[:, 1], color=color, lw=.7, alpha=.9, zorder=2)


def main():
    classification = json.loads((OUT/'historical-deltas.json').read_text())
    raw = list(csv.DictReader((OUT.parent/'invocations.csv').open()))
    fig, axes = plt.subplots(2, 7, figsize=(18, 6))
    plotted = []
    for ax, benchmark in zip(axes.flat, classification['BENCHMARKS']):
        cohort = 'final-targeted' if benchmark == 'dpt' else 'new-full'
        rows = [r for r in raw if r['benchmark'] == benchmark and r['cohort'] == cohort]
        title = classification['BENCHMARKS_TO_NAMES'][benchmark]
        if not rows:
            ax.set_title(title, fontsize=13)
            ax.text(.5, .5, 'Not evaluated\n(API key required)', ha='center', va='center',
                    transform=ax.transAxes, fontsize=9, color='#666666')
            ax.axis('off')
            continue
        versions = sorted({int(r['index']) for r in rows})
        assert versions == list(range(max(versions)+1))
        assert all(r['valid'] == 'True' for r in rows)
        times = {}
        for mode in MODES:
            times[mode] = []
            for version in versions[1:]:
                samples = [r for r in rows if r['mode'] == mode and int(r['index']) == version]
                assert len(samples) == 3 and {int(r['repetition']) for r in samples} == {0,1,2}
                value = statistics.mean(float(r['elapsed_sec']) for r in samples)
                times[mode].append(value)
                plotted.append(dict(benchmark=benchmark, cohort=cohort, mode=mode,
                                    index=version, script=samples[0]['script'],
                                    repetitions=3, mean_seconds=value))
        bottoms = [0., 0., 0.]
        centers = [.3, 1., 1.7]
        width = .35
        for i, version in enumerate(versions[1:]):
            deltas = classification['DELTAS'].get(benchmark, [])
            color = COLORS.get(deltas[i]['change_type'], '#999999') if i < len(deltas) else '#999999'
            tops = [bottoms[j]+times[m][i] for j,m in enumerate(MODES)]
            for j in (0,1):
                band(ax, centers[j]+width/2, centers[j+1]-width/2,
                     bottoms[j], tops[j], bottoms[j+1], tops[j+1],
                     color[0] if isinstance(color, tuple) else color)
            for j, mode in enumerate(MODES):
                if isinstance(color, tuple):
                    for shift, c in zip((-width/4, width/4), color):
                        ax.bar(centers[j]+shift, times[mode][i], width/2,
                               bottom=bottoms[j], color=c, zorder=3)
                    ax.add_patch(Rectangle((centers[j]-width/2, bottoms[j]), width,
                                           times[mode][i], fill=False, edgecolor='black', lw=.6, zorder=4))
                else:
                    ax.bar(centers[j], times[mode][i], width, bottom=bottoms[j],
                           color=color, edgecolor='black', linewidth=.6, zorder=3)
            bottoms = tops
        ax.set_title(title + (' †' if benchmark == 'dpt' else ''), fontsize=13)
        ax.set_xlim(0, 2)
        ax.set_ylim(0, max(bottoms)*1.04)
        ax.set_xticks(centers, ['Bash', 'Incr', 'Observe'], rotation=40, fontsize=8)
        ax.tick_params(axis='y', labelsize=9)
        ax.spines[['top', 'right']].set_visible(False)
    fig.supylabel('Cumulative re-execution time (s)', fontsize=13)
    fig.legend(handles=[Patch(facecolor=COLORS[k], edgecolor='black', label=label)
                        for k,label in [('add','Addition'),('mod','Modification'),('del','Deletion')]],
               loc='lower center', bbox_to_anchor=(.5,.045), ncols=3, frameon=False)
    fig.text(.03, .012, 'Bars left to right: original Bash / original Incr / Observe Incr. First execution excluded; mean of 3 repetitions; annotations off.\n'
             '† DPT: completed same-binary targeted run; other measured panels: new full reproduction. Each panel has its own seconds axis.', fontsize=9)
    fig.tight_layout(rect=(.015,.13,1,1))
    for ext in ('png','pdf','svg'):
        fig.savefig(OUT/f'reexecution-historical-bars.{ext}', dpi=200)
    plt.close(fig)
    with (OUT/'reexecution-historical-segments.csv').open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(plotted[0]))
        writer.writeheader(); writer.writerows(plotted)


if __name__ == '__main__':
    main()
