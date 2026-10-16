#!/usr/bin/env bash
set -e
set -o pipefail
for f in inputs/item*.txt; do
 IFS= read -r version < "$f"
 /usr/bin/true "$f" "$version" </dev/null
done
printf "completed\n"
