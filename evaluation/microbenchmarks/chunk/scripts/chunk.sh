#!/bin/bash
# Calculate mispelled words in an input

TOP=$(git rev-parse --show-toplevel)
PROGRAM="${TOP}/target/release/incr -a"
PROGRAM=""

dict=/usr/share/dict/words

$PROGRAM find "./inputs/pg-small" -type f -name '*.txt' -exec cat {} + |
$PROGRAM iconv -f UTF-8 -t ASCII//TRANSLIT//IGNORE//SUBSTITUTE |
$PROGRAM tr -cs A-Za-z '\n' |
$PROGRAM grep -v '[0-9]+' |
$PROGRAM grep -f "$dict" |
$PROGRAM rev |
$PROGRAM awk '{print length, $0}' |
$PROGRAM perl -pe 's/(\d+)\s(.*)/sprintf("%08d %s", $1, $2)/e' |
$PROGRAM cut -d' ' -f1-3 |
$PROGRAM awk '{print tolower($0)}' |
$PROGRAM sed -E 's/(.{1,3})/\1 /g' |
$PROGRAM awk '{for(i=1;i<=NF-1;i++) print $i FS $(i+1)}' |
$PROGRAM awk '{print $2}' |
$PROGRAM sed -E 's/(.)(.)/\2\1/g' |
$PROGRAM awk '{print $0, NF, length($0)}' |
$PROGRAM rev
