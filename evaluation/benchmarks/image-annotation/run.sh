#!/bin/bash
# run.sh: run the image-annotation benchmark.
# Usage: run.sh [--mode bash|incr|both] [--size min|small|full] [--scripts a.sh,b.sh]
# NOTE: Requires OPENAI_API_KEY set in environment.
cd "$(dirname "$0")" || exit 1

TOP=$(git rev-parse --show-toplevel)
BENCHMARK_DIR="$TOP/evaluation/benchmarks/image-annotation"
SCRIPT_DIR="$BENCHMARK_DIR/scripts"
INPUT_DIR="$BENCHMARK_DIR/inputs"
source "$TOP/evaluation/benchmarks/run_lib.sh"

parse_benchmark_run_sh_args "$@"

echo "[run] image-annotation: mode=$RUN_MODE size=$RUN_SIZE"
OUTPUT_DIR="$BENCHMARK_DIR/outputs/$RUN_SIZE"

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
    echo "[run] WARNING: OPENAI_API_KEY is not set. image-annotation scripts will fail."
fi

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
export IMG_DIR="$INPUT_DIR/jpg${suffix}/jpg"
export IN="$INPUT_DIR/jpg${suffix}/jpg"
export OUT="$OUTPUT_DIR"
TIME_FILE="$OUTPUT_DIR/timing.csv"

DEFAULT_SCRIPTS=(image-annotation-1.sh image-annotation-2.sh image-annotation-3.sh image-annotation-4.sh \
         image-annotation-5.sh image-annotation-6.sh image-annotation-7.sh)
finalize_benchmark_scripts "$SCRIPT_DIR" "${DEFAULT_SCRIPTS[@]}"
run_benchmark_scripts "${SCRIPTS[@]}"
echo "[run] image-annotation: done. Results: $TIME_FILE"
