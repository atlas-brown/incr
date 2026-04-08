#!/usr/bin/env python3
"""Create comm_* directory with placeholder data (used by fetch.sh)."""
import os
import sys

def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    dirname = sys.argv[2] if len(sys.argv) > 2 else "comm_small"
    os.makedirs(dirname, exist_ok=True)
    path = os.path.join(dirname, "placeholder.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"generated n={n}\n")

if __name__ == "__main__":
    main()
