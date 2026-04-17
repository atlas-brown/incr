#!/bin/bash
# setup.sh: idempotently install dependencies and fetch data for the dpt benchmark.
# Usage: setup.sh [--min|--small|--full]
# NOTE: Requires torch, torchvision, and the segment-anything model (~2GB download).
set -euo pipefail
cd "$(dirname "$0")" || exit 1

TOP=$(git rev-parse --show-toplevel)
BENCHMARK_DIR="$TOP/evaluation/benchmarks/dpt"

size=small
for arg in "$@"; do
    case "$arg" in
        --min)   size=min ;;
        --small) size=small ;;
        --full)  size=full ;;
    esac
done

echo "[setup] dpt: installing dependencies (torch, segment-anything, etc.)..."
bash "$BENCHMARK_DIR/install.sh"

echo "[setup] dpt: fetching $size inputs..."
bash "$BENCHMARK_DIR/fetch.sh" "--$size"
echo "[setup] dpt: done."
