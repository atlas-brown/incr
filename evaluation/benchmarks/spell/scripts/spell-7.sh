#!/bin/bash
# Calculate mispelled words in an input

# comm requires both operands sorted in the same locale. The installed word
# list is not necessarily sorted that way, and input words are lowercased.
dict=$(mktemp) || exit 1
trap 'rm -f "$dict"' EXIT
tr '[:upper:]' '[:lower:]' < /usr/share/dict/words | sort -u > "$dict"

find $IN -type f -name '*.txt' -exec cat {} + |
    sed 's/[^[:print:]]//g' |      # remove non-printing characters
    col -bx            |           # remove backspaces / linefeeds
    tr -cs A-Za-z '\n' |
    tr A-Z a-z |                   # map upper to lower case
    tr -d '[:punct:]' |            # remove punctuation
    sort |                         # put words in alphabetical order
    uniq |                         # remove duplicate words
    comm -23 - "$dict"               # report words not in dictionary
