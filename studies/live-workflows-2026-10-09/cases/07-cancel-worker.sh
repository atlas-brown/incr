#!/usr/bin/env bash
source "$DEMO/lib.sh"
# A controller cancels a worker before releasing its next task.
: > next-task
memo bash -eu -c '
    echo running > job.state
    echo ready
    until grep -q task next-task; do sleep .02; done
    if [[ $(cat job.state) == cancelled ]]; then
        echo cancelled
    else
        echo "processed: expensive-task"
    fi
' | {
    read -r ready; [[ $ready == ready ]]
    echo cancelled > job.state
    echo task > next-task
    cat
}
