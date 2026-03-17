#!/bin/bash
# Verify bio and nlp-ngrams speedups by re-running with clean cache.
# Run from incr/: bash evaluation/verify_speedup.sh
set -e
cd "$(dirname "$0")/.." || exit 1

BENCH_DIR="evaluation/benchmarks"
run_one() {
  local bench=$1 mode=$2
  export INCR_OBSERVE=$([ "$mode" = "observe" ] && echo 1 || echo 0)
  sudo rm -rf "$BENCH_DIR/$bench/cache" "$BENCH_DIR/$bench/outputs" 2>/dev/null || true
  mkdir -p "$BENCH_DIR/$bench/outputs"
  echo "=== $bench $mode ==="
  local start=$(date +%s)
  (cd "$BENCH_DIR" && bash "./$bench/execute.sh" --small --incr-only) 2>&1 | tail -5
  local end=$(date +%s)
  local total=$(awk -F, 'NR>1 {s+=$3} END {print s+0}' "$BENCH_DIR/$bench/outputs/timing.csv" 2>/dev/null || echo 0)
  echo "Wall: $((end-start))s, Sum of timings: ${total}s"
  echo ""
}

echo "Verifying bio speedup..."
run_one "bio" "default"
run_one "bio" "observe"

echo "Verifying nlp-ngrams speedup..."
run_one "nlp-ngrams" "default"
run_one "nlp-ngrams" "observe"

echo "Done. Compare the 'Sum of timings' values."
