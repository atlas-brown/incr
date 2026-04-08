#!/bin/bash
# setup.sh: idempotently install dependencies and fetch data for the spell benchmark.
# Usage: setup.sh [--min|--small|--full]
set -euo pipefail
cd "$(dirname "$0")" || exit 1

TOP=$(git rev-parse --show-toplevel)
BENCHMARK_DIR="$TOP/evaluation/benchmarks/spell"
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

# spell-*.sh pipelines use comm(1) against the system dictionary (scripts 6–7 especially).
if [[ ! -f /usr/share/dict/words ]]; then
    echo "[setup] spell: installing system word list (wamerican)..."
    sudo apt-get update -qq
    sudo apt-get install -y wamerican
fi

if [[ "$size" == "min" ]]; then
    if [[ ! -d "$INPUT_DIR/pg-min" ]]; then
        echo "[setup] spell: copying min inputs from repo..."
        cp -r "$BENCHMARK_DIR/min_inputs/pg-min" "$INPUT_DIR/pg-min"
    fi
else
    echo "[setup] spell: fetching $size inputs..."
    bash "$BENCHMARK_DIR/fetch.sh" "--$size"
fi

echo "[setup] spell: done."
