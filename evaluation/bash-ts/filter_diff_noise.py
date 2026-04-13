#!/usr/bin/env python3
import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


HEADER_RE = re.compile(r"^(\d+(?:,\d+)?)([acd])(\d+(?:,\d+)?)\n?$")
LINE_NUMBER_RE = re.compile(r": line \d+:")
INCR_PREFIX_RE = re.compile(
    r"(?P<indent>\s*)\S+/target/release/incr --try \S+/src/scripts/try\.sh --cache \S+ "
)


@dataclass
class Hunk:
    header: str
    body: list[str]
    op: str


def normalize_line(line: str) -> str:
    line = LINE_NUMBER_RE.sub(": line <line>:", line)
    line = line.replace("/tmp/incr-bash-ts.sh", "/tmp/bash")
    line = line.replace("incr-bash-ts.sh", "bash")
    line = INCR_PREFIX_RE.sub(lambda match: match.group("indent"), line)
    return line


def parse_diff(text: str) -> tuple[list[str], list[Hunk]]:
    lines = text.splitlines(keepends=True)
    preamble: list[str] = []
    hunks: list[Hunk] = []
    i = 0

    while i < len(lines) and not HEADER_RE.match(lines[i]):
        preamble.append(lines[i])
        i += 1

    while i < len(lines):
        header_match = HEADER_RE.match(lines[i])
        if not header_match:
            preamble.append(lines[i])
            i += 1
            continue

        header = lines[i]
        op = header_match.group(2)
        i += 1
        body: list[str] = []
        while i < len(lines) and not HEADER_RE.match(lines[i]):
            body.append(lines[i])
            i += 1
        hunks.append(Hunk(header=header, body=body, op=op))

    return preamble, hunks


def parse_hunk_sides(hunk: Hunk) -> tuple[list[str], list[str]]:
    left: list[str] = []
    right: list[str] = []

    if hunk.op == "c":
        right_side = False
        for line in hunk.body:
            if line.startswith("---"):
                right_side = True
                continue
            if line.startswith("< ") and not right_side:
                left.append(line[2:].rstrip("\n"))
            elif line.startswith("> ") and right_side:
                right.append(line[2:].rstrip("\n"))
    elif hunk.op == "d":
        for line in hunk.body:
            if line.startswith("< "):
                left.append(line[2:].rstrip("\n"))
    elif hunk.op == "a":
        for line in hunk.body:
            if line.startswith("> "):
                right.append(line[2:].rstrip("\n"))

    return left, right


def hunk_is_noise(hunk: Hunk) -> bool:
    left, right = parse_hunk_sides(hunk)
    normalized_left = [normalize_line(line) for line in left]
    normalized_right = [normalize_line(line) for line in right]
    return normalized_left == normalized_right


def filter_diff_text(text: str) -> str:
    preamble, hunks = parse_diff(text)
    kept: list[str] = list(preamble)

    for hunk in hunks:
        if hunk_is_noise(hunk):
            continue
        kept.append(hunk.header)
        kept.extend(hunk.body)

    return "".join(kept)


def process_path(path: str, in_place: bool) -> None:
    if path == "-":
        original = sys.stdin.read()
        filtered = filter_diff_text(original)
        sys.stdout.write(filtered)
        return

    file_path = Path(path)
    original = file_path.read_text(encoding="utf-8", errors="replace")
    filtered = filter_diff_text(original)
    if in_place:
        file_path.write_text(filtered, encoding="utf-8")
    else:
        sys.stdout.write(filtered)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Remove bash-ts diff hunks that only differ by line numbers, wrapper names, or injected incr prefixes."
    )
    parser.add_argument("paths", nargs="+", help="Diff file(s) to filter, or - for stdin")
    parser.add_argument(
        "-i",
        "--in-place",
        action="store_true",
        help="Rewrite the provided diff files instead of printing to stdout",
    )
    args = parser.parse_args()

    if not args.in_place and len(args.paths) > 1:
        parser.error("use --in-place when passing multiple files")

    exit_code = 0
    for path in args.paths:
        try:
            process_path(path, args.in_place)
        except FileNotFoundError:
            print(f"error: {path}: no such file", file=sys.stderr)
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
