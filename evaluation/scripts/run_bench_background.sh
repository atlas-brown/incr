#!/bin/bash
# Run the evaluation suite in the background (nohup). Logs to evaluation/bench_run.log
# Run from incr/: bash evaluation/scripts/run_bench_background.sh [extra run_all.sh args...]
# Default runs EASY / min / all modes (bash + incr + incr-observe).
set -e
EVAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INCR_ROOT="$(cd "$EVAL_DIR/.." && pwd)"

LOG="${EVAL_DIR}/bench_run.log"
PID_FILE="/tmp/incr_bench_run_all.pid"

if [[ $# -gt 0 ]]; then
    EXTRA=("$@")
else
    EXTRA=(--mode easy --size min --run-mode all)
fi

echo "Starting evaluation/benchmarks/run_all.sh ${EXTRA[*]} at $(date), log: $LOG"
nohup bash "$INCR_ROOT/evaluation/benchmarks/run_all.sh" "${EXTRA[@]}" >"$LOG" 2>&1 &
echo $! >"$PID_FILE"
echo "PID: $(cat "$PID_FILE"), tail -f $LOG to follow"
