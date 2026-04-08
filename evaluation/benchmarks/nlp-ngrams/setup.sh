#!/bin/bash
# setup.sh: idempotently install dependencies and fetch data for the nlp-ngrams benchmark.
# Usage: setup.sh [--min|--small|--full]
set -euo pipefail
cd "$(dirname "$0")" || exit 1

TOP=$(git rev-parse --show-toplevel)
BENCHMARK_DIR="$TOP/evaluation/benchmarks/nlp-ngrams"
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
    if [[ ! -d "$INPUT_DIR/pg-min" ]]; then
        echo "[setup] nlp-ngrams: copying min inputs from repo..."
        cp -r "$BENCHMARK_DIR/min_inputs/pg-min" "$INPUT_DIR/pg-min"
    fi
else
    echo "[setup] nlp-ngrams: fetching $size inputs..."
    bash "$BENCHMARK_DIR/fetch.sh" "--$size"
fi

echo "[setup] nlp-ngrams: done."
