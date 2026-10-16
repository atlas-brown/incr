#!/usr/bin/env bash
set -e
set -o pipefail
for f in inputs/item*.txt; do
 /usr/bin/tr a-z A-Z < "$f" > "outputs/leaf-${f##*/}"
done
for digit in 0 1 2 3 4 5 6 7 8 9; do
 set -- outputs/leaf-*"$digit".txt
 if [ -e "$1" ]; then
 /usr/bin/cat outputs/leaf-*"$digit".txt </dev/null | /usr/bin/cksum > "outputs/group-$digit"
 fi
done
/usr/bin/cat outputs/group-* </dev/null
