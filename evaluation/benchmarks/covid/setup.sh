#!/bin/bash
# setup.sh: idempotently install dependencies and fetch data for the covid benchmark.
# Usage: setup.sh [--min|--small|--full]
set -euo pipefail
cd "$(dirname "$0")" || exit 1

TOP=$(git rev-parse --show-toplevel)
BENCHMARK_DIR="$TOP/evaluation/benchmarks/covid"

size=small
for arg in "$@"; do
    case "$arg" in
        --min)   size=min ;;
        --small) size=small ;;
        --full)  size=full ;;
    esac
done

echo "[setup] covid: fetching $size inputs..."
bash "$BENCHMARK_DIR/fetch.sh" "--$size"
echo "[setup] covid: done."
