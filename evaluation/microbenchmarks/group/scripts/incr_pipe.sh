#!/bin/bash

TOP=$(git rev-parse --show-toplevel)
PROGRAM="${TOP}/target/release/incr"

$PROGRAM cat "$IN" | \
$PROGRAM sed '' | \
$PROGRAM awk 1 | \
$PROGRAM grep '' | \
$PROGRAM tail -n +1 | \
$PROGRAM tee | \
$PROGRAM cut -b 1- | \
$PROGRAM sed -n p | \
$PROGRAM awk '{print $0}' | \
$PROGRAM paste - | \
$PROGRAM grep '^' | \
$PROGRAM awk '//' | \
$PROGRAM grep '$' | \
$PROGRAM sed 's/^//'