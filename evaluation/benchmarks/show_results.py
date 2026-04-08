#!/usr/bin/env python3
"""Pretty-print timing CSVs produced by run_all.sh."""

import csv
import os
import sys
import argparse
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--size", default=None)
    p.add_argument("--results-dir", default=None)
    p.add_argument("--detail", action="store_true")
    p.add_argument("--help", "-h", action="store_true")
    args = p.parse_args()
    if args.help:
        print(
            "Usage: python3 show_results.py [--size min|small] [--results-dir DIR] [--detail]\n"
            "  --detail   per-script times per benchmark"
        )
        sys.exit(0)
    return args


def human_bytes(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def load_csv(path):
    rows = []
    with open(path) as f:
        for row in csv.DictReader(f):
            try:
                rows.append((row["mode"], row["script"], float(row["time_sec"])))
            except (KeyError, ValueError):
                pass
    return rows


def load_cache_size(size_dir, benchmark):
    size_file = size_dir / f"{benchmark}-size.txt"
    if not size_file.exists():
        return None
    try:
        return int(size_file.read_text().split()[0])
    except (ValueError, IndexError):
        return None


def col(text, width, align="left"):
    text = str(text)
    if align == "right":
        return text.rjust(width)
    return text.ljust(width)


def hline(widths, char="─", left="├", mid="┼", right="┤"):
    return left + mid.join(char * w for w in widths) + right


def main():
    args = parse_args()

    script_dir = Path(__file__).parent
    results_base = Path(args.results_dir) if args.results_dir else script_dir.parent / "run_results"

    # Determine size directory
    if args.size:
        sizes = [args.size]
    else:
        sizes = ["small", "min"]

    size_dir = None
    chosen_size = None
    for s in sizes:
        candidate = results_base / s
        if candidate.is_dir() and any(candidate.glob("*-time.csv")):
            size_dir = candidate
            chosen_size = s
            break

    if size_dir is None:
        print(f"No results found in {results_base}/")
        print("Run:  bash run_all.sh --mode easy --size min")
        sys.exit(1)

    # Collect all benchmarks
    csvs = sorted(size_dir.glob("*-time.csv"))
    benchmarks = [f.name.replace("-time.csv", "") for f in csvs]

    if not benchmarks:
        print(f"No timing CSVs found in {size_dir}")
        sys.exit(1)

    # Parse results
    results = {}
    for benchmark, csv_path in zip(benchmarks, csvs):
        rows = load_csv(csv_path)
        bash_rows = [(s, t) for m, s, t in rows if m == "bash"]
        incr_rows = [(s, t) for m, s, t in rows if m == "incr"]
        bash_total = sum(t for _, t in bash_rows)
        incr_total = sum(t for _, t in incr_rows)
        cache_bytes = load_cache_size(size_dir, benchmark)
        results[benchmark] = {
            "bash": bash_rows,
            "incr": incr_rows,
            "bash_total": bash_total,
            "incr_total": incr_total,
            "cache_bytes": cache_bytes,
            "has_incr": bool(incr_rows),
            "has_bash": bool(bash_rows),
        }

    # -------------------------------------------------------------------------
    # Header
    # -------------------------------------------------------------------------
    has_incr = any(r["has_incr"] for r in results.values())
    has_bash = any(r["has_bash"] for r in results.values())
    modes = []
    if has_bash:
        modes.append("bash")
    if has_incr:
        modes.append("incr")

    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║          incr  –  Artifact Evaluation Results               ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"  Input size : {chosen_size}")
    print(f"  Results dir: {size_dir}")
    if has_incr:
        print("  Note: incr times shown are first-run (cold cache, includes")
        print("        tracing overhead). Cache size shows what was stored.")
    print()

    # -------------------------------------------------------------------------
    # Summary table
    # -------------------------------------------------------------------------
    W_BENCH  = 18
    W_BASH   = 12
    W_INCR   = 12
    W_CACHE  = 12

    if has_incr and has_bash:
        widths = [W_BENCH, W_BASH, W_INCR, W_CACHE]
        header = (col("Benchmark", W_BENCH) + "│" +
                  col("bash (s)", W_BASH, "right") + "│" +
                  col("incr (s)", W_INCR, "right") + "│" +
                  col("cache", W_CACHE, "right"))
    elif has_bash:
        widths = [W_BENCH, W_BASH]
        header = col("Benchmark", W_BENCH) + "│" + col("bash (s)", W_BASH, "right")
    else:
        widths = [W_BENCH, W_INCR]
        header = col("Benchmark", W_BENCH) + "│" + col("incr (s)", W_INCR, "right")

    top    = "┌" + "┬".join("─" * w for w in widths) + "┐"
    mid    = "├" + "┼".join("─" * w for w in widths) + "┤"
    bot    = "└" + "┴".join("─" * w for w in widths) + "┘"
    sep    = "│"

    print(top)
    print(sep + header + sep)
    print(mid)

    total_bash = 0.0
    total_incr = 0.0
    for i, benchmark in enumerate(benchmarks):
        r = results[benchmark]
        bash_s = f"{r['bash_total']:.2f}" if r["has_bash"] else "—"
        incr_s = f"{r['incr_total']:.2f}" if r["has_incr"] else "—"
        cache_s = human_bytes(r["cache_bytes"]) if r["cache_bytes"] else "—"
        total_bash += r["bash_total"]
        total_incr += r["incr_total"]

        if has_incr and has_bash:
            row = (col(benchmark, W_BENCH) + sep +
                   col(bash_s, W_BASH, "right") + sep +
                   col(incr_s, W_INCR, "right") + sep +
                   col(cache_s, W_CACHE, "right"))
        elif has_bash:
            row = col(benchmark, W_BENCH) + sep + col(bash_s, W_BASH, "right")
        else:
            row = col(benchmark, W_BENCH) + sep + col(incr_s, W_INCR, "right")
        print(sep + row + sep)
        if i < len(benchmarks) - 1:
            print(mid)

    print(mid)
    bash_tot_s = f"{total_bash:.2f}" if has_bash else "—"
    incr_tot_s = f"{total_incr:.2f}" if has_incr else "—"
    if has_incr and has_bash:
        tot_row = (col("TOTAL", W_BENCH) + sep +
                   col(bash_tot_s, W_BASH, "right") + sep +
                   col(incr_tot_s, W_INCR, "right") + sep +
                   col("", W_CACHE))
    elif has_bash:
        tot_row = col("TOTAL", W_BENCH) + sep + col(bash_tot_s, W_BASH, "right")
    else:
        tot_row = col("TOTAL", W_BENCH) + sep + col(incr_tot_s, W_INCR, "right")
    print(sep + tot_row + sep)
    print(bot)

    # -------------------------------------------------------------------------
    # Per-benchmark detail
    # -------------------------------------------------------------------------
    if args.detail:
        W_SCRIPT = 28
        W_T = 10

        for benchmark in benchmarks:
            r = results[benchmark]
            scripts = sorted(set(s for s, _ in r["bash"]) | set(s for s, _ in r["incr"]))
            bash_map = dict(r["bash"])
            incr_map = dict(r["incr"])

            print()
            print(f"  ── {benchmark} ──")

            if r["has_bash"] and r["has_incr"]:
                dw = [W_SCRIPT, W_T, W_T]
                dtop = "  ┌" + "┬".join("─" * w for w in dw) + "┐"
                dmid = "  ├" + "┼".join("─" * w for w in dw) + "┤"
                dbot = "  └" + "┴".join("─" * w for w in dw) + "┘"
                print(dtop)
                print("  │" + col("script", W_SCRIPT) + "│" +
                      col("bash (s)", W_T, "right") + "│" +
                      col("incr (s)", W_T, "right") + "│")
                print(dmid)
                for s in scripts:
                    b = f"{bash_map[s]:.3f}" if s in bash_map else "—"
                    iv = f"{incr_map[s]:.3f}" if s in incr_map else "—"
                    print("  │" + col(s, W_SCRIPT) + "│" +
                          col(b, W_T, "right") + "│" +
                          col(iv, W_T, "right") + "│")
                print(dbot)
            else:
                mode = "bash" if r["has_bash"] else "incr"
                data = dict(r[mode])
                dw = [W_SCRIPT, W_T]
                dtop = "  ┌" + "┬".join("─" * w for w in dw) + "┐"
                dmid = "  ├" + "┼".join("─" * w for w in dw) + "┤"
                dbot = "  └" + "┴".join("─" * w for w in dw) + "┘"
                print(dtop)
                print("  │" + col("script", W_SCRIPT) + "│" +
                      col(f"{mode} (s)", W_T, "right") + "│")
                print(dmid)
                for s in scripts:
                    t = f"{data[s]:.3f}" if s in data else "—"
                    print("  │" + col(s, W_SCRIPT) + "│" + col(t, W_T, "right") + "│")
                print(dbot)

    print()


if __name__ == "__main__":
    main()
