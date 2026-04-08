#!/usr/bin/env python3
"""Emit synthetic log lines with IPs (used by fetch.sh for word-freq inputs)."""
import sys

def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    for i in range(n):
        a, b = i % 256, (i * 7) % 256
        print(
            f"10.{a//16}.{b}.{i % 250} - - [01/Jan/2020:12:00:{i % 60:02d} +0000] "
            f'"GET /x HTTP/1.1" 200 {100 + i % 500} "-" "bench"'
        )

if __name__ == "__main__":
    main()
