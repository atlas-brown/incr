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

# Restore all benchmark scripts via git (if in repo).
# Incr overwrites scripts in place; if interrupted, scripts can be left empty or instrumented.
if [[ -d "$INCR_ROOT/.git" ]]; then
    # Restore scripts with incr instrumentation (legacy strace path or current insert.py output)
    grep -rlE "target/release/incr|incr_script_" "$BENCH_DIR" 2>/dev/null | grep -E '\.sh$' | while read -r f; do
        rel="${f#$INCR_ROOT/}"
        (cd "$INCR_ROOT" && git checkout -- "$rel" 2>/dev/null) && echo "Restored (incr): $rel"
    done
    # Restore empty or otherwise broken scripts (e.g. word-freq wf.sh, top-n.sh)
    find "$BENCH_DIR" -name "*.sh" -type f 2>/dev/null | while read f; do
        [[ -s "$f" ]] && continue
        rel="${f#$INCR_ROOT/}"
        (cd "$INCR_ROOT" && git checkout -- "$rel" 2>/dev/null) && echo "Restored (empty): $rel"
    done
fi
