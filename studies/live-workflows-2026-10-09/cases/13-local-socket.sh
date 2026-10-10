#!/usr/bin/env bash
source "$DEMO/lib.sh"
# A one-request local helper exposes a Unix socket to its caller.
echo 'reply: healthy' > reply
memo bash -eu -c '
    nc -N -l -U helper.sock < reply > /dev/null & server=$!
    until [[ -S helper.sock ]]; do sleep .02; done
    echo listening
    wait "$server"
' | {
    read -r listening; [[ $listening == listening ]]
    if [[ ! -S helper.sock ]]; then
        echo 'socket: unavailable'
    else
        # bind() publishes the path just before listen(); allow that startup window.
        until nc -N -U helper.sock < /dev/null 2>/dev/null; do sleep .02; done
    fi
}
