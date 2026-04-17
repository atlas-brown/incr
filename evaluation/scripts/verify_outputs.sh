#!/bin/bash
# Verify incr (try+strace) and incr-observe produce identical stdout for each benchmark script.
# Run from incr/: bash evaluation/scripts/verify_outputs.sh [--min|--small] [--no-cleanup] [--run]
#
# By default, compares existing outputs under benchmarks/*/outputs/<size>/*.incr.out vs *.incr-observe.out
# if present. With --run, first runs: evaluation/benchmarks/run_all.sh --mode easy --run-mode all
#
# Cleans verify_outputs dir and /tmp artifacts on exit unless --no-cleanup.

EVAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INCR_ROOT="$(cd "$EVAL_DIR/.." && pwd)"
cd "$EVAL_DIR" || exit 1
BENCH_DIR="$EVAL_DIR/benchmarks"
VERIFY_DIR="$EVAL_DIR/verify_outputs"
SIZE_NAME="min"
NO_CLEANUP=false
DO_RUN=false
for arg in "$@"; do
    [[ "$arg" == "--min" ]] && SIZE_NAME="min"
    [[ "$arg" == "--small" ]] && SIZE_NAME="small"
    [[ "$arg" == "--no-cleanup" ]] && NO_CLEANUP=true
    [[ "$arg" == "--run" ]] && DO_RUN=true
done

mkdir -p "$VERIFY_DIR"

cleanup() {
    [[ "$NO_CLEANUP" == "true" ]] && return
    echo ""
    echo "Cleaning up artifacts..."
    "$EVAL_DIR/scripts/restore_benchmark_scripts.sh" 2>/dev/null || true
    rm -rf "$VERIFY_DIR"
    rm -rf /tmp/sort* /tmp/tmp* /tmp/cache* /tmp/incr_bench* 2>/dev/null || true
    echo "Done."
}
trap cleanup EXIT INT TERM

if [[ "$DO_RUN" == "true" ]]; then
    echo "Running full suite (bash + incr + incr-observe)..."
    bash "$INCR_ROOT/evaluation/benchmarks/run_all.sh" --mode easy --size "$SIZE_NAME" --run-mode all --skip-setup || true
fi

OUT_SUB="outputs/$SIZE_NAME"
fail=0
BENCHMARKS=(beginner bio covid file-mod nginx-analysis nlp-ngrams nlp-uppercase poet spell unixfun weather word-freq)

echo "=============================================="
echo "Verifying incr vs incr-observe stdout ($OUT_SUB)"
echo "=============================================="

for bench in "${BENCHMARKS[@]}"; do
    od="$BENCH_DIR/$bench/$OUT_SUB"
    if [[ ! -d "$od" ]]; then
        echo ">>> $bench: skip (no $OUT_SUB)"
        continue
    fi
    echo ""
    echo ">>> $bench"
    bench_fail=0
    shopt -s nullglob
    for f in "$od"/*.incr.out; do
        [[ -f "$f" ]] || continue
        base="${f%.incr.out}"
        obs="${base}.incr-observe.out"
        if [[ ! -f "$obs" ]]; then
            echo "  MISSING incr-observe: $(basename "$obs")"
            bench_fail=1
            continue
        fi
        if ! diff -q "$f" "$obs" >/dev/null 2>&1; then
            echo "  DIFF: $(basename "$f") vs $(basename "$obs")"
            diff "$f" "$obs" | head -15
            bench_fail=1
        fi
    done
    shopt -u nullglob

    if [[ "$bench_fail" -eq 0 ]]; then
        echo "  OK"
    else
        echo "  FAIL"
        fail=1
    fi
done

echo ""
echo "=============================================="
if [[ "$fail" -eq 0 ]]; then
    echo "All incr vs incr-observe stdout outputs match."
else
    echo "Some outputs differ or were missing."
    exit 1
fi
