#!/usr/bin/env bash
set -e
set -o pipefail
for f in inputs/item*.txt; do
 /usr/bin/install -m 644 "$f" "outputs/${f##*/}" </dev/null
done
