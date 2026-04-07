#!/bin/bash
TOP=$(git rev-parse --show-toplevel)
INPUT="$TOP/evaluation/war-and-peace/book-large.txt"

start=$(date +%s%3N)
cat "$INPUT" \
    | tr "[:upper:]" "[:lower:]" \
    | tr -s "[:space:]" "\n" \
    | sort \
    | uniq -c \
    | sort -nr
elapsed=$(( $(date +%s%3N) - start ))
echo "Elapsed: ${elapsed}ms" >&2
