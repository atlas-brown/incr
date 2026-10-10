#!/usr/bin/env bash
source "$DEMO/lib.sh"
# Stream batch filenames; each receipt lets the exporter reuse its batch file.
echo empty > batch.csv
: > receipt
memo bash -eu -c '''
    for batch in north south west; do
        printf "%s,10\n" "$batch" > batch.csv
        echo batch.csv
        until grep -qx "$batch" receipt; do sleep .02; done
    done
''' | for batch in north south west; do
    IFS= read -r file
    cat "$file"
    echo "$batch" > receipt
done
