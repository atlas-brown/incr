#!/bin/bash 
# tag: sort_words_by_num_of_syllables
# set -e

IN=${IN:-$SUITE_DIR/inputs/pg}
OUT=${1:-$SUITE_DIR/outputs/8.1/}
ENTRIES=${ENTRIES:-1000}
mkdir -p "$OUT"

# Inlined the original `pure_func` shell function. The function call itself
# works fine under incr — incr detects exported (`export -f`) functions via the
# `BASH_FUNC_pure_func%%` env var and dispatches them through `bash -c`. The
# real bug is that the function body's first wrapped command (`mktemp`) drains
# the function's piped stdin before its `cat > file` can read it. Inlining
# restructures the pipeline so the stdin-consumer writes to a file before any
# other wrapped command runs.
for input in $(ls ${IN} | head -n ${ENTRIES} | xargs -I arg1 basename arg1)
do
    TEMPDIR=$(mktemp -d)
    cat $IN/$input | tr -c 'A-Za-z' '[\n*]' | grep -v "^\s*$" | sort -u > ${TEMPDIR}/${input}.words
    tr -sc '[AEIOUaeiou\012]' ' ' < ${TEMPDIR}/${input}.words | awk '{print NF}' > ${TEMPDIR}/${input}.syl
    paste ${TEMPDIR}/${input}.syl ${TEMPDIR}/${input}.words | sort -nr | sed 5q > ${OUT}/${input}.out
    rm -rf ${TEMPDIR}
done

echo 'done';
# rm -rf "$OUT"
