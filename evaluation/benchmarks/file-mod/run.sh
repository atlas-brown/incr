#!/bin/bash
# run.sh: run the file-mod benchmark.
# Usage: run.sh [--mode bash|incr|both] [--size min|small|full] [--scripts a.sh,b.sh]
cd "$(dirname "$0")" || exit 1

TOP=$(git rev-parse --show-toplevel)
BENCHMARK_DIR="$TOP/evaluation/benchmarks/file-mod"
SCRIPT_DIR="$BENCHMARK_DIR/scripts"
INPUT_DIR="$BENCHMARK_DIR/inputs"
source "$TOP/evaluation/benchmarks/run_lib.sh"

parse_benchmark_run_sh_args "$@"

echo "[run] file-mod: mode=$RUN_MODE size=$RUN_SIZE"
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
    min)   suffix=".min" ;;
    small) suffix=".small" ;;
    full)  suffix="" ;;
esac
export IN="$INPUT_DIR/songs${suffix}"
export OUT="$OUTPUT_DIR"
export IMG_DIR="$INPUT_DIR/dpt${suffix}"
TIME_FILE="$OUTPUT_DIR/timing.csv"

DEFAULT_SCRIPTS=(file-mod-1.sh file-mod-2.sh file-mod-3.sh file-mod-4.sh file-mod-5.sh file-mod-6.sh file-mod-7.sh)
finalize_benchmark_scripts "$SCRIPT_DIR" "${DEFAULT_SCRIPTS[@]}"
run_benchmark_scripts "${SCRIPTS[@]}"
echo "[run] file-mod: done. Results: $TIME_FILE"
