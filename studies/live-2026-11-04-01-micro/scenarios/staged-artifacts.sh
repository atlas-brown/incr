#!/usr/bin/env bash
set -e
set -o pipefail
for f in inputs/item*.txt; do
 name=${f##*/}
 /usr/bin/cp "$f" "outputs/$name.stage" </dev/null
 /usr/bin/tr a-z A-Z < "outputs/$name.stage" > "outputs/$name.ready"
 /usr/bin/mv "outputs/$name.ready" "outputs/$name.final" </dev/null
 /usr/bin/rm "outputs/$name.stage" </dev/null
done
