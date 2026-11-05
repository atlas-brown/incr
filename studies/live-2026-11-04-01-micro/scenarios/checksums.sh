#!/usr/bin/env bash
set -e
set -o pipefail
for f in inputs/item*.txt; do
 value=$(/usr/bin/cksum "$f" </dev/null)
 printf "%s\n" "$value"
done
