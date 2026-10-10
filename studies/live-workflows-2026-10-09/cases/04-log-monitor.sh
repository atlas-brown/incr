#!/usr/bin/env bash
source "$DEMO/lib.sh"
# A controller watches a running job's log and asks it to stop on an error.
: > build.log
memo bash -eu -c '
    echo "worker: started"
    echo "ERROR: missing source" >> build.log
    until [[ -e stop ]]; do sleep .02; done
' & worker=$!
until grep -q ERROR build.log; do sleep .02; done
echo 'monitor: stopping build'
touch stop
wait "$worker"
