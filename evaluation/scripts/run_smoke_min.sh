#!/bin/bash
# Smoke test: run each benchmark with --min --incr-only to verify it works.
# Usage: bash run_smoke_min.sh [default|observe]
# Run from incr/: bash evaluation/scripts/run_smoke_min.sh
EVAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$EVAL_DIR" || exit 1

cleanup_on_exit() {
    echo ""
    "$EVAL_DIR/scripts/restore_benchmark_scripts.sh" 2>/dev/null || true
    for b in beginner bio covid dpt nginx-analysis nlp-uppercase nlp-ngrams poet spell unixfun weather word-freq; do
        sudo rm -rf "benchmarks/$b/cache" "benchmarks/$b/outputs" 2>/dev/null || true
    done
    rm -rf /tmp/sort* /tmp/tmp* /tmp/cache* /tmp/incr_bench* 2>/dev/null || true
}
trap cleanup_on_exit EXIT INT TERM

# Skip image-annotation (OpenAI key), file-mod (no min_inputs)
BENCHMARKS=(
    "beginner" "bio" "covid" "dpt"
    "nginx-analysis" "nlp-uppercase" "nlp-ngrams" "poet" "spell"
    "unixfun" "weather" "word-freq"
)

MODE_ARG="${1:-observe}"
if [[ "$MODE_ARG" == "default" ]]; then
    export INCR_OBSERVE=0
else
    export INCR_OBSERVE=1
fi

echo "=============================================="
echo "Smoke test (--min, incr only) in $MODE_ARG mode"
echo "=============================================="

for benchmark in "${BENCHMARKS[@]}"; do
    echo ""
    echo ">>> Smoke: $benchmark"
    if [[ ! -f "benchmarks/$benchmark/fetch.sh" ]]; then
        echo "  Skipped: no fetch.sh"
        continue
    fi
    bash "benchmarks/$benchmark/fetch.sh" --min || { echo "  FAILED: fetch"; exit 1; }
    sudo bash "benchmarks/$benchmark/clean.sh" 2>/dev/null || true
    bash "benchmarks/$benchmark/execute.sh" "--min" "--incr-only" || { echo "  FAILED: execute"; sudo bash "benchmarks/$benchmark/clean.sh" 2>/dev/null || true; exit 1; }
    if [[ ! -f "benchmarks/$benchmark/outputs/timing.csv" ]]; then
        echo "  FAILED: no timing.csv"
        exit 1
    fi
    echo "  OK"
    sudo bash "benchmarks/$benchmark/clean.sh" 2>/dev/null || true
done

echo ""
echo "=============================================="
echo "Smoke test passed for all benchmarks"
echo "=============================================="
