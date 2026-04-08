#!/bin/bash
# run.sh: run the covid benchmark.
# Usage: run.sh [--mode bash|incr|both] [--size min|small|full] [--scripts a.sh,b.sh]
cd "$(dirname "$0")" || exit 1

TOP=$(git rev-parse --show-toplevel)
BENCHMARK_DIR="$TOP/evaluation/benchmarks/covid"
SCRIPT_DIR="$BENCHMARK_DIR/scripts"
source "$TOP/evaluation/benchmarks/run_lib.sh"

parse_benchmark_run_sh_args "$@"

echo "[run] covid: mode=$RUN_MODE size=$RUN_SIZE"
OUTPUT_DIR="$BENCHMARK_DIR/outputs/$RUN_SIZE"

restore_instrumented_scripts "$SCRIPT_DIR"
cleanup_overlay_mounts
cleanup_tmp_artifacts
sudo bash "$BENCHMARK_DIR/clean.sh" 2>/dev/null || true

cleanup() {
    restore_instrumented_scripts "$SCRIPT_DIR"
    cleanup_tmp_artifacts
}
trap cleanup EXIT INT TERM

case "$RUN_SIZE" in
    min)   export INPUT="$BENCHMARK_DIR/inputs/in_min.csv" ;;
    small) export INPUT="$BENCHMARK_DIR/inputs/in_small.csv" ;;
    full)  export INPUT="$BENCHMARK_DIR/inputs/in.csv" ;;
esac
TIME_FILE="$OUTPUT_DIR/timing.csv"

DEFAULT_SCRIPTS=(1.sh 2.sh 3.sh 4.sh 5.sh)
finalize_benchmark_scripts "$SCRIPT_DIR" "${DEFAULT_SCRIPTS[@]}"
run_benchmark_scripts "${SCRIPTS[@]}"
echo "[run] covid: done. Results: $TIME_FILE"
