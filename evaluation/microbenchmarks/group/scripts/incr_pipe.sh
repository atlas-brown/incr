#!/bin/bash

TOP=$(git rev-parse --show-toplevel)
PROGRAM="${TOP}/target/release/incr"

$PROGRAM cat "$IN" | \
$PROGRAM sed '' | \
$PROGRAM awk 1 | \
$PROGRAM grep -a '' | \
$PROGRAM tail -n +1 | \
$PROGRAM tee | \
$PROGRAM cut -b 1- | \
$PROGRAM sed -n p | \
$PROGRAM awk '{print $0}' | \
$PROGRAM paste - | \
$PROGRAM grep -a '^' | \
$PROGRAM awk '//' | \
$PROGRAM grep -a '$' | \
$PROGRAM sed 's/^//' | \
$PROGRAM cat | \
$PROGRAM dd status=none | \
$PROGRAM sed -e '' | \
$PROGRAM sed ';' | \
$PROGRAM sed 's/$//' | \
$PROGRAM sed -n '1,$p' | \
$PROGRAM sed 'h;g' | \
$PROGRAM awk '{print}' | \
$PROGRAM awk 'BEGIN{} {print}' | \
$PROGRAM awk '{if(1) print}' | \
$PROGRAM awk '{a=$0; print a}' | \
$PROGRAM grep -a -e '' | \
$PROGRAM grep -aE '.*' | \
$PROGRAM grep -aE '^' | \
$PROGRAM grep -aF '' | \
$PROGRAM sh -c 'cat'