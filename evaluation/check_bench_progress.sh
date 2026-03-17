#!/bin/bash
# Check benchmark progress, clean up if hung.
# Usage: bash check_bench_progress.sh
LOG_D="/users/jxia3/atlas/incr/evaluation/bench_run_default.log"
LOG_O="/users/jxia3/atlas/incr/evaluation/bench_run_observe.log"
PID_D="/tmp/incr_bench_default.pid"
PID_O="/tmp/incr_bench_observe.pid"

check_one() {
  local name=$1 log=$2 pid_file=$3
  if [[ ! -f "$pid_file" ]]; then return; fi
  local pid=$(cat "$pid_file" 2>/dev/null)
  if [[ -z "$pid" ]]; then return; fi
  if kill -0 "$pid" 2>/dev/null; then
    echo "=== $name still running (pid $pid) ==="
    tail -3 "$log" 2>/dev/null || true
    # Check if log has grown in last 2 min (not hung)
    local mtime=$(stat -c %Y "$log" 2>/dev/null || echo 0)
    local now=$(date +%s)
    if (( now - mtime > 120 )); then
      echo "WARNING: $name may be hung (no log activity for 2+ min)"
    fi
  else
    echo "=== $name finished ==="
    tail -20 "$log" 2>/dev/null || true
    rm -f "$pid_file"
  fi
}

check_one "default" "$LOG_D" "$PID_D"
check_one "observe" "$LOG_O" "$PID_O"
