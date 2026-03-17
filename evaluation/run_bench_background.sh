#!/bin/bash
# Run benchmark suite in background with periodic checks.
# Usage: bash run_bench_background.sh [default|observe]
# Run from incr/: bash evaluation/run_bench_background.sh default
set -e
cd "$(dirname "$0")/.." || exit 1

MODE="${1:-default}"
LOG="/users/jxia3/atlas/incr/evaluation/bench_run_${MODE}.log"
PID_FILE="/tmp/incr_bench_${MODE}.pid"

echo "Starting benchmark ($MODE) at $(date), log: $LOG"
nohup bash -c "
  cd /users/jxia3/atlas/incr
  export INCR_OBSERVE=$([ \"$MODE\" = observe ] && echo 1 || echo 0)
  bash evaluation/benchmarks/run.sh $MODE 2>&1
" > "$LOG" 2>&1 &
echo $! > "$PID_FILE"
echo "PID: $(cat $PID_FILE), tail -f $LOG to follow"
