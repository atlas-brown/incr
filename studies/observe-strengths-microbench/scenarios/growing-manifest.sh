#!/usr/bin/env bash
set -e
set -o pipefail
while IFS= read -r f; do
 /usr/bin/cksum "$f" </dev/null
done < manifest.txt
