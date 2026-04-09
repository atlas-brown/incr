#!/bin/bash

cat "$INPUT" \
    | tr "[:upper:]" "[:lower:]" \
    | tr -s "[:space:]" "\n" \
    | sort \
    | uniq -c \
    | sort -nr