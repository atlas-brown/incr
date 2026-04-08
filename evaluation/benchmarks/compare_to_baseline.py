#!/usr/bin/env python3
"""Compare aggregated timing CSVs to evaluation/default_results/default_3."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


def sum_mode(path: Path, mode: str) -> float:
    total = 0.0
    with path.open() as f:
        for row in csv.DictReader(f):
            if row.get("mode") == mode:
                total += float(row["time_sec"])
    return total


def main() -> None:
    p = argparse.ArgumentParser(description="Compare run_results to default_results baseline")
    p.add_argument(
        "--baseline",
        default=None,
        help="Directory with *-time.csv (default: default_results/default_3)",
    )
    p.add_argument(
        "--current",
        default=None,
        help="Directory with *-time.csv (default: run_results/small)",
    )
    args = p.parse_args()

    bench_dir = Path(__file__).resolve().parent
    eval_dir = bench_dir.parent
    baseline_dir = Path(args.baseline) if args.baseline else eval_dir / "default_results" / "default_3"
    current_dir = Path(args.current) if args.current else eval_dir / "run_results" / "small"

    if not baseline_dir.is_dir():
        print(f"Baseline not found: {baseline_dir}", file=sys.stderr)
        sys.exit(1)
    if not current_dir.is_dir():
        print(f"Current results not found: {current_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Baseline: {baseline_dir}")
    print(f"Current:  {current_dir}")
    print()
    print(f"{'benchmark':<18} {'bash_r':>8} {'incr_r':>8}  (ratio current/baseline; ~1.0 = same machine)")
    print("-" * 60)

    bad = False
    for bcsv in sorted(baseline_dir.glob("*-time.csv")):
        name = bcsv.name
        cur = current_dir / name
        if not cur.exists():
            print(f"{name[:-9]:<18} {'—':>8} {'—':>8}  (no current file)")
            continue
        b_b = sum_mode(bcsv, "bash")
        i_b = sum_mode(bcsv, "incr")
        b_c = sum_mode(cur, "bash")
        i_c = sum_mode(cur, "incr")
        rb = b_c / b_b if b_b > 1e-6 else 0.0
        ri = i_c / i_b if i_b > 1e-6 else 0.0

        flag = ""
        if rb < 0.02 and b_b > 60:
            flag = "  <-- bash very fast vs baseline (check inputs)"
            bad = True
        elif rb > 50 and b_b < 600:
            flag = "  <-- bash much slower (weaker machine or large inputs)"

        print(f"{name[:-9]:<18} {rb:8.2f} {ri:8.2f}{flag}")

    print()
    if bad:
        print("Warning: at least one benchmark looks suspiciously fast.", file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
