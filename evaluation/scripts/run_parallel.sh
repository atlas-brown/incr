#!/bin/bash
# Run all benchmarks in parallel (each benchmark runs default then observe).
# Usage: bash run_parallel.sh [--skip-dpt]
#   --skip-dpt  Skip dpt (longest benchmark, ~10+ min)
# Run from incr/: bash evaluation/scripts/run_parallel.sh
# Monitor: bash evaluation/scripts/monitor_benchmarks.sh

EVAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$EVAL_DIR" || exit 1
BENCH_DIR="$EVAL_DIR/benchmarks"
LOG_DIR="$EVAL_DIR/parallel_logs"
RESULTS_DIR="$EVAL_DIR/run_results_parallel"
mkdir -p "$LOG_DIR" "$RESULTS_DIR/default" "$RESULTS_DIR/observe"

# Same as run.sh (skip image-annotation, file-mod)
# word-freq first: it fails when run alongside many others (resource contention)
ALL_BENCHMARKS=(word-freq beginner bio covid dpt nginx-analysis nlp-uppercase nlp-ngrams poet spell unixfun weather)
ALL_SIZES=(small small small small small small small small small small small)

SKIP_DPT=false
for arg in "$@"; do
    [[ "$arg" == "--skip-dpt" ]] && SKIP_DPT=true
done

if [[ "$SKIP_DPT" == "true" ]]; then
    BENCHMARKS=()
    SIZES=()
    for i in "${!ALL_BENCHMARKS[@]}"; do
        [[ "${ALL_BENCHMARKS[$i]}" != "dpt" ]] && BENCHMARKS+=("${ALL_BENCHMARKS[$i]}") && SIZES+=("${ALL_SIZES[$i]}")
    done
    echo "Skipping dpt (--skip-dpt)"
else
    BENCHMARKS=("${ALL_BENCHMARKS[@]}")
    SIZES=("${ALL_SIZES[@]}")
fi

run_one_benchmark() {
    local i=$1
    local bench="${BENCHMARKS[$i]}"
    local size="${SIZES[$i]}"
    local log_default="$LOG_DIR/${bench}_default.log"
    local log_observe="$LOG_DIR/${bench}_observe.log"

    # Default mode (run from benchmarks/ to match sequential run.sh)
    {
        echo "=== $bench DEFAULT $(date) ==="
        sudo bash "$BENCH_DIR/$bench/clean.sh" 2>/dev/null || true
        rm -rf "$BENCH_DIR/$bench/cache" "$BENCH_DIR/$bench/outputs"
        mkdir -p "$BENCH_DIR/$bench/outputs"
        export INCR_OBSERVE=0
        (cd "$BENCH_DIR" && bash "./$bench/execute.sh" "--$size" "--incr-only")
        cp "$BENCH_DIR/$bench/outputs/timing.csv" "$RESULTS_DIR/default/${bench}-time.csv" 2>/dev/null || true
        if [[ -d "$BENCH_DIR/$bench/cache" ]]; then
            du -sb "$BENCH_DIR/$bench/cache" > "$RESULTS_DIR/default/${bench}-size.txt" 2>/dev/null || true
        fi
        echo "=== $bench DEFAULT DONE $(date) ==="
    } > "$log_default" 2>&1

    # Observe mode
    {
        echo "=== $bench OBSERVE $(date) ==="
        sudo bash "$BENCH_DIR/$bench/clean.sh" 2>/dev/null || true
        rm -rf "$BENCH_DIR/$bench/cache" "$BENCH_DIR/$bench/outputs"
        mkdir -p "$BENCH_DIR/$bench/outputs"
        export INCR_OBSERVE=1
        (cd "$BENCH_DIR" && bash "./$bench/execute.sh" "--$size" "--incr-only")
        cp "$BENCH_DIR/$bench/outputs/timing.csv" "$RESULTS_DIR/observe/${bench}-time.csv" 2>/dev/null || true
        if [[ -d "$BENCH_DIR/$bench/cache" ]]; then
            du -sb "$BENCH_DIR/$bench/cache" > "$RESULTS_DIR/observe/${bench}-size.txt" 2>/dev/null || true
        fi
        echo "=== $bench OBSERVE DONE $(date) ==="
    } > "$log_observe" 2>&1
}

# Restore any benchmark scripts left in incr mode from previous interrupted run
"$EVAL_DIR/scripts/restore_benchmark_scripts.sh" 2>/dev/null || true

# Clean everything first
echo "Cleaning all benchmarks..."
for bench in "${BENCHMARKS[@]}"; do
    sudo bash "$BENCH_DIR/$bench/clean.sh" 2>/dev/null || true
    rm -rf "$BENCH_DIR/$bench/cache" "$BENCH_DIR/$bench/outputs"
done
rm -rf /tmp/sort* /tmp/tmp* 2>/dev/null || true

cleanup_on_exit() {
    echo ""
    echo "Cleaning up (interrupted or done)..."
    "$EVAL_DIR/scripts/restore_benchmark_scripts.sh" 2>/dev/null || true
    for bench in "${BENCHMARKS[@]}"; do
        sudo rm -rf "$BENCH_DIR/$bench/cache" "$BENCH_DIR/$bench/outputs" 2>/dev/null || true
    done
    rm -rf /tmp/sort* /tmp/tmp* /tmp/cache* /tmp/incr_bench* 2>/dev/null || true
}
trap cleanup_on_exit EXIT INT TERM

# Run in batches of 3 to avoid resource contention (word-freq produces empty output when many run at once)
BATCH_SIZE=3
echo "Starting ${#BENCHMARKS[@]} benchmarks in batches of $BATCH_SIZE..."
for ((i=0; i<${#BENCHMARKS[@]}; i+=BATCH_SIZE)); do
    for ((j=i; j<i+BATCH_SIZE && j<${#BENCHMARKS[@]}; j++)); do
        run_one_benchmark "$j" &
    done
    wait
    # Clean caches and sort temp files between batches to free disk space
    for ((j=i; j<i+BATCH_SIZE && j<${#BENCHMARKS[@]}; j++)); do
        b="${BENCHMARKS[$j]}"
        rm -rf "$BENCH_DIR/$b/cache" "$BENCH_DIR/$b/outputs" 2>/dev/null || true
    done
    rm -rf /tmp/sort* /tmp/tmp* 2>/dev/null || true
done
echo "All benchmarks finished."
