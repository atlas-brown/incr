#!/usr/bin/env bash
set -e
set -o pipefail
for d in inputs/dir*; do
 (cd "$d"; /usr/bin/printf "%s\n" ./* </dev/null)
done
