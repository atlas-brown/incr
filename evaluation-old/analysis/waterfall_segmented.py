#!/usr/bin/env python3
"""
Segmented Waterfall (Gantt) chart generator for stream-command logs.

This extends the original "waterfall.py" by breaking each command interval into
sub-segments representing the *stage* the command is executing.

Assumes log lines like:
    [HH:MM:SS.mmm] [command] message

Default stage tokens (ordered as they typically appear):
    - "Starting stream command"                            -> stage "start"
    - "Spawned stream child"                               -> stage "spawn"
    - "Loaded cache directory"                             -> stage "load_cache_dir"
    - "Loaded cache data and child outputs"                -> stage "load_cache_data"
    - "Extracted dependencies and committed files"         -> stage "extract_and_commit"
    - "Outputted cached data and committed files"          -> stage "output_and_commit"

We pair each command's "start" with its corresponding end (any line that matches
one of the end tokens), then within that interval we segment by the above stage
markers seen for that *same* command instance.

Usage:
    python waterfall_segmented.py path/to/trace.txt --out-png trace_waterfall.png \
        [--out-csv intervals.csv] [--out-seg-csv segments.csv] [--title "My Run"] [--max-bars 0]

Chart notes
- Uses matplotlib only; no explicit colors/styles are set (follows environment rules).
- Each command instance is a horizontal bar broken into adjacent segments.
- Legend lists stages. If some stages are absent, they won't appear.
"""

import argparse
import re
from collections import defaultdict, deque
from datetime import datetime, date, timedelta
from typing import Deque, Dict, List, Tuple, Optional

import matplotlib.pyplot as plt
import pandas as pd

LINE_RE = re.compile(r'^\[(?P<time>\d{2}:\d{2}:\d{2}\.\d{3})\]\s+\[(?P<cmd>[^\]]+)\]\s+(?P<msg>.*)$')

DEFAULT_START_TOKEN = "Starting stream command"
DEFAULT_END_TOKENS = (
    "Outputted cached data and committed files",
    "Extracted dependencies and committed files",
    "committed files",  # fallback catch-all
)

# Stage dictionary maps substring -> canonical stage name (first match wins; order matters).
STAGE_TOKENS = [
    ("Starting stream command", "start"),
    ("Spawned stream child", "spawn"),
    ("Loaded cache directory", "load_cache_dir"),
    ("Loaded cache data and child outputs", "load_cache_data"),
    ("Extracted dependencies and committed files", "extract_and_commit"),
    ("Outputted cached data and committed files", "output_and_commit"),
]

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate a segmented waterfall (Gantt) PNG from a stream-command log.")
    p.add_argument("log", help="Path to log file")
    p.add_argument("--out-png", default="waterfall_segmented.png", help="Output PNG path (default: waterfall_segmented.png)")
    p.add_argument("--out-csv", default=None, help="Optional CSV to save paired intervals (one row per command instance)")
    p.add_argument("--out-seg-csv", default=None, help="Optional CSV to save per-stage segments (multiple rows per instance)")
    p.add_argument("--title", default="Segmented Waterfall of Command Executions", help="Chart title")
    p.add_argument("--start-token", default=DEFAULT_START_TOKEN, help="Start token substring")
    p.add_argument("--end-token", action="append", dest="end_tokens",
                   help="End token substring (may be passed multiple times). If omitted, uses defaults")
    p.add_argument("--max-bars", type=int, default=0, help="Show at most N command instances (0 = all)")
    p.add_argument("--figwidth", type=float, default=14.0, help="Figure width in inches")
    p.add_argument("--row-height", type=float, default=0.2, help="Height per bar (inches) for autosizing")
    p.add_argument("--min-height", type=float, default=6.0, help="Minimum figure height in inches")
    p.add_argument("--stage-boundary", choices=["left", "right"], default="left",
                   help="Interpret stage logs as beginning (left) or completing (right) a stage (default: left)")
    p.add_argument("--stage-attribution", choices=["fifo", "lifo", "state"], default="state",
                   help="Assign mid-interval markers: fifo, lifo, or state (state-machine-aware FIFO, default)")
    return p.parse_args()

def _stage_from_msg(msg: str) -> Optional[str]:
    for token, stage in STAGE_TOKENS:
        if token in msg:
            return stage
    return None

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
            msg = m.group("msg").strip()
            events.append({
                "lineno": lineno,
                "dt": dt,
                "cmd": m.group("cmd").strip(),
                "msg": msg,
                "is_start": start_token in msg,
                "is_end": any(tok in msg for tok in end_tokens),
                "stage": _stage_from_msg(msg),
            })
    return events


def pair_and_segment(events: List[dict]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    # Default: state-machine aware FIFO + left-bound semantics

    """State-machine aware pairing/segmentation.

    - Intervals: paired FIFO by command (first start -> first end).
    - Stage markers (non-start/non-end):
        Assigned to the earliest still-open instance of that command whose
        current stage index is strictly less than the incoming stage index.
        (i.e., the first instance that hasn't reached this stage yet)
    - Left-bound semantics: a marker denotes the *begin* of that stage.
    """
    # Build stage order/index
    stage_to_idx = {stage: i for i, (_, stage) in enumerate(STAGE_TOKENS)}
    # Per-cmd queue of open instances
    # Each instance dict: {
    #   "start_ev": dict, "instance_id": int,
    #   "markers": List[(dt, stage, msg)], "curr_idx": int
    # }
    open_q: Dict[str, Deque[dict]] = defaultdict(deque)
    intervals = []
    instance_markers: Dict[int, List[Tuple[datetime, Optional[str], str]]] = {}
    instance_id_counter = 0

    # Helper: create a new instance on start
    def _open_instance(cmd: str, ev: dict) -> dict:
        nonlocal instance_id_counter
        instance_id_counter += 1
        inst = {
            "start_ev": ev,
            "instance_id": instance_id_counter,
            "markers": [],
            "curr_idx": -1,  # before 'start'; we'll push 'start' explicitly if present
        }
        # If this start line also carries a stage token (usually "start"), record it
        if ev["stage"] is not None:
            inst["markers"].append((ev["dt"], ev["stage"], ev["msg"]))
            inst["curr_idx"] = max(inst["curr_idx"], stage_to_idx.get(ev["stage"], -1))
        else:
            # If no stage token, still mark a BEGIN to anchor segments
            inst["markers"].append((ev["dt"], None, "BEGIN"))
        open_q[cmd].append(inst)
        return inst

    # Helper: assign a stage marker to an open instance (FIFO), respecting progression
    def _assign_stage(cmd: str, ev: dict):
        if ev["stage"] is None or not open_q[cmd]:
            return
        sidx = stage_to_idx.get(ev["stage"], None)
        if sidx is None:
            return
        # Find earliest instance whose curr_idx < sidx
        chosen = None
        for inst in open_q[cmd]:
            if inst["curr_idx"] < sidx:
                chosen = inst
                break
        # Fallback: if none found (out-of-order or duplicates), attach to the oldest anyway
        if chosen is None:
            chosen = open_q[cmd][0]
        chosen["markers"].append((ev["dt"], ev["stage"], ev["msg"]))
        chosen["curr_idx"] = max(chosen["curr_idx"], sidx)

    # Helper: close instance on end (FIFO)
    def _close_instance(cmd: str, ev: dict):
        if not open_q[cmd]:
            return None
        inst = open_q[cmd].popleft()
        # If the end line also encodes a stage token, capture it (still left-bound)
        if ev["stage"] is not None:
            sidx = stage_to_idx.get(ev["stage"], -1)
            if sidx > inst["curr_idx"]:
                inst["markers"].append((ev["dt"], ev["stage"], ev["msg"]))
                inst["curr_idx"] = sidx
        # Build interval row
        intervals.append({
            "instance_id": inst["instance_id"],
            "cmd": cmd,
            "start": inst["start_ev"]["dt"],
            "end": ev["dt"],
            "start_line": inst["start_ev"]["lineno"],
            "end_line": ev["lineno"],
            "end_msg": ev["msg"],
        })
        instance_markers[inst["instance_id"]] = inst["markers"]
        return inst

    # Process events chronologically
    for ev in sorted(events, key=lambda x: x["dt"]):
        cmd = ev["cmd"]
        if ev["is_start"]:
            _open_instance(cmd, ev)
        elif ev["is_end"]:
            _close_instance(cmd, ev)
        else:
            _assign_stage(cmd, ev)

    intervals_df = pd.DataFrame(intervals).sort_values(["start", "instance_id"]).reset_index(drop=True)

    # Build per-stage segments with left-bound semantics
    seg_rows = []
    if not intervals_df.empty:
        for _, row in intervals_df.iterrows():
            inst_id = row["instance_id"]
            t_start = row["start"]
            t_end = row["end"]
            markers = instance_markers.get(inst_id, [])
            # Keep markers within [start, end]
            markers = [(dt, stg, msg) for (dt, stg, msg) in markers if t_start <= dt <= t_end]
            # Ensure we have an anchor at t_start
            if not markers or markers[0][0] > t_start:
                markers = [(t_start, None, "BEGIN")] + markers
            markers = sorted(markers, key=lambda x: x[0])
            # Ensure we have a terminator at t_end carrying forward last stage
            if markers[-1][0] < t_end:
                markers.append((t_end, markers[-1][1], "END"))

            # Coalesce adjacent duplicate stages while building segments
            last_t = None
            last_stage = None
            for i in range(len(markers) - 1):
                seg_t0, seg_stage, _ = markers[i]
                seg_t1, _, _ = markers[i + 1]
                stage_name = seg_stage or "unknown"
                if last_t is None:
                    last_t = seg_t0
                    last_stage = stage_name
                elif stage_name != last_stage or seg_t0 != last_t:
                    # flush previous
                    seg_rows.append({
                        "instance_id": inst_id,
                        "cmd": row["cmd"],
                        "seg_start": last_t,
                        "seg_end": seg_t0,
                        "stage": last_stage,
                    })
                    last_t = seg_t0
                    last_stage = stage_name
            # flush final to t_end
            if last_t is not None:
                seg_rows.append({
                    "instance_id": inst_id,
                    "cmd": row["cmd"],
                    "seg_start": last_t,
                    "seg_end": t_end,
                    "stage": last_stage,
                })

    segments_df = pd.DataFrame(seg_rows).sort_values(["seg_start", "instance_id"]).reset_index(drop=True)
    return intervals_df, segments_df


def plot_segmented_waterfall(intervals_df: pd.DataFrame,
                             segments_df: pd.DataFrame,
                             out_png: str,
                             title: str,
                             figwidth: float,
                             row_height: float,
                             min_height: float,
                             max_bars: int = 0) -> None:
    if intervals_df.empty:
        raise SystemExit("No intervals parsed. Check tokens or log format.")

    # Optionally reduce number of instances shown
    if max_bars and max_bars > 0:
        keep_ids = set(intervals_df.sort_values("start").head(max_bars)["instance_id"].tolist())
        intervals_df = intervals_df[intervals_df["instance_id"].isin(keep_ids)].copy()
        segments_df = segments_df[segments_df["instance_id"].isin(keep_ids)].copy()

    # Prepare labels and relative times (shared zero)
    t0 = intervals_df["start"].min()

    # order bars by start time
    intervals_df = intervals_df.sort_values("start").reset_index(drop=True)
    intervals_df["ordinal"] = intervals_df.groupby("cmd").cumcount() + 1
    intervals_df["label"] = intervals_df["cmd"] + " #" + intervals_df["ordinal"].astype(str)
    intervals_df["ypos"] = range(len(intervals_df))

    # map instance_id -> ypos and label
    y_map = dict(zip(intervals_df["instance_id"], intervals_df["ypos"]))
    label_map = dict(zip(intervals_df["instance_id"], intervals_df["label"]))

    # Transform segments
    seg = segments_df.copy()
    seg["ypos"] = seg["instance_id"].map(y_map)
    seg = seg.dropna(subset=["ypos"])  # drop any pruned segments
    seg["start_rel_s"] = (seg["seg_start"] - t0).dt.total_seconds()
    seg["end_rel_s"]   = (seg["seg_end"]   - t0).dt.total_seconds()
    seg["duration_s"]  = seg["end_rel_s"] - seg["start_rel_s"]

    # Autosize height
    height = max(min_height, row_height * len(intervals_df))

    # Plot
    plt.figure(figsize=(figwidth, height))
    # one bar per segment; matplotlib default color cycle will differentiate stages when we map by stage
    # To construct a legend per stage, we'll plot by unique stages serially.
    stage_order = [s for _, s in STAGE_TOKENS if s in set(seg["stage"].tolist())]  # deterministic stage order

    legend_handles = {}
    for stage in stage_order:
        sub = seg[seg["stage"] == stage]
        # barh per segment (no explicit colors/styles)
        bars = plt.barh(sub["ypos"], sub["duration_s"], left=sub["start_rel_s"], label=stage)
        # Register a single handle for the legend if not already
        if stage not in legend_handles and len(bars) > 0:
            legend_handles[stage] = bars[0]

    # Y axis labels
    plt.yticks(intervals_df["ypos"], intervals_df["label"])

    plt.xlabel("Time since first start (seconds)")
    plt.title(title)
    if legend_handles:
        plt.legend(list(legend_handles.values()), list(legend_handles.keys()), title="Stage", loc="best")
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close()

def main():
    args = parse_args()
    end_tokens = tuple(args.end_tokens) if args.end_tokens else DEFAULT_END_TOKENS

    events = parse_log(args.log, args.start_token, end_tokens)
    if args.stage_attribution == "state" and args.stage_boundary == "left":
        intervals_df, segments_df = pair_and_segment(events)
    else:
        intervals_df, segments_df = _pair_and_segment_flexible(events, args.stage_attribution, args.stage_boundary)

    # Optional CSV dumps
    if args.out_csv:
        intervals_df.to_csv(args.out_csv, index=False)
    if args.out_seg_csv:
        segments_df.to_csv(args.out_seg_csv, index=False)

    # Plot
    plot_segmented_waterfall(
        intervals_df=intervals_df,
        segments_df=segments_df,
        out_png=args.out_png,
        title=args.title,
        figwidth=args.figwidth,
        row_height=args.row_height,
        min_height=args.min_height,
        max_bars=args.max_bars,
    )

    # Brief summary
    if not intervals_df.empty:
        total_span = (intervals_df["end"].max() - intervals_df["start"].min()).total_seconds()
        print(f"Instances: {len(intervals_df)}  |  Segments: {len(segments_df)}  |  Total span: {total_span:.3f}s  |  PNG: {args.out_png}")
        if args.out_csv:
            print(f"Intervals CSV: {args.out_csv}")
        if args.out_seg_csv:
            print(f"Segments CSV: {args.out_seg_csv}")
    else:
        print("No instances found.")

if __name__ == "__main__":
    main()
