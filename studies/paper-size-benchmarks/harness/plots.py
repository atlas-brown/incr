"""Standalone figures from saved, validated evidence; never runs benchmarks."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    args = parser.parse_args()
    data = json.loads((args.run / 'summary.json').read_text())
    config = json.loads((args.run / 'configuration.json').read_text())
    families = data['family_totals']
    modes = config['modes']
    names = [f['benchmark'] for f in families]
    output = args.run / 'figures'
    output.mkdir(exist_ok=True)
    x = np.arange(len(names))
    width = .8 / len(modes)
    fig, ax = plt.subplots(figsize=(max(9, len(names) * .7), 5))
    for index, mode in enumerate(modes):
        values = [f['complete_mode_totals_sec'].get(mode, np.nan) for f in families]
        ax.bar(x - .4 + width / 2 + index * width, values, width, label=mode)
    ax.set_xticks(x, names, rotation=40, ha='right')
    ax.set_ylabel('Mean total development-sequence time (seconds)')
    ax.set_title(f'{config["profile"]}: {"complete" if data["complete"] else "incomplete; missing bars omitted"}')
    ax.legend()
    fig.tight_layout()
    for extension in ('png', 'pdf'):
        fig.savefig(output / f'sequence-times.{extension}', dpi=180)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(max(9, len(names) * .7), 5))
    for index, mode in enumerate(modes):
        if mode == 'bash':
            continue
        values = [f['peak_cache_bytes'].get(mode, np.nan) / 1024**3 for f in families]
        ax.bar(x - .4 + width / 2 + index * width, values, width, label=mode)
    ax.set_xticks(x, names, rotation=40, ha='right')
    ax.set_ylabel('Sampled peak cache allocation (GiB)')
    ax.set_title('Cache allocation; invalid/incomplete samples remain in raw evidence')
    ax.legend()
    fig.tight_layout()
    for extension in ('png', 'pdf'):
        fig.savefig(output / f'cache-space.{extension}', dpi=180)
    plt.close(fig)
    print(output)


if __name__ == '__main__':
    main()
