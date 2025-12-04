#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

ED_CMD = re.compile(r'^(\d+)(?:,(\d+))?([acd])(\d+)(?:,(\d+))?$')

def strip_leading_lineno(s: str) -> str:
    m = re.match(r'^\s*\d+\s+(.*)$', s)  # handles `cat -n` prefixes like "  7 109c109"
    return m.group(1) if m else s

def split_ed_chunks(diff_text: str):
    lines = diff_text.splitlines(keepends=True)
    i, n = 0, len(lines)
    while i < n:
        raw = lines[i]
        header_line = strip_leading_lineno(raw).rstrip("\n")
        m = ED_CMD.match(header_line.strip())
        if not m:
            i += 1
            continue

        op = m.group(3)  # 'a' | 'c' | 'd'
        i += 1

        old_block, new_block = 0, 0

        # OLD lines: "< ..."
        while i < n and lines[i].lstrip().startswith("<"):
            old_block += 1
            i += 1

        # Optional separator for 'c'
        if i < n and lines[i].strip() == '---':
            i += 1

        # NEW lines: "> ..."
        while i < n and lines[i].lstrip().startswith(">"):
            new_block += 1
            i += 1

        yield op, old_block, new_block

def differences_for_chunk(op: str, old_cnt: int, new_cnt: int) -> int:
    if op == 'a':
        return new_cnt
    if op == 'd':
        return old_cnt
    # 'c'
    return max(old_cnt, new_cnt)

def main():
    ap = argparse.ArgumentParser(description="Print number of differences from normal/ed diffs.")
    ap.add_argument("-i", "--input",  default="results", help="Directory with .diff files (default: results)")
    ap.add_argument("-g", "--glob",   default="*.diff",  help="Glob for diff files (default: *.diff)")
    args = ap.parse_args()

    in_dir = Path(args.input)
    grand_total = 0

    for diff_path in sorted(in_dir.glob(args.glob)):
        text = diff_path.read_text(errors="replace")
        file_total = 0
        for op, old_cnt, new_cnt in split_ed_chunks(text):
            file_total += differences_for_chunk(op, old_cnt, new_cnt)
        print(f"{diff_path.name} {file_total}")
        grand_total += file_total

    print(f"TOTAL {grand_total}")

if __name__ == "__main__":
    main()
