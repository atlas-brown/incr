#!/usr/bin/env python3
"""
Cold-start overhead: first script per benchmark with empty incr cache.

run_lib.sh clears the cache before the incr block and again before incr-observe,
so the first script in run order is the cold start for that mode. We pair times
by script name against bash on the same script.

Plots slowdown vs bash: incr/bash and incr-observe/bash (1.0 = same as bash).

Usage:
  cd incr/evaluation/analysis
  python3 cold_start_overhead.py --results-dir observe_results/observe_1/small \\
      --output-dir observe_results/observe_1/plots
"""
import argparse
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
        description="Plot cold-start slowdown (first script) vs bash per benchmark"
    )
    parser.add_argument(
        "--output-dir", default="analysis/plots",
        help="Output directory (default: analysis/plots/, relative to evaluation/)",
    )
    parser.add_argument(
        "--results-dir", default=None,
        help="Directory with <benchmark>-time.csv (default: run_results/small or min)",
    )
    parser.add_argument(
        "--skip-dpt", action="store_true",
        help="Exclude dpt from the plot",
    )
    parser.add_argument(
        "--size", default=None,
        help="min or small when auto-detecting results dir",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    eval_dir = script_dir.parent

    if args.results_dir:
        results_dir = Path(args.results_dir)
        if not results_dir.is_absolute():
            results_dir = eval_dir / results_dir
    else:
        sizes = [args.size] if args.size else ["small", "min"]
        results_dir = None
        for sz in sizes:
            cand = eval_dir / "run_results" / sz
            if cand.exists() and any(cand.glob("*-time.csv")):
                results_dir = cand
                break
        if results_dir is None:
            results_dir = eval_dir / "run_results" / "small"

    out_dir = Path(args.output_dir)
    if not out_dir.is_absolute():
        out_dir = eval_dir / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if not results_dir.exists():
        print(f"Results directory not found: {results_dir}")
        return 1

    csvs = sorted(results_dir.glob("*-time.csv"))
    if not csvs:
        print(f"No *-time.csv in {results_dir}")
        return 1

    benchmarks = [f.stem.replace("-time", "") for f in csvs]
    if args.skip_dpt:
        benchmarks = [b for b in benchmarks if b != "dpt"]
        csvs = [results_dir / f"{b}-time.csv" for b in benchmarks]

    if pd is None:
        print("pandas required. pip install pandas matplotlib")
        return 1

    rows = []
    for b, path in zip(benchmarks, csvs):
        df = pd.read_csv(path)
        bash = df[df["mode"] == "bash"]
        if bash.empty:
            continue
        script = bash.iloc[0]["script"]
        t_b = float(bash.iloc[0]["time_sec"])
        if t_b <= 0:
            continue
        r_incr = df[(df["mode"] == "incr") & (df["script"] == script)]
        r_obs = df[(df["mode"] == "incr-observe") & (df["script"] == script)]
        if r_incr.empty or r_obs.empty:
            continue
        t_i = float(r_incr.iloc[0]["time_sec"])
        t_o = float(r_obs.iloc[0]["time_sec"])
        rows.append(
            {
                "benchmark": b,
                "script": script,
                "bash": t_b,
                "incr": t_i,
                "incr_observe": t_o,
                "slowdown_incr": t_i / t_b,
                "slowdown_observe": t_o / t_b,
            }
        )

    if not rows:
        print("No benchmark rows (need bash, incr, incr-observe for first script).")
        return 1

    table = pd.DataFrame(rows)
    print(f"\nCold start (first script) vs bash — from {results_dir}")
    print(f"{'Benchmark':<18} {'script':<22} {'bash':>8} {'incr':>8} {'obs':>8} "
          f"{'incr/bash':>10} {'obs/bash':>10}")
    print("-" * 96)
    for _, r in table.iterrows():
        print(
            f"{r['benchmark']:<18} {str(r['script']):<22} {r['bash']:>8.3f} "
            f"{r['incr']:>8.3f} {r['incr_observe']:>8.3f} "
            f"{r['slowdown_incr']:>10.2f}x {r['slowdown_observe']:>10.2f}x"
        )

    if not HAS_PLOT:
        print("(Skipping plot — install matplotlib)")
        return 0

    x = range(len(table))
    w = 0.36
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.axhline(1.0, color="#555", linestyle="--", linewidth=1, alpha=0.8, label="bash baseline")
    ax.bar([i - w / 2 for i in x], table["slowdown_incr"], w, label="incr (cold)", color="#e74c3c", alpha=0.9)
    ax.bar([i + w / 2 for i in x], table["slowdown_observe"], w, label="incr-observe (cold)", color="#27ae60", alpha=0.9)
    ax.set_xticks(list(x))
    ax.set_xticklabels(table["benchmark"], rotation=45, ha="right")
    ax.set_ylabel("Slowdown vs bash (×)")
    ax.set_title("Cold start: first script time / bash time on same script")
    ax.legend(loc="upper right")
    ax.set_ylim(bottom=0)
    fig.tight_layout()

    for ext in ["pdf", "png"]:
        out_path = out_dir / f"cold_start_overhead.{ext}"
        fig.savefig(out_path, bbox_inches="tight", dpi=150)
        print(f"Saved {out_path}")
    plt.close()
    return 0


if __name__ == "__main__":
    exit(main())
