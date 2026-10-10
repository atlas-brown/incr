#!/usr/bin/env bash
source "$DEMO/lib.sh"
# A disk-backed queue streams filenames, with deletion providing backpressure.
mkdir spool
memo bash -eu -c '
    printf "invoice 42\n" > spool/job
    echo spool/job
    until [[ ! -e spool/job ]]; do sleep .02; done
' | while IFS= read -r file; do
    if [[ ! -f $file ]]; then echo 'spool: unavailable'; exit 1; fi
    cat "$file"
    rm "$file"
done
