#!/usr/bin/env bash
source "$DEMO/lib.sh"
# Noclobber implements an exclusive create: only one worker may claim the job.
: > finish
memo bash -eu -c '
    set -o noclobber
    echo first > job.claim
    echo claimed
    until grep -q finish finish; do sleep .02; done
' | {
    read -r claimed; [[ $claimed == claimed ]]
    if (set -o noclobber; echo second > job.claim) 2>/dev/null; then
        echo 'claim: duplicate owner'
    else
        echo 'claim: already owned'
    fi
    echo finish > finish
}
