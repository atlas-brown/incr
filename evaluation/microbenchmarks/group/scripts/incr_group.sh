#!/bin/bash

TOP=$(git rev-parse --show-toplevel)
PROGRAM="${TOP}/target/release/incr"

SCRIPT=$(cat <<'EOF'
sed '' | \
awk 1 | \
grep '' | \
tail -n +1 | \
tee | \
cut -b 1- | \
sed -n p | \
awk '{print $0}' | \
paste - | \
grep '^' | \
awk '//' | \
grep '$' | \
sed 's/^//'
EOF
)

$PROGRAM cat "$IN" | $PROGRAM bash -c "$SCRIPT"