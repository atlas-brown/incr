#!/bin/bash
# setup.sh: idempotently install dependencies and fetch data for the word-freq benchmark.
# Usage: setup.sh [--min|--small|--full]
set -euo pipefail
cd "$(dirname "$0")" || exit 1

TOP=$(git rev-parse --show-toplevel)
BENCHMARK_DIR="$TOP/evaluation/benchmarks/word-freq"
INPUT_DIR="$BENCHMARK_DIR/inputs"

size=small
for arg in "$@"; do
    case "$arg" in
        --min)   size=min ;;
        --small) size=small ;;
        --full)  size=full ;;
    esac
done

echo "[setup] word-freq: fetching $size inputs..."
bash "$BENCHMARK_DIR/fetch.sh" "--$size"

# execute.sh --min expects inputs/10M.txt, but fetch.sh --min doesn't create it.
# Build it from 1M.txt (which fetch.sh downloads unconditionally).
if [[ "$size" == "min" ]]; then
    if [[ ! -f "$INPUT_DIR/10M.txt" && -f "$INPUT_DIR/1M.txt" ]]; then
        echo "[setup] word-freq: building 10M.txt from 1M.txt..."
        for (( i = 0; i < 10; i++ )); do
            cat "$INPUT_DIR/1M.txt" >> "$INPUT_DIR/10M.txt"
        done
    fi
fi

echo "[setup] word-freq: done."
