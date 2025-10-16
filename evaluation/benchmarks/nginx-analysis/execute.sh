#!/usr/bin/env bash

cd "$(dirname "$0")" || exit 1

TOP=$(git rev-parse --show-toplevel)
EVAL_DIR="${TOP}/evaluation"
BENCHMARK="nginx"
SCRIPT_DIR="${EVAL_DIR}/benchmarks/${BENCHMARK}/scripts"
OUTPUT_DIR="${EVAL_DIR}/benchmarks/${BENCHMARK}/outputs"

size=full
for arg in "$@"; do
    case "$arg" in
    --small) size=small ;;
    --min) size=min ;;
    esac
done
INPUT="${EVAL_DIR}/benchmarks/${BENCHMARK}/inputs/nginx-logs_${size}"

SCRIPTS=("nginx-1.sh" "nginx-2.sh" "nginx-3.sh")

TIME_FILE="${EVAL_DIR}/results/${BENCHMARK}-timings.csv"
mkdir -p "$(dirname "$TIME_FILE")"
echo "mode,script,time_sec" > "$TIME_FILE"

measure_time() {
    local mode="$1"
    local script="$2"
    mkdir -p "$outdir"

    local out_file="${OUTPUT_DIR}/${script}.${mode}.out"
    local err_file="${OUTPUT_DIR}/${script}.${mode}.err"

    local time_output
    time_output=$({ time "$@" >"$out_file" 2>"$err_file"; } 2>&1) || true

    # Extract the real time and convert to seconds
    local elapsed
    elapsed=$(echo "$time_output" | grep real | awk '{print $2}' |
        awk -Fm '{if (NF==2){sub("s","",$2); print ($1*60)+$2}else{gsub("s","",$1); print $1}}')

    echo "$mode,$script,$elapsed" >> "$TIME_FILE"
}

# Baseline: bash
for script in "${SCRIPTS[@]}"; do
    echo "Running $script with bash..."
    measure_time "bash" "$script" bash "${SCRIPT_DIR}/${script}" "$INPUT"
done

# Incremental run: incr
for script in "${SCRIPTS[@]}"; do
    echo "Running $script with incr..."
    measure_time "incr" "$script" "${EVAL_DIR}/incr.sh ${SCRIPT_DIR}/${script}" "$INPUT"
done
