#!/bin/bash
set -euo pipefail

# Keep the previous index intact until the full pipeline succeeds. Sorting to
# the same path that merge.js reads races with opening/truncating that path.
next_index=$(mktemp "$OUT/index.XXXXXX")
trap 'rm -f "$next_index"' EXIT
cat "$1" |
  c/process.sh |
  c/stem.js |
  c/combine.sh |
  c/invert.sh "$2" |
  c/merge.js "$OUT/global-index.txt" |
  sort > "$next_index"
mv "$next_index" "$OUT/global-index.txt"
