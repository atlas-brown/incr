#!/bin/bash
# Install, fetch, and run all benchmarks.
#
# Options:
#   --mode easy|full       default: easy — 12 benchmarks; full: +dpt, image-annotation
#   --size min|small       default: min — tiny inputs; small: paper-sized workloads
#   --run-mode bash|incr|both   default: both
#   --skip-setup
#   --clear-cache / --no-clear-cache   default: clear cache after each benchmark
#   --clear-outputs / --no-clear-outputs
#       For --size small, outputs are cleared after each benchmark by default
#       (large stdout; avoids filling disk). Override with --no-clear-outputs.
#   --timeout=SECS           default: 14400 (beginner small can exceed 2h wall time)
#   --results-dir=DIR        default: ../run_results
#   --only=a,b,c             run only these benchmarks (names as for --mode easy|full)
#   --help
set -uo pipefail
cd "$(dirname "$0")" || exit 1

TOP=$(git rev-parse --show-toplevel)
source "$TOP/evaluation/benchmarks/run_lib.sh"

MODE=easy
SIZE=min
RUN_MODE=both
SKIP_SETUP=0
CLEAR_CACHE=1
CLEAR_OUTPUTS=0
CLEAR_OUTPUTS_SET=0
BENCH_TIMEOUT=14400
RESULTS_DIR="$TOP/evaluation/run_results"
RUN_ONLY_BENCHMARKS=()

for arg in "$@"; do
    case "$arg" in
        --mode=*)        MODE="${arg#--mode=}" ;;
        --size=*)        SIZE="${arg#--size=}" ;;
        --run-mode=*)    RUN_MODE="${arg#--run-mode=}" ;;
        --results-dir=*) RESULTS_DIR="${arg#--results-dir=}" ;;
        --only=*)
            _list="${arg#--only=}"
            IFS=',' read -ra _parts <<< "$_list"
            for t in "${_parts[@]}"; do
                t="${t#"${t%%[![:space:]]*}"}"
                t="${t%"${t##*[![:space:]]}"}"
                [[ -n "$t" ]] && RUN_ONLY_BENCHMARKS+=("$t")
            done
            ;;
        --mode)          ;;
        --size)          ;;
        --run-mode)      ;;
        easy|full)       MODE=$arg ;;
        min|small)       SIZE=$arg ;;
        bash|incr|both)  RUN_MODE=$arg ;;
        --skip-setup)    SKIP_SETUP=1 ;;
        --clear-cache)   CLEAR_CACHE=1 ;;
        --no-clear-cache) CLEAR_CACHE=0 ;;
        --clear-outputs) CLEAR_OUTPUTS=1; CLEAR_OUTPUTS_SET=1 ;;
        --no-clear-outputs) CLEAR_OUTPUTS=0; CLEAR_OUTPUTS_SET=1 ;;
        --timeout=*)     BENCH_TIMEOUT="${arg#--timeout=}" ;;
        --help|-h)
            sed -n '2,17p' "$0"
            exit 0
            ;;
    esac
done

if [[ "$CLEAR_OUTPUTS_SET" -eq 0 && "$SIZE" == "small" ]]; then
    CLEAR_OUTPUTS=1
fi

# Benchmark lists
EASY_BENCHMARKS=(
    beginner
    bio
    covid
    file-mod
    nginx-analysis
    nlp-ngrams
    nlp-uppercase
    poet
    spell
    unixfun
    weather
    word-freq
)

COMPLEX_BENCHMARKS=(
    dpt
    image-annotation
)

if [[ "$MODE" == "full" ]]; then
    BENCHMARKS=("${EASY_BENCHMARKS[@]}" "${COMPLEX_BENCHMARKS[@]}")
else
    BENCHMARKS=("${EASY_BENCHMARKS[@]}")
fi

if [[ ${#RUN_ONLY_BENCHMARKS[@]} -gt 0 ]]; then
    _filtered=()
    for b in "${RUN_ONLY_BENCHMARKS[@]}"; do
        _ok=0
        for a in "${BENCHMARKS[@]}"; do
            if [[ "$b" == "$a" ]]; then
                _ok=1
                break
            fi
        done
        if [[ "$_ok" -eq 0 ]]; then
            echo "[run] ERROR: --only benchmark '$b' is not in the current suite (mode=$MODE)." >&2
            exit 1
        fi
        _filtered+=("$b")
    done
    BENCHMARKS=("${_filtered[@]}")
fi

echo "============================================================"
echo " incr evaluation suite"
echo " mode=$MODE  size=$SIZE  run-mode=$RUN_MODE  timeout=${BENCH_TIMEOUT}s"
echo " clear-cache=$CLEAR_CACHE  clear-outputs=$CLEAR_OUTPUTS"
echo " benchmarks (${#BENCHMARKS[@]}): ${BENCHMARKS[*]}"
echo "============================================================"
echo ""

global_cleanup() {
    trap '' EXIT INT TERM
    echo ""
    echo "[global] Interrupted — running cleanup..."
    for b in "${BENCHMARKS[@]}"; do
        restore_instrumented_scripts "$TOP/evaluation/benchmarks/$b/scripts"
    done
    cleanup_overlay_mounts
    cleanup_tmp_artifacts
    exit 1
}
trap global_cleanup INT TERM

echo "[global] Running pre-run cleanup..."
cleanup_overlay_mounts
cleanup_tmp_artifacts

mkdir -p "$RESULTS_DIR"

declare -a PASSED=()
declare -a FAILED=()
declare -a SKIPPED=()
declare -a FAILED_SETUP=()

if [[ "$SKIP_SETUP" == "0" ]]; then
    echo ""
    echo "=== SETUP PHASE ==="
    for benchmark in "${BENCHMARKS[@]}"; do
        echo ""
        echo "--- Setting up: $benchmark ---"
        if ! timeout "$BENCH_TIMEOUT" bash "$TOP/evaluation/benchmarks/$benchmark/setup.sh" "--$SIZE" 2>&1; then
            echo "[setup] WARNING: setup failed for $benchmark; skipping."
            FAILED_SETUP+=("$benchmark")
        fi
    done
fi

echo ""
echo "=== EXECUTION PHASE ==="

for benchmark in "${BENCHMARKS[@]}"; do
    echo ""
    echo "--- Running: $benchmark ---"

    if [[ "${#FAILED_SETUP[@]}" -gt 0 ]] && printf '%s\n' "${FAILED_SETUP[@]}" | grep -qx "$benchmark"; then
        echo "[run] SKIPPED (setup failed)"
        SKIPPED+=("$benchmark")
        continue
    fi

    restore_instrumented_scripts "$TOP/evaluation/benchmarks/$benchmark/scripts"

    if timeout "$BENCH_TIMEOUT" bash "$TOP/evaluation/benchmarks/$benchmark/run.sh" \
        "--mode=$RUN_MODE" "--size=$SIZE" 2>&1; then
        echo "[run] PASSED: $benchmark"
        PASSED+=("$benchmark")
        mkdir -p "$RESULTS_DIR/$SIZE"
        timing_csv="$TOP/evaluation/benchmarks/$benchmark/outputs/$SIZE/timing.csv"
        if [[ -f "$timing_csv" ]]; then
            cp "$timing_csv" "$RESULTS_DIR/$SIZE/${benchmark}-time.csv"
        fi
        cache_dir="$TOP/evaluation/benchmarks/$benchmark/cache"
        if [[ -d "$cache_dir" ]]; then
            du -sb "$cache_dir" > "$RESULTS_DIR/$SIZE/${benchmark}-size.txt" 2>/dev/null || true
        fi
    else
        echo "[run] FAILED: $benchmark (exit code $?)"
        FAILED+=("$benchmark")
    fi

    cleanup_tmp_artifacts
    cleanup_overlay_mounts

    if [[ "$CLEAR_CACHE" == "1" ]]; then
        cache_dir="$TOP/evaluation/benchmarks/$benchmark/cache"
        if [[ -d "$cache_dir" ]]; then
            echo "[cleanup] Clearing cache: $cache_dir"
            rm -rf "$cache_dir"
        fi
    fi

    if [[ "$CLEAR_OUTPUTS" == "1" ]]; then
        out_dir="$TOP/evaluation/benchmarks/$benchmark/outputs"
        if [[ -d "$out_dir" ]]; then
            echo "[cleanup] Clearing outputs: $out_dir"
            rm -rf "$out_dir"
        fi
    fi
done

echo ""
echo "============================================================"
echo " SUMMARY"
echo "============================================================"
echo " Passed  (${#PASSED[@]}): ${PASSED[*]:-none}"
echo " Failed  (${#FAILED[@]}): ${FAILED[*]:-none}"
echo " Skipped (${#SKIPPED[@]}): ${SKIPPED[*]:-none}"
echo ""
echo " Results written to: $RESULTS_DIR/$SIZE"
echo "============================================================"

if [[ "${#FAILED[@]}" -gt 0 ]]; then
    exit 1
fi
exit 0
