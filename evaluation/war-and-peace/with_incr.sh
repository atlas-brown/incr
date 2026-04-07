#!/bin/bash
TOP=$(git rev-parse --show-toplevel)
INPUT="$TOP/evaluation/war-and-peace/book-large.txt"
INCR="$TOP/target/release/incr"
TRY="$TOP/src/scripts/try.sh"
CACHE="$TOP/cache"

if [ -d "$CACHE" ] && [ -n "$(ls -A "$CACHE" 2>/dev/null)" ]; then
    echo "Cache found at $CACHE, replaying cached results where possible." >&2
else
    echo "No cache found, cold run. Results will be cached for next run." >&2
fi

start=$(date +%s%3N)
"$INCR" --try "$TRY" --cache "$CACHE" cat "$INPUT" \
    | "$INCR" --try "$TRY" --cache "$CACHE" tr "[:upper:]" "[:lower:]" \
    | "$INCR" --try "$TRY" --cache "$CACHE" tr -s "[:space:]" "\n" \
    | "$INCR" --try "$TRY" --cache "$CACHE" sort \
    | "$INCR" --try "$TRY" --cache "$CACHE" uniq -c \
    | "$INCR" --try "$TRY" --cache "$CACHE" sort -nr
elapsed=$(( $(date +%s%3N) - start ))
echo "Elapsed: ${elapsed}ms" >&2
