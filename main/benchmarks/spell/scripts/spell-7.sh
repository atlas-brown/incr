#!/bin/bash
# Calculate mispelled words in an input

dict=/usr/share/dict/words
dict_sorted=$(mktemp -p "${TMPDIR:-/tmp}" spell_dict.XXXXXX)
trap 'rm -f "$dict_sorted"' EXIT
LC_ALL=C sort -u "$dict" > "$dict_sorted" || exit 1

find $IN -type f -name '*.txt' -exec cat {} + |
    sed 's/[^[:print:]]//g' |      # remove non-printing characters
    col -bx            |           # remove backspaces / linefeeds
    tr -cs A-Za-z '\n' |
    tr A-Z a-z |                   # map upper to lower case
    tr -d '[:punct:]' |            # remove punctuation
    LC_ALL=C sort |
    uniq |                         # remove duplicate words
    LC_ALL=C comm -23 - "$dict_sorted"
