#!/bin/bash
# Verify bio and nlp-ngrams speedups - re-run with --min and clean cache.
# Run from incr/: bash evaluation/verify_bio_ngrams.sh
set -e
cd "$(dirname "$0")/.." || exit 1

BENCH_DIR="evaluation/benchmarks"

run_bench() {
  local bench=$1 mode=$2
  export INCR_OBSERVE=$([ "$mode" = "observe" ] && echo 1 || echo 0)
  sudo rm -rf "$BENCH_DIR/$bench/cache" "$BENCH_DIR/$bench/outputs" 2>/dev/null || true
  mkdir -p "$BENCH_DIR/$bench/outputs"
  echo "=== $bench $mode (--min) ==="
  (cd "$BENCH_DIR" && bash "./$bench/execute.sh" --min --incr-only) 2>&1 | tail -3
  local total=$(awk -F, 'NR>1 {s+=$3} END {print s+0}' "$BENCH_DIR/$bench/outputs/timing.csv" 2>/dev/null || echo 0)
  echo "Total: ${total}s"
  echo ""
}

echo "--- bio: was 45s default vs 5s observe (9x) ---"
run_bench "bio" "default"
run_bench "bio" "observe"

echo "--- nlp-ngrams: was 61s default vs 21s observe (2.9x). ngrams-2/3 may have cache hits. ---"
run_bench "nlp-ngrams" "default"
run_bench "nlp-ngrams" "observe"

echo "Done. Compare totals - similar ratio = real speedup."
