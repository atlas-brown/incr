#!/usr/bin/env bash
set -e
set -o pipefail
for f in inputs/item*.txt; do
 /usr/bin/grep alpha "$f" </dev/null | /usr/bin/cut -d " " -f 2 | /usr/bin/uniq -c > "outputs/${f##*/}.summary"
done
/usr/bin/cat outputs/*.summary </dev/null
