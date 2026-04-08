#!/bin/bash
# run.sh: run the unixfun benchmark.
# Usage: run.sh [--mode bash|incr|both] [--size min|small|full] [--scripts a.sh,b.sh]
cd "$(dirname "$0")" || exit 1

TOP=$(git rev-parse --show-toplevel)
BENCHMARK_DIR="$TOP/evaluation/benchmarks/unixfun"
SCRIPT_DIR="$BENCHMARK_DIR/scripts"
source "$TOP/evaluation/benchmarks/run_lib.sh"

parse_benchmark_run_sh_args "$@"

echo "[run] unixfun: mode=$RUN_MODE size=$RUN_SIZE"
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
    min)   export INPUT="$BENCHMARK_DIR/inputs/4.min.txt" ;;
    small) export INPUT="$BENCHMARK_DIR/inputs/4.small.txt" ;;
    full)  export INPUT="$BENCHMARK_DIR/inputs/4.full.txt" ;;
esac
TIME_FILE="$OUTPUT_DIR/timing.csv"

DEFAULT_SCRIPTS=(7.sh 8.sh 9.sh 10.sh 11.sh 12.sh)
finalize_benchmark_scripts "$SCRIPT_DIR" "${DEFAULT_SCRIPTS[@]}"
run_benchmark_scripts "${SCRIPTS[@]}"
echo "[run] unixfun: done. Results: $TIME_FILE"
