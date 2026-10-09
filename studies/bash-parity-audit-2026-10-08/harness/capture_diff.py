#!/usr/bin/env python3
"""Record suite diff operands, excluding diff's capability self-tests."""
import json
import os
from pathlib import Path
import sys


def main():
    files = [Path(arg) for arg in sys.argv[1:] if not arg.startswith("-") and Path(arg).is_file()]
    if len(files) >= 2 and files[-2].resolve() != files[-1].resolve():
        directory = Path("/tmp/diff-captures")
        directory.mkdir(exist_ok=True)
        record = {
            "actual_path": str(files[-2]),
            "expected_path": str(files[-1]),
            "actual": files[-2].read_bytes().decode(errors="surrogateescape"),
            "expected": files[-1].read_bytes().decode(errors="surrogateescape"),
        }
        target = directory / f'{len(list(directory.glob("*.json"))):04d}.json'
        target.write_text(json.dumps(record) + "\n")
    os.execv("/usr/bin/diff", ["diff", *sys.argv[1:]])


if __name__ == "__main__":
    main()
