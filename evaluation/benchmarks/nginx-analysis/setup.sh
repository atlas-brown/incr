#!/bin/bash
# setup.sh: idempotently install dependencies and fetch data for the nginx-analysis benchmark.
# Usage: setup.sh [--min|--small|--full]
set -euo pipefail
cd "$(dirname "$0")" || exit 1

TOP=$(git rev-parse --show-toplevel)
BENCHMARK_DIR="$TOP/evaluation/benchmarks/nginx-analysis"

size=small
for arg in "$@"; do
    case "$arg" in
        --min)   size=min ;;
        --small) size=small ;;
        --full)  size=full ;;
    esac
done

echo "[setup] nginx-analysis: fetching $size inputs..."
bash "$BENCHMARK_DIR/fetch.sh" "--$size"
echo "[setup] nginx-analysis: done."
