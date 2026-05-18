#!/bin/bash

mkdir -p $2
# Inlined the original `pure_func` shell function so incr (which execs commands
# directly rather than via bash) can run this script without modification.
# Each pipeline appends to $logname rather than using `{ ... } > $logname`
# because incr's script rewriter only attaches the group redirect to the last
# statement inside the brace group.
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
