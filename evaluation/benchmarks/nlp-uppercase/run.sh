#!/bin/bash
# run.sh: run the nlp-uppercase benchmark.
# Usage: run.sh [--mode bash|incr|both] [--size min|small|full] [--scripts a.sh,b.sh]
cd "$(dirname "$0")" || exit 1

TOP=$(git rev-parse --show-toplevel)
BENCHMARK_DIR="$TOP/evaluation/benchmarks/nlp-uppercase"
SCRIPT_DIR="$BENCHMARK_DIR/scripts"
source "$TOP/evaluation/benchmarks/run_lib.sh"

parse_benchmark_run_sh_args "$@"

echo "[run] nlp-uppercase: mode=$RUN_MODE size=$RUN_SIZE"
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
    min)   export IN="$BENCHMARK_DIR/inputs/pg-min"
           export ENTRIES=1 ;;
    small) export IN="$BENCHMARK_DIR/inputs/pg-small"
           export ENTRIES=30 ;;
    full)  export IN="$BENCHMARK_DIR/inputs/pg"
           export ENTRIES=115916 ;;
esac
export BENCHMARK_DIR
TIME_FILE="$OUTPUT_DIR/timing.csv"

DEFAULT_SCRIPTS=(uppercase_by_token.sh uppercase_by_type.sh)
finalize_benchmark_scripts "$SCRIPT_DIR" "${DEFAULT_SCRIPTS[@]}"
run_benchmark_scripts "${SCRIPTS[@]}"
echo "[run] nlp-uppercase: done. Results: $TIME_FILE"
