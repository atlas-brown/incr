#!/usr/bin/env bash
set -e
set -o pipefail
for f in inputs/item*.txt; do
 /usr/bin/tr a-z A-Z < "$f" > "outputs/${f##*/}"
done
