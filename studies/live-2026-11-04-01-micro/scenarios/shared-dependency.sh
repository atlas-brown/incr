#!/usr/bin/env bash
set -e
set -o pipefail
for f in inputs/item*.txt; do
 /usr/bin/cat config.txt "$f" </dev/null | /usr/bin/cksum
done
