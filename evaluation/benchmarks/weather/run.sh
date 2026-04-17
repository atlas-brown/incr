#!/bin/bash
# run.sh: run the weather benchmark (temp-analytics scripts by default).
# Usage: run.sh [--mode bash|incr|both] [--size min|small|full] [--scripts a.sh,b.sh] [--tuft]
# --tuft: run tuft-weather scripts instead of temp-analytics scripts
cd "$(dirname "$0")" || exit 1

TOP=$(git rev-parse --show-toplevel)
BENCHMARK_DIR="$TOP/evaluation/benchmarks/weather"
SCRIPT_DIR="$BENCHMARK_DIR/scripts"
source "$TOP/evaluation/benchmarks/run_lib.sh"

TUFT=0
filtered_args=()
for arg in "$@"; do
    case "$arg" in
        --tuft) TUFT=1 ;;
        *) filtered_args+=("$arg") ;;
    esac
done
parse_benchmark_run_sh_args "${filtered_args[@]}"

echo "[run] weather: mode=$RUN_MODE size=$RUN_SIZE tuft=$TUFT"
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

mkdir -p "$OUTPUT_DIR"
TIME_FILE="$OUTPUT_DIR/timing.csv"

if [[ "$TUFT" == "1" ]]; then
    export input_file="$BENCHMARK_DIR/inputs/tuft_weather.${RUN_SIZE}.txt"
    export scripts_dir="$SCRIPT_DIR"
    DEFAULT_SCRIPTS=(tuft-weather-1.sh tuft-weather-2.sh tuft-weather-3.sh)
else
    export input_file="$BENCHMARK_DIR/inputs/temperatures.${RUN_SIZE}.txt"
    export INPUT="$BENCHMARK_DIR/inputs/temperatures.${RUN_SIZE}.txt"
    export statistics_dir="$OUTPUT_DIR/statistics.${RUN_SIZE}"
    mkdir -p "$statistics_dir"
    DEFAULT_SCRIPTS=(temp-analytics-1.sh temp-analytics-2.sh temp-analytics-3.sh)
fi
finalize_benchmark_scripts "$SCRIPT_DIR" "${DEFAULT_SCRIPTS[@]}"
run_benchmark_scripts "${SCRIPTS[@]}"
echo "[run] weather: done. Results: $TIME_FILE"
