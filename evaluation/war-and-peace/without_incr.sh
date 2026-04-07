#!/bin/bash
TOP=$(git rev-parse --show-toplevel)
INPUT="$TOP/evaluation/war-and-peace/book-large.txt"

cat "$INPUT" \
    | tr "[:upper:]" "[:lower:]" \
    | tr -s "[:space:]" "\n" \
    | sort \
    | uniq -c \
    | sort -nr
