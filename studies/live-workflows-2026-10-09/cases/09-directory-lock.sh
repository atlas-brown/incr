#!/usr/bin/env bash
source "$DEMO/lib.sh"
# The portable mkdir lock used by deployment and cron scripts.
: > release
memo bash -eu -c '
    mkdir deploy.lock
    trap "rmdir deploy.lock" EXIT
    echo locked
    until grep -q release release; do sleep .02; done
' | {
    read -r locked; [[ $locked == locked ]]
    if mkdir deploy.lock 2>/dev/null; then
        echo 'deploy: overlap'; rmdir deploy.lock
    else
        echo 'deploy: busy'
    fi
    echo release > release
}
