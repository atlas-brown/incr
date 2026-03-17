#!/bin/bash
# Restore benchmark scripts if left in incr-instrumented state (e.g. after kill/Ctrl+C).
# Run from incr/: bash evaluation/scripts/restore_benchmark_scripts.sh
# Also removes stray incr_script_* files.

EVAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BENCH_DIR="$EVAL_DIR/benchmarks"
INCR_ROOT="$(cd "$EVAL_DIR/.." && pwd)"

# Remove stray incr_script_* temp files
find "$BENCH_DIR" -name "incr_script_*" -type f 2>/dev/null | while read f; do
    rm -f "$f"
    echo "Removed: $f"
done

# Restore scripts with incr instrumentation via git (if in repo)
if [[ -d "$INCR_ROOT/.git" ]]; then
    grep -rl "target/release/incr --try" "$BENCH_DIR" 2>/dev/null | grep -E '\.sh$' | while read f; do
        rel="${f#$INCR_ROOT/}"
        (cd "$INCR_ROOT" && git checkout -- "$rel" 2>/dev/null) && echo "Restored: $rel"
    done
fi
