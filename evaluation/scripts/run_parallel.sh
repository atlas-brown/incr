#!/bin/bash
# Run EASY benchmarks (+ optional dpt) in parallel (one process per benchmark).
# Heuristic speedup only; sequential evaluation/benchmarks/run_all.sh is canonical.
#
# Usage: bash run_parallel.sh [--skip-dpt] [--min|--small] [--run-mode both|all|...]
# Run from incr/: bash evaluation/scripts/run_parallel.sh
# Logs: evaluation/parallel_logs/<benchmark>.log

EVAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INCR_ROOT="$(cd "$EVAL_DIR/.." && pwd)"
cd "$EVAL_DIR" || exit 1

LOG_DIR="$EVAL_DIR/parallel_logs"
mkdir -p "$LOG_DIR"

SIZE=min
RUN_MODE=both
SKIP_DPT=false
for arg in "$@"; do
    [[ "$arg" == "--skip-dpt" ]] && SKIP_DPT=true
    [[ "$arg" == "--min" ]] && SIZE=min
    [[ "$arg" == "--small" ]] && SIZE=small
    [[ "$arg" == --run-mode=* ]] && RUN_MODE="${arg#--run-mode=}"
done

# word-freq first: can be sensitive to resource contention
ALL_BENCHMARKS=(word-freq beginner bio covid file-mod nginx-analysis nlp-uppercase nlp-ngrams poet spell unixfun weather)
if [[ "$SKIP_DPT" != "true" ]]; then
    ALL_BENCHMARKS+=(dpt)
fi

cleanup_on_exit() {
    echo ""
    echo "Cleaning up (parallel run)..."
    "$EVAL_DIR/scripts/restore_benchmark_scripts.sh" 2>/dev/null || true
    for bench in "${ALL_BENCHMARKS[@]}"; do
        sudo rm -rf "$EVAL_DIR/benchmarks/$bench/cache" "$EVAL_DIR/benchmarks/$bench/outputs" 2>/dev/null || true
    done
    rm -rf /tmp/sort* /tmp/tmp* /tmp/cache* 2>/dev/null || true
}
trap cleanup_on_exit EXIT INT TERM

"$EVAL_DIR/scripts/restore_benchmark_scripts.sh" 2>/dev/null || true

echo "Cleaning benchmark dirs..."
for bench in "${ALL_BENCHMARKS[@]}"; do
    sudo bash "$EVAL_DIR/benchmarks/$bench/clean.sh" 2>/dev/null || true
    rm -rf "$EVAL_DIR/benchmarks/$bench/cache" "$EVAL_DIR/benchmarks/$bench/outputs"
done

run_one() {
    local bench=$1
    local log="$LOG_DIR/${bench}.log"
    echo "=== $bench ($SIZE, $RUN_MODE) ===" >"$log"
    (
        cd "$INCR_ROOT" || exit 1
        exec bash evaluation/benchmarks/run_all.sh --only "$bench" --mode easy --size "$SIZE" --run-mode "$RUN_MODE" --skip-setup
    ) >>"$log" 2>&1
    echo "=== $bench DONE ===" >>"$log"
}

BATCH_SIZE=3
echo "Starting ${#ALL_BENCHMARKS[@]} benchmarks in batches of $BATCH_SIZE (parallel)..."
for ((i=0; i<${#ALL_BENCHMARKS[@]}; i+=BATCH_SIZE)); do
    for ((j=i; j<i+BATCH_SIZE && j<${#ALL_BENCHMARKS[@]}; j++)); do
        run_one "${ALL_BENCHMARKS[$j]}" &
    done
    wait
    for ((j=i; j<i+BATCH_SIZE && j<${#ALL_BENCHMARKS[@]}; j++)); do
        b="${ALL_BENCHMARKS[$j]}"
        rm -rf "$EVAL_DIR/benchmarks/$b/cache" "$EVAL_DIR/benchmarks/$b/outputs" 2>/dev/null || true
    done
    rm -rf /tmp/sort* /tmp/tmp* 2>/dev/null || true
done
echo "All parallel benchmark jobs finished. Logs: $LOG_DIR"
