#!/bin/bash

TOP=$(git rev-parse --show-toplevel)
PROGRAM="${TOP}/target/release/incr -a"
PROGRAM=""

cat "$IN" | \
sed -E 's/(.)/\1/g' | \
awk '{gsub(/./, "&"); print}' | \
sed -e 's/^/X/; s/^X//' | \
grep -a -E "^.*$"