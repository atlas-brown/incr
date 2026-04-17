#!/bin/bash
# Thin wrapper around the benchmark orchestrator. Run from incr/:
#   bash evaluation/run.sh [args...]
# Arguments are forwarded to evaluation/benchmarks/run_all.sh.
# Example:
#   bash evaluation/run.sh --mode easy --size min --run-mode both
cd "$(dirname "$0")/.." || exit 1
exec bash evaluation/benchmarks/run_all.sh "$@"
