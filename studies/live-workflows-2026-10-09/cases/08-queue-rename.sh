#!/usr/bin/env bash
source "$DEMO/lib.sh"
# Workers claim a queued file by atomically moving it out of the inbox.
mkdir inbox working
echo job > inbox/job
: > finish
memo bash -eu -c '
    mv inbox/job working/first
    echo claimed
    until grep -q finish finish; do sleep .02; done
' | {
    read -r claimed; [[ $claimed == claimed ]]
    if mv inbox/job working/second 2>/dev/null; then
        echo 'queue: duplicate claim'
    else
        echo 'queue: already claimed'
    fi
    echo finish > finish
}
