#!/bin/bash
# run.sh: run the bio benchmark.
# Usage: run.sh [--mode bash|incr|both] [--size min|small|full] [--scripts a.sh,b.sh]
cd "$(dirname "$0")" || exit 1

TOP=$(git rev-parse --show-toplevel)
BENCHMARK_DIR="$TOP/evaluation/benchmarks/bio"
SCRIPT_DIR="$BENCHMARK_DIR/scripts"
source "$TOP/evaluation/benchmarks/run_lib.sh"

parse_benchmark_run_sh_args "$@"

echo "[run] bio: mode=$RUN_MODE size=$RUN_SIZE"
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
    min)   export IN="$BENCHMARK_DIR/inputs/bio-min"
           export IN_NAME="$BENCHMARK_DIR/inputs/bio-min/input_min.txt" ;;
    small) export IN="$BENCHMARK_DIR/inputs/bio-small"
           export IN_NAME="$BENCHMARK_DIR/inputs/bio-small/input_small.txt" ;;
    full)  export IN="$BENCHMARK_DIR/inputs/bio-full"
           export IN_NAME="$BENCHMARK_DIR/inputs/bio-full/input.txt" ;;
esac
export OUT="$OUTPUT_DIR"
TIME_FILE="$OUTPUT_DIR/timing.csv"

# bio scripts need Gene_locs.txt in the scripts directory
cp "$BENCHMARK_DIR/Gene_locs.txt" "$SCRIPT_DIR/" 2>/dev/null || true

DEFAULT_SCRIPTS=(bio-1.sh bio-2.sh bio-3.sh bio-4-0.sh bio-4.sh bio-5.sh bio-6.sh)
finalize_benchmark_scripts "$SCRIPT_DIR" "${DEFAULT_SCRIPTS[@]}"
run_benchmark_scripts "${SCRIPTS[@]}"
echo "[run] bio: done. Results: $TIME_FILE"
