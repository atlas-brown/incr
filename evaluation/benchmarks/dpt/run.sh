#!/bin/bash
# run.sh: run the dpt benchmark.
# Usage: run.sh [--mode bash|incr|both] [--size min|small|full] [--scripts a.sh,b.sh]
# NOTE: Requires torch and segment-anything model. Use setup.sh first.
cd "$(dirname "$0")" || exit 1

TOP=$(git rev-parse --show-toplevel)
BENCHMARK_DIR="$TOP/evaluation/benchmarks/dpt"
SCRIPT_DIR="$BENCHMARK_DIR/scripts"
INPUT_DIR="$BENCHMARK_DIR/inputs"
source "$TOP/evaluation/benchmarks/run_lib.sh"

parse_benchmark_run_sh_args "$@"

echo "[run] dpt: mode=$RUN_MODE size=$RUN_SIZE"
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
    full)  suffix=".full" ;;
esac
export IMG_DIR="$INPUT_DIR/dpt${suffix}"
export RUN_SIZE
export OUTPUT_DIR
TIME_FILE="$OUTPUT_DIR/timing.csv"

DEFAULT_SCRIPTS=(dpt_1.sh dpt_2.sh dpt_3a.sh dpt_3b.sh dpt_4.sh dpt_5a.sh dpt_5b.sh dpt_5c.sh dpt_5d.sh dpt_5e.sh)
finalize_benchmark_scripts "$SCRIPT_DIR" "${DEFAULT_SCRIPTS[@]}"
run_benchmark_scripts "${SCRIPTS[@]}"
echo "[run] dpt: done. Results: $TIME_FILE"
