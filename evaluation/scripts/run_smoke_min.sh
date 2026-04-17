#!/bin/bash
# Quick smoke test: EASY benchmarks, min inputs, all three modes (bash + incr + incr-observe).
# Run from incr/: bash evaluation/scripts/run_smoke_min.sh
# Forwards extra args to run_all.sh (e.g. --skip-setup after a successful setup).

EVAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INCR_ROOT="$(cd "$EVAL_DIR/.." && pwd)"

cleanup_on_exit() {
    echo ""
    "$EVAL_DIR/scripts/restore_benchmark_scripts.sh" 2>/dev/null || true
    rm -rf /tmp/sort* /tmp/tmp* /tmp/cache* /tmp/incr_bench* 2>/dev/null || true
}
trap cleanup_on_exit EXIT INT TERM

exec bash "$INCR_ROOT/evaluation/benchmarks/run_all.sh" --mode easy --size min --run-mode all "$@"
