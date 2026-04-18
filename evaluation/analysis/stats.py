#!/usr/bin/env python3
"""
Aggregate timing stats from evaluation *-time.csv files (bash, incr, incr-observe).

Usage:
  cd incr/evaluation/analysis
  python3 stats.py --results-dir ../observe_results/observe_1/small
  python3 stats.py --results-dir ../run_results/small
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def discover_benchmarks(results_dir: Path) -> list:
    return sorted(
        p.stem.replace("-time", "")
        for p in results_dir.glob("*-time.csv")
    )


def load_all_results(results_dir: Path) -> pd.DataFrame:
    results_dir = Path(results_dir)
    frames = []
    for b in discover_benchmarks(results_dir):
        path = results_dir / f"{b}-time.csv"
        df = pd.read_csv(path)
        df["benchmark"] = b
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def first_script_overheads(all_data: pd.DataFrame) -> pd.DataFrame:
    """Cold start: first bash script vs same script under incr / incr-observe."""
    rows = []
    for benchmark in sorted(all_data["benchmark"].unique()):
        sub = all_data[all_data["benchmark"] == benchmark]
        bash = sub[sub["mode"] == "bash"]
        if bash.empty:
            continue
        script0 = bash.iloc[0]["script"]
        t_b = float(bash.iloc[0]["time_sec"])
        if t_b <= 0:
            continue
        row = {"benchmark": benchmark, "script": script0, "bash_sec": t_b}
        for mode in ("incr", "incr-observe"):
            m = sub[(sub["mode"] == mode) & (sub["script"] == script0)]
            if m.empty:
                row[f"{mode}_sec"] = float("nan")
                row[f"{mode}_slowdown_vs_bash"] = float("nan")
                continue
            t = float(m.iloc[0]["time_sec"])
            row[f"{mode}_sec"] = t
            row[f"{mode}_slowdown_vs_bash"] = t / t_b
        rows.append(row)
    return pd.DataFrame(rows)


def print_first_script_summary(table: pd.DataFrame) -> None:
    if table.empty:
        print("No first-script overhead table (missing bash rows?).")
        return
    print("\n=== First script (cold start) vs bash ===\n")
    display = table.copy()
    for col in ("incr_slowdown_vs_bash", "incr-observe_slowdown_vs_bash"):
        if col in display.columns:
            display[col] = display[col].map(lambda x: f"{x:.2f}x" if pd.notna(x) else "n/a")
    # Flatten column names for display
    rename = {
        "bash_sec": "bash_s",
        "incr_sec": "incr_s",
        "incr-observe_sec": "obs_s",
        "incr_slowdown_vs_bash": "incr/bash",
        "incr-observe_slowdown_vs_bash": "obs/bash",
    }
    display = display.rename(columns={k: v for k, v in rename.items() if k in display.columns})
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)
    print(display.to_string(index=False))

    for mode, col in [("incr", "incr_slowdown_vs_bash"), ("incr-observe", "incr-observe_slowdown_vs_bash")]:
        s = table[col].dropna()
        if s.empty:
            print(f"\n({mode}: no data)")
            continue
        print(f"\n{mode} vs bash (first script): max slowdown {s.max():.2f}x, "
              f"mean slowdown {s.mean():.2f}x, min slowdown {s.min():.2f}x")


def per_iteration_speedups_vs_bash(all_data: pd.DataFrame, target_mode: str) -> pd.Series:
    """bash_time / target_time for each script, every benchmark (aligned by bash script order)."""
    vals = []
    for benchmark in sorted(all_data["benchmark"].unique()):
        sub = all_data[all_data["benchmark"] == benchmark]
        bash_df = sub[sub["mode"] == "bash"]
        tgt_df = sub[sub["mode"] == target_mode]
        if bash_df.empty or tgt_df.empty:
            continue
        bash_map = bash_df.set_index("script")["time_sec"]
        tgt_map = tgt_df.set_index("script")["time_sec"]
        for script in bash_df["script"].tolist():
            if script not in tgt_map.index or script not in bash_map.index:
                continue
            b_t = float(bash_map[script])
            u_t = float(tgt_map[script])
            if u_t <= 0:
                continue
            vals.append(b_t / u_t)
    return pd.Series(vals, dtype=float)


def print_speedup_section(all_data: pd.DataFrame) -> None:
    print("\n=== Per-script speedup vs bash (bash / mode) ===\n")
    for mode in ("incr", "incr-observe"):
        s = per_iteration_speedups_vs_bash(all_data, mode)
        if s.empty:
            print(f"{mode}: no paired rows\n")
            continue
        gt1 = s[s > 1]
        print(f"{mode}:")
        print(f"  count: {len(s)}")
        print(f"  max speedup:  {s.max():.2f}x")
        print(f"  mean speedup: {s.mean():.2f}x")
        if gt1.empty:
            print("  min speedup > 1: n/a")
        else:
            print(f"  min speedup > 1: {gt1.min():.2f}x")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Stats over *-time.csv (bash vs incr / incr-observe)")
    parser.add_argument(
        "--results-dir",
        default=None,
        help="Directory with <benchmark>-time.csv (default: run_results/small or min under evaluation/)",
    )
    args = parser.parse_args()

    eval_dir = Path(__file__).resolve().parent.parent
    if args.results_dir:
        results_dir = Path(args.results_dir)
        if not results_dir.is_absolute():
            results_dir = eval_dir / results_dir
    else:
        results_dir = eval_dir / "run_results" / "small"
        if not results_dir.exists():
            results_dir = eval_dir / "run_results" / "min"

    if not results_dir.exists():
        print(f"Results directory not found: {results_dir}")
        return 1

    all_data = load_all_results(results_dir)
    if all_data.empty:
        print(f"No CSVs in {results_dir}")
        return 1

    print(f"Results: {results_dir}")
    print(f"Benchmarks: {sorted(all_data['benchmark'].unique())}")

    ft = first_script_overheads(all_data)
    # normalize column names for observe (hyphen in key)
    print_first_script_summary(ft)
    print_speedup_section(all_data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
