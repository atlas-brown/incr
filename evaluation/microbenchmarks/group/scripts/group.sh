#!/bin/bash

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

cat "$IN" | bash -c "$SCRIPT"