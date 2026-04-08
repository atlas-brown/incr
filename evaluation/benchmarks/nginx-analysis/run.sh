#!/bin/bash
# run.sh: run the nginx-analysis benchmark.
# Usage: run.sh [--mode bash|incr|both] [--size min|small|full] [--scripts a.sh,b.sh]
cd "$(dirname "$0")" || exit 1

TOP=$(git rev-parse --show-toplevel)
BENCHMARK_DIR="$TOP/evaluation/benchmarks/nginx-analysis"
SCRIPT_DIR="$BENCHMARK_DIR/scripts"
source "$TOP/evaluation/benchmarks/run_lib.sh"

parse_benchmark_run_sh_args "$@"

echo "[run] nginx-analysis: mode=$RUN_MODE size=$RUN_SIZE"
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
    min)   export INPUT="$BENCHMARK_DIR/inputs/nginx-logs_min" ;;
    small) export INPUT="$BENCHMARK_DIR/inputs/nginx-logs_small" ;;
    full)  export INPUT="$BENCHMARK_DIR/inputs/nginx-logs_full" ;;
esac
TIME_FILE="$OUTPUT_DIR/timing.csv"

DEFAULT_SCRIPTS=(nginx-1.sh nginx-2.sh nginx-3.sh nginx-4.sh nginx-5.sh nginx-6.sh nginx-7.sh nginx-8.sh \
         nginx-9.sh nginx-10.sh nginx-11.sh nginx-12.sh nginx-13.sh nginx-14.sh nginx-15.sh \
         nginx-16.sh nginx-17.sh nginx-18.sh nginx-19.sh nginx-20.sh nginx-21.sh nginx-22.sh)
finalize_benchmark_scripts "$SCRIPT_DIR" "${DEFAULT_SCRIPTS[@]}"
run_benchmark_scripts "${SCRIPTS[@]}"
echo "[run] nginx-analysis: done. Results: $TIME_FILE"
