#!/usr/bin/env python3
"""
Compare incr default (try+strace) vs observe mode from run_results.
Usage: python compare_default_observe.py [--output-dir DIR]
Reads from ../run_results/default/ and ../run_results/observe/
"""
import argparse
import os
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd
    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False
    pd = None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="plots", help="Output directory for plots")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    results_dir = script_dir.parent / "run_results"
    default_dir = results_dir / "default"
    observe_dir = results_dir / "observe"
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not default_dir.exists() or not observe_dir.exists():
        print(f"Need both {default_dir} and {observe_dir}")
        return 1

    benchmarks = sorted([f.stem.replace("-time", "") for f in default_dir.glob("*-time.csv")])
    if not benchmarks:
        print("No benchmark results found")
        return 1

    if pd is None:
        print("pandas required for comparison. pip install pandas")
        return 1

    # Collect totals per benchmark
    default_totals = {}
    observe_totals = {}
    for b in benchmarks:
        df_d = pd.read_csv(default_dir / f"{b}-time.csv")
        df_o = pd.read_csv(observe_dir / f"{b}-time.csv")
        default_totals[b] = df_d["time_sec"].sum()
        observe_totals[b] = df_o["time_sec"].sum()

    # Bar chart: default vs observe total time per benchmark (if matplotlib available)
    x = range(len(benchmarks))
    w = 0.35
    default_vals = [default_totals.get(b, 0) for b in benchmarks]
    observe_vals = [observe_totals.get(b, 0) for b in benchmarks]
    if HAS_PLOT:
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.bar([i - w/2 for i in x], default_vals, w, label="default (try+strace)", color="#e74c3c", alpha=0.9)
        ax.bar([i + w/2 for i in x], observe_vals, w, label="observe", color="#27ae60", alpha=0.9)
        ax.set_xticks(x)
        ax.set_xticklabels(benchmarks, rotation=45, ha="right")
        ax.set_ylabel("Total time (s)")
        ax.set_title("incr: default (try+strace) vs observe")
        ax.legend()
        ax.set_ylim(bottom=0)
        fig.tight_layout()
        for ext in ["pdf", "png"]:
            out_path = out_dir / f"default_vs_observe.{ext}"
            fig.savefig(out_path, bbox_inches="tight", dpi=150)
            print(f"Saved {out_path}")
        plt.close()
    else:
        print("(Skipping plot - matplotlib not installed)")

    # Summary table
    print("\nSummary (total sec per benchmark):")
    print(f"{'Benchmark':<20} {'default':>10} {'observe':>10} {'ratio':>8}")
    print("-" * 52)
    for b in benchmarks:
        d, o = default_totals[b], observe_totals[b]
        ratio = d / o if o > 0 else 0
        print(f"{b:<20} {d:>10.3f} {o:>10.3f} {ratio:>7.2f}x")
    d_total = sum(default_totals.values())
    o_total = sum(observe_totals.values())
    print("-" * 52)
    print(f"{'TOTAL':<20} {d_total:>10.3f} {o_total:>10.3f} {d_total/o_total if o_total else 0:>7.2f}x")

    return 0


if __name__ == "__main__":
    exit(main())
