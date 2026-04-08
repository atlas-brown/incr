#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")" || exit 1

TOP=$(git rev-parse --show-toplevel)
BENCHMARK="beginner"
INPUT_DIR="${TOP}/evaluation/benchmarks/${BENCHMARK}/inputs"

URL=https://atlas.cs.brown.edu/data
mkdir -p "$INPUT_DIR"

size=full
for arg in "$@"; do
    case "$arg" in
        --small) size=small ;;
        --min)   size=min ;;
    esac
done

if [[ "$size" == "min" ]]; then
    if [[ ! -d "$INPUT_DIR/nginx-logs_$size" ]]; then
        mkdir -p "$INPUT_DIR/nginx-logs_$size"
        cp "${INPUT_DIR}/../min_inputs/nginx-logs/"* "$INPUT_DIR/nginx-logs_$size"
    fi
    exit 0
elif [[ "$size" == "small" ]]; then
    if [[ ! -d "$INPUT_DIR/nginx-logs_$size" ]]; then
        need_bytes=$((32 * 1024 * 1024 * 1024))
        avail_bytes=$(df -B1 --output=avail "$INPUT_DIR" | tail -1)
        if [[ "$avail_bytes" -lt "$need_bytes" ]]; then
            echo "[fetch] ERROR: need at least ~32GiB free on this filesystem for beginner --small inputs (available: $avail_bytes bytes)." >&2
            echo "[fetch] Free space or use --min for tiny inputs." >&2
            exit 1
        fi
        zip_dst="$INPUT_DIR/nginx.zip"
        wget --no-check-certificate "$URL/nginx.zip" -O "$zip_dst"
        unzip "$zip_dst" -d "$INPUT_DIR"
        mv "$INPUT_DIR/nginx-logs" "$INPUT_DIR/nginx-logs_$size"
        rm -f "$zip_dst"
        input_dir="$INPUT_DIR/nginx-logs_$size"
        for log in "$input_dir"/*; do
            if [[ "$log" != "$input_dir/log0" ]]; then
                cat "$log" >> "$input_dir/log0"
                rm -f "$log"
            fi
        done
        for _i in {1..3}; do
            cp "$input_dir/log0" "$input_dir/dup"
            cat "$input_dir/dup" >> "$input_dir/log0"
            rm -f "$input_dir/dup"
        done
    fi
    exit 0
else
    if [[ ! -d "$INPUT_DIR/nginx-logs_$size" ]]; then
        zip_dst="$INPUT_DIR/nginx.zip"
        wget --no-check-certificate "$URL/nginx.zip" -O "$zip_dst"
        unzip "$zip_dst" -d "$INPUT_DIR"
        mv "$INPUT_DIR/nginx-logs" "$INPUT_DIR/nginx-logs_$size"
        rm -f "$zip_dst"

        zip_dst="$INPUT_DIR/nginx_large.zip"
        wget --no-check-certificate "$URL/log-analysis/web-server-access-logs.zip" -O "$zip_dst"
        unzip "$zip_dst" -d "$INPUT_DIR"
        mv "$INPUT_DIR/access.log" "$INPUT_DIR/nginx-logs_$size/access.log"
        rm -f "$zip_dst"
    fi
fi
