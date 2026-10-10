#!/usr/bin/env bash
source "$DEMO/lib.sh"
# A stream is journaled with tee. A consumer verifies the journal before acking.
: > journal
{
    echo 'record 42'
    until [[ -e accepted ]]; do sleep .02; done
} | memo tee journal | while IFS= read -r record; do
    echo "stream: $record"
    # tee may write stdout first, so wait for the journal instead of racing it.
    until grep -qx "$record" journal; do sleep .02; done
    echo 'journal: verified'
    touch accepted
done
