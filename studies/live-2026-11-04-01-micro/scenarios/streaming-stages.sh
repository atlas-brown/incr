#!/usr/bin/env bash
set -e
set -o pipefail
for f in inputs/item*.txt; do
 /usr/bin/cat "$f" </dev/null | /usr/bin/tr a-z A-Z | /usr/bin/cksum
done
