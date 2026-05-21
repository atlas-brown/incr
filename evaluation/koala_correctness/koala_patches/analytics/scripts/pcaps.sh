#!/bin/bash

mkdir -p $2
# Inlined the original `pure_func` shell function. The function call itself
# works fine under incr — incr detects exported (`export -f`) functions via
# the `BASH_FUNC_pure_func%%` env var and dispatches them through `bash -c`.
# The real bug is that the function body's first wrapped command (`mktemp`)
# drains the function's piped stdin before its `tee` can read it. Inlining
# (and replacing piped stdin with `cp "$item" "$tempfile"`) lets every later
# stage read from the file rather than a piped stdin.
#
# Each pipeline appends to $logname rather than using `{ ... } > $logname`
# because incr's script rewriter only attaches the group redirect to the last
# statement inside the brace group, so the first N-1 statements' stdout would
# otherwise be lost.
for item in $1/*; do
    logname=$2/$(basename $item).log
    tempfile=$(mktemp)
    cp "$item" "$tempfile"
    : > "$logname"
    tcpdump -nn -r "$tempfile" -A 'port 53' 2>/dev/null | sort | uniq | grep -Ev '(com|net|org|gov|mil|arpa)' 2>/dev/null >> "$logname"
    tcpdump -nn -r "$tempfile" -s 0 -v -n -l 2>/dev/null | grep -E -i "POST /|GET /|Host:" 2>/dev/null >> "$logname"
    tcpdump -nn -r "$tempfile" -s 0 -A -n -l 2>/dev/null | grep -E -i "POST /|pwd=|passwd=|password=|Host:" 2>/dev/null >> "$logname"
    tcpdump -nn -r "$tempfile" -s 0 -A -n -l 'port 23' 2>/dev/null | grep -E -i "login:|password:" 2>/dev/null >> "$logname"
    rm -f "$tempfile"
done
