#!/bin/bash

TOP=$(git rev-parse --show-toplevel)
PROGRAM="${TOP}/target/release/incr"
PROGRAM=""

$PROGRAM cat "$IN" | \
$PROGRAM tr 'a-zA-Z' 'a-zA-Z' | \
$PROGRAM sed '' | \
$PROGRAM awk '{for(i=0;i<100;i++); print $0}' | \
$PROGRAM grep -a "" | \
$PROGRAM cat | \
$PROGRAM tail -n +1 | \
$PROGRAM cut -b 1- | \
$PROGRAM sed -e 's/^//' | \
$PROGRAM awk '1' | \
$PROGRAM tr '0-9' '0-9' | \
$PROGRAM cat | \
$PROGRAM grep -a -E "" | \
$PROGRAM sed -n 'p' | \
$PROGRAM awk '//' | \
$PROGRAM tail -n +1 | \
$PROGRAM cut -b 1- | \
$PROGRAM sed -e 's/$//' | \
$PROGRAM cat | \
$PROGRAM awk '{if(1)print}'