#!/bin/bash 
#tag: count_trigrams.sh
# set -e

IN=${IN:-$SUITE_DIR/inputs/pg}
OUT=${1:-$SUITE_DIR/outputs/4_3b/}
ENTRIES=${ENTRIES:-1000}
mkdir -p "$OUT"

# Inlined the original `pure_func` shell function. The function call itself
# works fine under incr — incr detects exported (`export -f`) functions via the
# `BASH_FUNC_pure_func%%` env var and dispatches them through `bash -c`. The
# real bug is that the function body's first wrapped command (`mktemp`) drains
# the function's piped stdin before its `cat > file` can read it. Inlining
# restructures the pipeline so the stdin-consumer (`cat | tr | grep`) writes
# to a file before any other wrapped command runs.
for input in $(ls ${IN} | head -n ${ENTRIES} | xargs -I arg1 basename arg1)
do
    TEMPDIR=$(mktemp -d)
    cat $IN/$input | tr -c 'A-Za-z' '[\n*]' | grep -v "^\s*$" > ${TEMPDIR}/${input}.words
    tail +2 ${TEMPDIR}/${input}.words > ${TEMPDIR}/${input}.nextwords
    tail +2 ${TEMPDIR}/${input}.words > ${TEMPDIR}/${input}.nextwords2
    paste ${TEMPDIR}/${input}.words ${TEMPDIR}/${input}.nextwords ${TEMPDIR}/${input}.nextwords2 \
        | sort | uniq -c > ${OUT}/${input}.trigrams
    rm -rf ${TEMPDIR}
done

echo 'done';
# rm -rf ${OUT}
