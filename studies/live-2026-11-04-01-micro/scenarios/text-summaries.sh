#!/usr/bin/env bash
set -e
set -o pipefail
summarize() { /usr/bin/wc -l "$1" </dev/null; /usr/bin/grep -c alpha "$1" </dev/null; }
for f in inputs/item*.txt; do
 summarize "$f"
done
