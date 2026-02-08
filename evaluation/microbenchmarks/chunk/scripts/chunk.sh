#!/bin/bash

TOP=$(git rev-parse --show-toplevel)
PROGRAM="${TOP}/target/release/incr"
# PROGRAM=""

$PROGRAM cat "$IN" | \
$PROGRAM sed -E 's/(.)/\1/g' | \
$PROGRAM awk '{gsub(/./, "&"); print}' | \
$PROGRAM sed -e 's/^/X/; s/^X//' | \
$PROGRAM grep -a -E "^.*$"