#!/bin/bash
# run.sh: run the beginner benchmark.
# Usage: run.sh [--mode bash|incr|both] [--size min|small|full] [--scripts a.sh,b.sh]
cd "$(dirname "$0")" || exit 1

TOP=$(git rev-parse --show-toplevel)
BENCHMARK_DIR="$TOP/evaluation/benchmarks/beginner"
SCRIPT_DIR="$BENCHMARK_DIR/scripts"
source "$TOP/evaluation/benchmarks/run_lib.sh"

parse_benchmark_run_sh_args "$@"

echo "[run] beginner: mode=$RUN_MODE size=$RUN_SIZE"
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
    min)   INPUT="$BENCHMARK_DIR/inputs/nginx-logs_min" ;;
    small) INPUT="$BENCHMARK_DIR/inputs/nginx-logs_small" ;;
    full)  INPUT="$BENCHMARK_DIR/inputs/nginx-logs_full" ;;
esac
export IN="$INPUT/log0"
export OUT="$OUTPUT_DIR"
TIME_FILE="$OUTPUT_DIR/timing.csv"

DEFAULT_SCRIPTS=(beginner-01.sh beginner-02.sh beginner-03.sh beginner-04.sh beginner-05.sh
         beginner-06.sh beginner-07.sh beginner-08.sh beginner-09.sh beginner-10.sh
         beginner-11.sh beginner-12.sh beginner-13.sh beginner-14.sh)
finalize_benchmark_scripts "$SCRIPT_DIR" "${DEFAULT_SCRIPTS[@]}"
run_benchmark_scripts "${SCRIPTS[@]}"
echo "[run] beginner: done. Results: $TIME_FILE"
