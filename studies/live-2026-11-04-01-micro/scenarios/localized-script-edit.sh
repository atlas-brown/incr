#!/usr/bin/env bash
set -e
set -o pipefail
for f in inputs/item*.txt; do
 if [ "$f" = inputs/item000000.txt ]; then
 /usr/bin/tr a-z A-Z < "$f" | /usr/bin/cksum
 else
 /usr/bin/tr a-z A-Z < "$f" | /usr/bin/cksum
 fi
done
