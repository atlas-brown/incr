#!/usr/bin/env bash
source "$DEMO/lib.sh"
# A producer publishes a named stream; its caller opens the advertised endpoint.
memo bash -eu -c '
    mkfifo events.fifo
    echo events.fifo
    printf "event: uploaded\n" > events.fifo
' | while IFS= read -r endpoint; do
    if [[ ! -p $endpoint ]]; then echo 'fifo: unavailable'; exit 1; fi
    cat "$endpoint"
done
