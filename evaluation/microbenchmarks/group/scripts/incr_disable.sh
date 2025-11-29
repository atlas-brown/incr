#!/bin/bash

TOP=$(git rev-parse --show-toplevel)
PROGRAM="${TOP}/target/release/incr"

SCRIPT=$(cat <<'EOF'
cat - | \
sed '' | \
awk 1 | \
grep -a '' | \
tail -n +1 | \
tee | \
cut -b 1- | \
sed -n p | \
awk '{print $0}' | \
paste - | \
grep -a '^' | \
awk '//' | \
grep -a '$' | \
sed 's/^//' | \
cat | \
dd status=none | \
sed -e '' | \
sed ';' | \
sed 's/$//' | \
sed -n '1,$p' | \
sed 'h;g' | \
awk '{print}' | \
awk 'BEGIN{} {print}' | \
awk '{if(1) print}' | \
awk '{a=$0; print a}' | \
grep -a -e '' | \
grep -aE '.*' | \
grep -aE '^' | \
grep -aF '' | \
sh -c 'cat'
EOF
)

$PROGRAM cat "$IN" | $PROGRAM bash -c "$SCRIPT" | ./scripts/expensive.py