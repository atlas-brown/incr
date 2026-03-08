#!/bin/bash
# Run incr + observe integration tests.
# Usage: bash run.sh [filter]
# Run from incr/: bash agent/tests/run.sh

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INCR_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

[ -x "$INCR_ROOT/target/release/incr" ] || { echo "Build incr: cargo build --release"; exit 1; }
[ -x "$INCR_ROOT/../observe/target/release/observe" ] || { echo "Build observe: cd observe && cargo build --release"; exit 1; }

filter="${1:-}"
PASSED=0
FAILED=0

for t in "$SCRIPT_DIR"/t_incr_*.sh; do
    [ -f "$t" ] || continue
    name=$(basename "$t" .sh)
    [ -n "$filter" ] && [[ "$name" != *"$filter"* ]] && continue
    echo "  $name"
    if (cd "$INCR_ROOT" && bash "$t" 2>&1); then
        PASSED=$((PASSED + 1))
    else
        FAILED=$((FAILED + 1))
        echo "    FAILED"
    fi
done

echo ""
echo "══════════════════════════════════════════"
echo "  $PASSED passed, $FAILED failed"
echo "══════════════════════════════════════════"
[ "$FAILED" -eq 0 ]
