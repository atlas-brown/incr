#!/bin/bash
# Run benchmarks in default (try+strace) or observe mode.
# Usage: bash run.sh [default|observe]
#   default  - incr with try+strace (INCR_OBSERVE=0)
#   observe  - incr with observe when available (INCR_OBSERVE=1)
#   (none)   - run both modes, save to run_results/default/ and run_results/observe/
cd "$(dirname "$0")" || exit 1

EVAL_DIR="$(cd .. && pwd)"
cleanup_on_exit() {
    echo ""
    echo "Cleaning up (interrupted or done)..."
    "$EVAL_DIR/scripts/restore_benchmark_scripts.sh" 2>/dev/null || true
    rm -rf /tmp/sort* /tmp/tmp* /tmp/cache* /tmp/incr_bench* 2>/dev/null || true
}
trap cleanup_on_exit EXIT INT TERM

# Restore any scripts left in incr state from previous interrupted run
"$EVAL_DIR/scripts/restore_benchmark_scripts.sh" 2>/dev/null || true
rm -rf /tmp/sort* /tmp/tmp* 2>/dev/null || true

# Skip image-annotation (requires OpenAI API key), file-mod (no min_inputs)
BENCHMARKS=(
    "beginner"
    "bio"
    "covid"
    "dpt"
    "nginx-analysis"
    "nlp-uppercase"
    "nlp-ngrams"
    "poet"
    "spell"
    "unixfun"
    "weather"
    "word-freq"
)
SIZES=(
    "small"
    "small"
    "small"
    "small"
    "small"
    "small"
    "small"
    "small"
    "small"
    "small"
    "small"
    "small"
)

MODE_ARG="${1:-}"
if [[ "$MODE_ARG" == "default" ]]; then
    MODES=("default")
    export INCR_OBSERVE=0
elif [[ "$MODE_ARG" == "observe" ]]; then
    MODES=("observe")
    export INCR_OBSERVE=1
else
    MODES=("default" "observe")
fi

for eval_mode in "${MODES[@]}"; do
    if [[ "$eval_mode" == "default" ]]; then
        export INCR_OBSERVE=0
    else
        export INCR_OBSERVE=1
    fi

    RESULTS_DIR="../run_results/$eval_mode"
    rm -rf "$RESULTS_DIR"
    mkdir -p "$RESULTS_DIR"

    echo "=============================================="
    echo "Running benchmarks in $eval_mode mode"
    echo "=============================================="

    for i in "${!BENCHMARKS[@]}"; do
        benchmark="${BENCHMARKS[$i]}"
        size="${SIZES[$i]}"
        mode=""

        echo "Running $benchmark '$mode' $size ($eval_mode)"
        sudo bash "./$benchmark/clean.sh"
        sleep 0.01

        if [[ "$mode" == "" ]]; then
            bash "./$benchmark/execute.sh" "--$size" "--incr-only"
        else
            bash "./$benchmark/execute.sh" "$mode" "--$size" "--incr-only"
        fi
        sleep 0.01

        cp "./$benchmark/outputs/timing.csv" "$RESULTS_DIR/$benchmark-time.csv"
        if [[ -d "./$benchmark/cache" ]]; then
            du -sb "./$benchmark/cache" > "$RESULTS_DIR/$benchmark-size.txt"
        else
            echo "0" > "$RESULTS_DIR/$benchmark-size.txt"
        fi

        rm -rf "./$benchmark/cache"
        rm -rf "./$benchmark/outputs"
        rm -rf /tmp/sort*
        rm -rf /tmp/tmp*
    done
done
