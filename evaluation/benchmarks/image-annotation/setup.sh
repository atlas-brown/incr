#!/bin/bash
# setup.sh: idempotently install dependencies and fetch data for the image-annotation benchmark.
# Usage: setup.sh [--min|--small|--full]
# NOTE: Requires an OpenAI API key (OPENAI_API_KEY) set in the environment.
set -euo pipefail
cd "$(dirname "$0")" || exit 1

TOP=$(git rev-parse --show-toplevel)
BENCHMARK_DIR="$TOP/evaluation/benchmarks/image-annotation"

size=small
for arg in "$@"; do
    case "$arg" in
        --min)   size=min ;;
        --small) size=small ;;
        --full)  size=full ;;
    esac
done

echo "[setup] image-annotation: installing dependencies (llm, llm-interpolate)..."
bash "$BENCHMARK_DIR/install.sh"

echo "[setup] image-annotation: fetching $size inputs..."
bash "$BENCHMARK_DIR/fetch.sh" "--$size"
echo "[setup] image-annotation: done."
