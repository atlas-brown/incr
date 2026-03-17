#!/bin/bash
# Run all benchmarks in parallel (each benchmark runs default then observe).
# Usage: bash run_parallel.sh
# Run from incr/: bash evaluation/run_parallel.sh
# Monitor: bash evaluation/monitor_benchmarks.sh

cd "$(dirname "$0")" || exit 1
BENCH_DIR="$(pwd)/benchmarks"
LOG_DIR="$(pwd)/parallel_logs"
RESULTS_DIR="$(pwd)/run_results_parallel"
mkdir -p "$LOG_DIR" "$RESULTS_DIR/default" "$RESULTS_DIR/observe"

# Same as run.sh (skip image-annotation, file-mod)
BENCHMARKS=(beginner bio covid dpt nginx-analysis nlp-uppercase nlp-ngrams poet spell unixfun weather word-freq)
SIZES=(small small small small small small small small small small small)

run_one_benchmark() {
    local i=$1
    local bench="${BENCHMARKS[$i]}"
    local size="${SIZES[$i]}"
    local log_default="$LOG_DIR/${bench}_default.log"
    local log_observe="$LOG_DIR/${bench}_observe.log"

    # Default mode
    {
        echo "=== $bench DEFAULT $(date) ==="
        sudo bash "$BENCH_DIR/$bench/clean.sh" 2>/dev/null || true
        rm -rf "$BENCH_DIR/$bench/cache" "$BENCH_DIR/$bench/outputs"
        mkdir -p "$BENCH_DIR/$bench/outputs"
        export INCR_OBSERVE=0
        bash "$BENCH_DIR/$bench/execute.sh" "--$size" "--incr-only"
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
        bash "$BENCH_DIR/$bench/execute.sh" "--$size" "--incr-only"
        cp "$BENCH_DIR/$bench/outputs/timing.csv" "$RESULTS_DIR/observe/${bench}-time.csv" 2>/dev/null || true
        if [[ -d "$BENCH_DIR/$bench/cache" ]]; then
            du -sb "$BENCH_DIR/$bench/cache" > "$RESULTS_DIR/observe/${bench}-size.txt" 2>/dev/null || true
        fi
        echo "=== $bench OBSERVE DONE $(date) ==="
    } > "$log_observe" 2>&1
}

# Clean everything first
echo "Cleaning all benchmarks..."
for bench in "${BENCHMARKS[@]}"; do
    sudo bash "$BENCH_DIR/$bench/clean.sh" 2>/dev/null || true
    rm -rf "$BENCH_DIR/$bench/cache" "$BENCH_DIR/$bench/outputs"
done
rm -rf /tmp/sort* /tmp/tmp* 2>/dev/null || true

echo "Starting ${#BENCHMARKS[@]} benchmarks in parallel..."
for i in "${!BENCHMARKS[@]}"; do
    run_one_benchmark "$i" &
done
wait
echo "All benchmarks finished."
