#!/usr/bin/env python3
"""
Waterfall (Gantt) chart generator for stream-command logs.

Assumes log lines like:
    [HH:MM:SS.mmm] [command] message
and pairs:
    Start token:  "Starting stream command"
    End tokens:   "Outputted cached data and committed files",
                  "Extracted dependencies and committed files",
                  or any message containing "committed files" (fallback).

Usage:
    python waterfall_from_log.py path/to/trace.txt --out-png trace_waterfall.png \
        [--out-csv intervals.csv] [--title "My Run"] [--max-bars 0]

Notes
- Handles multiple concurrent starts per command by queueing them.
- Handles day rollover (timestamps resetting after midnight).
- If --max-bars > 0, limits visible bars to the first N intervals by start time.
"""

import argparse
import re
from collections import defaultdict, deque
from datetime import datetime, date, timedelta
from typing import Deque, Dict, List, Tuple

import matplotlib.pyplot as plt
import pandas as pd

LINE_RE = re.compile(r'^\[(?P<time>\d{2}:\d{2}:\d{2}\.\d{3})\]\s+\[(?P<cmd>[^\]]+)\]\s+(?P<msg>.*)$')

DEFAULT_START_TOKEN = "Starting stream command"
DEFAULT_END_TOKENS = (
    "Outputted cached data and committed files",
    "Extracted dependencies and committed files",
    "committed files",  # fallback
)

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate a waterfall (Gantt) PNG from a stream-command log.")
    p.add_argument("log", help="Path to log file")
    p.add_argument("--out-png", default="waterfall.png", help="Output PNG path (default: waterfall.png)")
    p.add_argument("--out-csv", default=None, help="Optional CSV to save parsed intervals")
    p.add_argument("--title", default="Waterfall of Command Executions", help="Chart title")
    p.add_argument("--start-token", default=DEFAULT_START_TOKEN, help="Start token substring")
    p.add_argument("--end-token", action="append", dest="end_tokens",
                   help="End token substring (may be passed multiple times). If omitted, uses defaults")
    p.add_argument("--max-bars", type=int, default=0, help="Show at most N intervals (0 = all)")
    p.add_argument("--figwidth", type=float, default=12.0, help="Figure width in inches")
    p.add_argument("--row-height", type=float, default=0.15, help="Height per bar (inches) for autosizing")
    p.add_argument("--min-height", type=float, default=6.0, help="Minimum figure height in inches")
    return p.parse_args()

def parse_log(path: str, start_token: str, end_tokens: Tuple[str, ...]) -> List[dict]:
    """Parse log into a list of events with datetimes, handling day rollover."""
    events = []
    day = date.today()
    prev_time = None

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for lineno, line in enumerate(f, start=1):
            m = LINE_RE.match(line.strip())
            if not m:
                continue
            ts = datetime.strptime(m.group("time"), "%H:%M:%S.%f").time()
            # day rollover handling: if time goes backwards, advance one day
            if prev_time and ts < prev_time:
                day = day + timedelta(days=1)
            prev_time = ts

            dt = datetime.combine(day, ts)
            msg = m.group("msg")
            events.append({
                "lineno": lineno,
                "dt": dt,
                "cmd": m.group("cmd").strip(),
                "msg": msg.strip(),
                "is_start": start_token in msg,
                "is_end": any(tok in msg for tok in end_tokens),
            })
    return events

def pair_intervals(events: List[dict]) -> pd.DataFrame:
    """Pair start/end events per command using a FIFO queue; return a DataFrame of intervals."""
    open_starts: Dict[str, Deque[dict]] = defaultdict(deque)
    intervals = []

    for ev in sorted(events, key=lambda x: x["dt"]):
        cmd = ev["cmd"]
        if ev["is_start"]:
            open_starts[cmd].append(ev)
        elif ev["is_end"]:
            if open_starts[cmd]:
                s = open_starts[cmd].popleft()
                intervals.append({
                    "cmd": cmd,
                    "start": s["dt"],
                    "end": ev["dt"],
                    "start_line": s["lineno"],
                    "end_line": ev["lineno"],
                    "end_msg": ev["msg"],
                })

    df = pd.DataFrame(intervals).sort_values("start").reset_index(drop=True)
    return df

def plot_waterfall(df: pd.DataFrame, out_png: str, title: str, figwidth: float, row_height: float, min_height: float, max_bars: int = 0) -> None:
    if df.empty:
        raise SystemExit("No intervals parsed. Check tokens or log format.")

    # Prepare labels and relative times
    df = df.copy()
    df["ordinal"] = df.groupby("cmd").cumcount() + 1
    df["label"] = df["cmd"] + " #" + df["ordinal"].astype(str)
    t0 = df["start"].min()
    df["start_rel_s"] = (df["start"] - t0).dt.total_seconds()
    df["end_rel_s"]   = (df["end"]   - t0).dt.total_seconds()
    df["duration_s"]  = df["end_rel_s"] - df["start_rel_s"]

    if max_bars and max_bars > 0:
        df = df.head(max_bars)

    # Autosize height based on number of bars
    height = max(min_height, row_height * len(df))

    plt.figure(figsize=(figwidth, height))
    ypos = list(range(len(df)))
    plt.barh(ypos, df["duration_s"], left=df["start_rel_s"])  # (no explicit colors/styles)
    plt.yticks(ypos, df["label"])
    plt.xlabel("Time since first start (seconds)")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close()

def main():
    args = parse_args()
    end_tokens = tuple(args.end_tokens) if args.end_tokens else DEFAULT_END_TOKENS

    events = parse_log(args.log, args.start_token, end_tokens)
    df = pair_intervals(events)

    # Optional CSV dump
    if args.out_csv:
        pd.DataFrame(df).to_csv(args.out_csv, index=False)

    # Plot
    plot_waterfall(
        df=df,
        out_png=args.out_png,
        title=args.title,
        figwidth=args.figwidth,
        row_height=args.row_height,
        min_height=args.min_height,
        max_bars=args.max_bars,
    )

    # Brief summary
    total_span = (df["end"].max() - df["start"].min()).total_seconds()
    print(f"Intervals: {len(df)}  |  Total span: {total_span:.3f}s  |  PNG: {args.out_png}")
    if args.out_csv:
        print(f"CSV: {args.out_csv}")

if __name__ == "__main__":
    main()
