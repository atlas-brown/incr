#!/usr/bin/env python3
"""
Compare incr (try+strace) vs incr-observe from run_all.sh results.

The new format has a single CSV per benchmark under:
  <results-dir>/<size>/<benchmark>-time.csv

Each CSV has columns: mode, script, time_sec
Modes: bash, incr, incr-observe

Usage:
  cd incr/evaluation/analysis
  python3 compare_default_observe.py --results-dir run_results/min
  python3 compare_default_observe.py --results-dir run_results/small --skip-dpt
  python3 compare_default_observe.py --results-dir observe_results/observe_1/small \\
      --output-dir observe_results/observe_1/plots

Paths for --results-dir and --output-dir are relative to incr/evaluation/ unless absolute.
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
    parser = argparse.ArgumentParser(
        description="Compare incr vs incr-observe timing results from run_all.sh"
    )
    parser.add_argument(
        "--output-dir", default="analysis/plots",
        help="Output directory for plots, relative to evaluation/ if not absolute "
             "(default: analysis/plots/)"
    )
    parser.add_argument(
        "--results-dir", default=None,
        help="Path to results dir containing <benchmark>-time.csv files. "
             "Default: auto-detects ../run_results/min or ../run_results/small."
    )
    parser.add_argument(
        "--skip-dpt", action="store_true",
        help="Exclude dpt from plot (long benchmark)"
    )
    parser.add_argument(
        "--size", default=None,
        help="Size subdir to look in (min or small). Used when --results-dir is not given."
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    eval_dir = script_dir.parent

    if args.results_dir:
        results_dir = Path(args.results_dir)
        if not results_dir.is_absolute():
            results_dir = eval_dir / results_dir
    else:
        # Auto-detect: prefer min, then small
        sizes = [args.size] if args.size else ["min", "small"]
        results_dir = None
        for sz in sizes:
            cand = eval_dir / "run_results" / sz
            if cand.exists() and any(cand.glob("*-time.csv")):
                results_dir = cand
                break
        if results_dir is None:
            results_dir = eval_dir / "run_results" / "min"

    out_dir = Path(args.output_dir)
    if not out_dir.is_absolute():
        out_dir = eval_dir / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if not results_dir.exists():
        print(f"Results directory not found: {results_dir}")
        print("Run: bash evaluation/benchmarks/run_all.sh --run-mode all --size min")
        return 1

    csvs = sorted(results_dir.glob("*-time.csv"))
    if not csvs:
        print(f"No *-time.csv files found in {results_dir}")
        return 1

    benchmarks = [f.stem.replace("-time", "") for f in csvs]
    if args.skip_dpt:
        benchmarks = [b for b in benchmarks if b != "dpt"]
        csvs = [results_dir / f"{b}-time.csv" for b in benchmarks]
        print("Excluding dpt (--skip-dpt)")

    if pd is None:
        print("pandas required. pip install pandas matplotlib")
        return 1

    incr_totals = {}
    observe_totals = {}
    bash_totals = {}

    for b, csv_path in zip(benchmarks, csvs):
        df = pd.read_csv(csv_path)
        for mode, store in [("incr", incr_totals), ("incr-observe", observe_totals), ("bash", bash_totals)]:
            rows = df[df["mode"] == mode]
            store[b] = rows["time_sec"].sum() if len(rows) > 0 else None

    # Summary table
    print(f"\nResults from: {results_dir}")
    print(f"{'Benchmark':<20} {'bash':>8} {'incr':>8} {'incr-obs':>10} {'incr/obs ratio':>14}")
    print("-" * 66)
    for b in benchmarks:
        d = incr_totals.get(b)
        o = observe_totals.get(b)
        ba = bash_totals.get(b)
        ratio_str = f"{d/o:>6.2f}x" if d and o else "     n/a"
        d_str = f"{d:>8.3f}" if d is not None else "     n/a"
        o_str = f"{o:>10.3f}" if o is not None else "       n/a"
        ba_str = f"{ba:>8.3f}" if ba is not None else "     n/a"
        print(f"{b:<20} {ba_str} {d_str} {o_str} {ratio_str}")

    d_total = sum(v for v in incr_totals.values() if v is not None)
    o_total = sum(v for v in observe_totals.values() if v is not None)
    print("-" * 66)
    print(f"{'TOTAL':<20} {'':>8} {d_total:>8.3f} {o_total:>10.3f} {d_total/o_total if o_total else 0:>13.2f}x")

    # Bar chart
    if HAS_PLOT:
        x = range(len(benchmarks))
        w = 0.3

        incr_vals = [incr_totals.get(b) or 0 for b in benchmarks]
        obs_vals = [observe_totals.get(b) or 0 for b in benchmarks]
        bash_vals = [bash_totals.get(b) or 0 for b in benchmarks]

        has_bash = any(v > 0 for v in bash_vals)

        fig, ax = plt.subplots(figsize=(14, 6))
        if has_bash:
            offset = [-w, 0, w]
            ax.bar([i + offset[0] for i in x], bash_vals, w, label="bash (baseline)", color="#3498db", alpha=0.85)
            ax.bar([i + offset[1] for i in x], incr_vals, w, label="incr (try+strace)", color="#e74c3c", alpha=0.9)
            ax.bar([i + offset[2] for i in x], obs_vals, w, label="incr-observe", color="#27ae60", alpha=0.9)
        else:
            ax.bar([i - w/2 for i in x], incr_vals, w, label="incr (try+strace)", color="#e74c3c", alpha=0.9)
            ax.bar([i + w/2 for i in x], obs_vals, w, label="incr-observe", color="#27ae60", alpha=0.9)

        ax.set_xticks(list(x))
        ax.set_xticklabels(benchmarks, rotation=45, ha="right")
        ax.set_ylabel("Total time (s)")
        ax.set_title("incr: try+strace vs observe")
        ax.legend()
        ax.set_ylim(bottom=0)
        fig.tight_layout()

        for ext in ["pdf", "png"]:
            out_path = out_dir / f"default_vs_observe.{ext}"
            fig.savefig(out_path, bbox_inches="tight", dpi=150, format=ext)
            print(f"Saved {out_path}")
        plt.close()
    else:
        print("(Skipping plot — install matplotlib + pandas for plots)")

    return 0


if __name__ == "__main__":
    exit(main())
