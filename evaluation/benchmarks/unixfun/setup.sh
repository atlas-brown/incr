#!/bin/bash
# setup.sh: idempotently install dependencies and fetch data for the unixfun benchmark.
# Usage: setup.sh [--min|--small|--full]
set -euo pipefail
cd "$(dirname "$0")" || exit 1

TOP=$(git rev-parse --show-toplevel)
BENCHMARK_DIR="$TOP/evaluation/benchmarks/unixfun"
INPUT_DIR="$BENCHMARK_DIR/inputs"

size=small
for arg in "$@"; do
    case "$arg" in
        --min)   size=min ;;
        --small) size=small ;;
        --full)  size=full ;;
    esac
done

mkdir -p "$INPUT_DIR"

if [[ "$size" == "min" ]]; then
    target="$INPUT_DIR/4.min.txt"
    if [[ ! -f "$target" ]]; then
        echo "[setup] unixfun: building min input from repo data..."
        base="$BENCHMARK_DIR/min_inputs/4.txt"
        # Build a ~6MB file by repeating the base chess notation file
        base_size=$(wc -c < "$base")
        target_size=$((6 * 1024 * 1024))
        iter=$(( target_size / base_size + 1 ))
        for (( i = 0; i < iter; i++ )); do
            cat "$base" >> "$target"
        done
    fi
else
    echo "[setup] unixfun: fetching $size inputs..."
    bash "$BENCHMARK_DIR/fetch.sh" "--$size"
    # fetch.sh --small creates 4_1G.txt then moves it to 4.small.txt (handled inside)
    # No rename needed for small/full
fi

echo "[setup] unixfun: done."
