#!/usr/bin/env bash
source "$DEMO/lib.sh"
# A streaming logger stays alive while its caller appends a second audit record.
: > audit.log
{
    echo worker
    until [[ -e logged ]]; do sleep .02; done
} | memo bash -eu -c '''
    while IFS= read -r record; do
        echo "$record" >> audit.log
        echo logged
    done
''' | while IFS= read -r confirmation; do
    [[ $confirmation == logged ]]
    echo peer >> audit.log
    touch logged
done
cat audit.log
