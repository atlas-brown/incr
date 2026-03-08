#!/bin/bash
# Run full evaluation suite in default (try+strace) and/or observe mode.
# Usage: bash run.sh [default|observe]
#   default  - run benchmarks with incr in default mode (try+strace)
#   observe  - run benchmarks with incr using observe
#   (none)   - run both modes
#
# Run from incr/: bash evaluation/run.sh [default|observe]
# Results: evaluation/run_results/default/ and evaluation/run_results/observe/
cd "$(dirname "$0")/.." || exit 1

MODE="${1:-}"
bash evaluation/benchmarks/run.sh "$MODE"
