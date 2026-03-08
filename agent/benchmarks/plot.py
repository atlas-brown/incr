#!/usr/bin/env python3
"""
Plot incr strace vs observe benchmark results.
Parses BENCH:name:tracer:value lines from results.
Usage: python plot.py [results.txt]
"""

import re
import subprocess
import sys
from pathlib import Path
from collections import defaultdict

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use("Agg")
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def parse_results(text: str) -> dict:
    """Parse BENCH:name:tracer:value lines."""
    data = defaultdict(dict)
    for line in text.splitlines():
        m = re.match(r"BENCH:([^:]+):(strace|observe):([\d.]+)", line)
        if m:
            name, tracer, val = m.group(1), m.group(2), float(m.group(3))
            data[name][tracer] = val
    return dict(data)


def plot_results(data: dict, output_path: Path) -> None:
    """Create bar chart of all benchmark results."""
    if not HAS_MATPLOTLIB:
        print("matplotlib not installed. Run: pip install matplotlib")
        sys.exit(1)

    # Order: cold before warm, logical grouping
    order = [
        "cat_cold", "cat_warm", "cat_large_cold", "cat_large_warm",
        "sed_cold", "sed_warm", "write_cold", "write_warm",
        "cp_cold", "cp_warm", "grep_cold",
        "batch_write_cold", "batch_write_warm",
    ]
    names = [n for n in order if n in data]
    for k in sorted(data.keys()):
        if k not in names:
            names.append(k)

    labels = [n.replace("_", "\n") for n in names]
    strace_vals = [data.get(n, {}).get("strace", 0) * 1000 for n in names]
    observe_vals = [data.get(n, {}).get("observe", 0) * 1000 for n in names]

    x = range(len(names))
    width = 0.35

    fig, ax = plt.subplots(figsize=(14, 6))
    bars1 = ax.bar([i - width/2 for i in x], strace_vals, width, label="strace", color="#e74c3c", alpha=0.9)
    bars2 = ax.bar([i + width/2 for i in x], observe_vals, width, label="observe", color="#27ae60", alpha=0.9)

    ax.set_ylabel("Time (ms)")
    ax.set_title("incr: strace vs observe (preliminary benchmarks)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8, rotation=30, ha="right")
    ax.legend()
    ax.set_ylim(bottom=0)

    for bar in bars1:
        h = bar.get_height()
        if h > 0:
            ax.annotate(f"{h:.1f}", xy=(bar.get_x() + bar.get_width()/2, h),
                        xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontsize=6)
    for bar in bars2:
        h = bar.get_height()
        if h > 0:
            ax.annotate(f"{h:.1f}", xy=(bar.get_x() + bar.get_width()/2, h),
                        xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontsize=6)

    fig.tight_layout()
    fig.savefig(output_path, dpi=120)
    print(f"Plot saved to {output_path}")


def main():
    script_dir = Path(__file__).resolve().parent
    results_file = Path(sys.argv[1]) if len(sys.argv) > 1 else script_dir / "results.txt"

    if not results_file.exists():
        print(f"Results not found: {results_file}")
        print("Run: bash agent/benchmarks/run.sh")
        sys.exit(1)

    text = results_file.read_text()
    data = parse_results(text)
    if not data:
        print("No BENCH: lines found in", results_file)
        sys.exit(1)

    plot_path = script_dir / "benchmark_plot.png"
    plot_results(data, plot_path)


if __name__ == "__main__":
    main()
