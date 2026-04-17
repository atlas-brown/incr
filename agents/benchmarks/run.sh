#!/bin/bash
# Run benchmark and save results.
# Usage: bash run.sh [output_file]
# Run from incr/: bash agents/benchmarks/run.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INCR_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT="${1:-$SCRIPT_DIR/results.txt}"

echo "Running benchmark (output -> $OUTPUT)..."
cd "$INCR_ROOT" && bash "$SCRIPT_DIR/bench.sh" 2>&1 | tee "$OUTPUT"
echo ""; echo "Results saved to $OUTPUT"
