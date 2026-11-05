#!/usr/bin/env bash
set -e
set -o pipefail
read -r parameters < parameters.txt
for f in inputs/item*.txt; do
 for p in $parameters; do
 /usr/bin/grep -c "token$p" "$f" </dev/null || [ "$?" = 1 ]
 done
done
