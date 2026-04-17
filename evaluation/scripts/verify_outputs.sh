#!/bin/bash
# Verify all run modes (bash, incr, incr-observe) produce identical stdout for each benchmark script.
# Run from incr/: bash evaluation/scripts/verify_outputs.sh [--min|--small] [--no-cleanup] [--run]
#
# Compares all available mode outputs under benchmarks/*/outputs/<size>/ using bash as the
# reference. If bash output is absent, the first mode found is used as reference.
# With --run, first runs: evaluation/benchmarks/run_all.sh --mode easy --run-mode all
#
# Cleans verify_outputs dir and /tmp artifacts on exit unless --no-cleanup.

EVAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INCR_ROOT="$(cd "$EVAL_DIR/.." && pwd)"
cd "$EVAL_DIR" || exit 1
BENCH_DIR="$EVAL_DIR/benchmarks"
VERIFY_DIR="$EVAL_DIR/verify_outputs"
SIZE_NAME="min"
NO_CLEANUP=false
DO_RUN=false
for arg in "$@"; do
    [[ "$arg" == "--min" ]] && SIZE_NAME="min"
    [[ "$arg" == "--small" ]] && SIZE_NAME="small"
    [[ "$arg" == "--no-cleanup" ]] && NO_CLEANUP=true
    [[ "$arg" == "--run" ]] && DO_RUN=true
done

mkdir -p "$VERIFY_DIR"

cleanup() {
    [[ "$NO_CLEANUP" == "true" ]] && return
    echo ""
    echo "Cleaning up artifacts..."
    "$EVAL_DIR/scripts/restore_sentinels.sh" 2>/dev/null || true
    rm -rf "$VERIFY_DIR"
    rm -rf /tmp/sort* /tmp/tmp* /tmp/cache* /tmp/incr_bench* 2>/dev/null || true
    echo "Done."
}
trap cleanup EXIT INT TERM

if [[ "$DO_RUN" == "true" ]]; then
    echo "Running full suite (all modes)..."
    bash "$INCR_ROOT/evaluation/benchmarks/run_all.sh" --mode easy --size "$SIZE_NAME" --run-mode all --skip-setup || true
fi

OUT_SUB="outputs/$SIZE_NAME"
fail=0
BENCHMARKS=(beginner bio covid file-mod nginx-analysis nlp-ngrams nlp-uppercase poet spell unixfun weather word-freq)

echo "=============================================="
echo "Verifying all mode outputs ($OUT_SUB)"
echo "=============================================="

for bench in "${BENCHMARKS[@]}"; do
    od="$BENCH_DIR/$bench/$OUT_SUB"
    if [[ ! -d "$od" ]]; then
        echo ">>> $bench: skip (no $OUT_SUB)"
        continue
    fi
    echo ""
    echo ">>> $bench"
    bench_fail=0
    shopt -s nullglob

    # Collect unique script basenames from all *.*.out files
    declare -A scripts_seen
    for f in "$od"/*.out; do
        [[ -f "$f" ]] || continue
        fname=$(basename "$f")
        # strip trailing .<mode>.out to get script name
        script_name="${fname%.*}"      # strips .out
        script_name="${script_name%.*}" # strips .<mode>
        scripts_seen["$script_name"]=1
    done

    for script_name in $(echo "${!scripts_seen[@]}" | tr ' ' '\n' | sort); do
        # Collect all mode outputs for this script
        modes=()
        for f in "$od/${script_name}".*.out; do
            [[ -f "$f" ]] || continue
            fname=$(basename "$f")
            mode="${fname#"${script_name}."}"
            mode="${mode%.out}"
            modes+=("$mode")
        done

        [[ ${#modes[@]} -lt 2 ]] && continue  # need at least 2 modes to compare

        # Use bash as reference if present, else first mode alphabetically
        ref_mode="bash"
        if [[ ! -f "$od/${script_name}.bash.out" ]]; then
            ref_mode=$(echo "${modes[@]}" | tr ' ' '\n' | sort | head -1)
        fi
        ref_file="$od/${script_name}.${ref_mode}.out"

        for mode in $(echo "${modes[@]}" | tr ' ' '\n' | sort); do
            [[ "$mode" == "$ref_mode" ]] && continue
            cmp_file="$od/${script_name}.${mode}.out"
            if ! diff -q "$ref_file" "$cmp_file" >/dev/null 2>&1; then
                echo "  DIFF: ${script_name}.${ref_mode}.out vs ${script_name}.${mode}.out"
                diff "$ref_file" "$cmp_file" | head -15
                bench_fail=1
            fi
        done
    done
    unset scripts_seen

    shopt -u nullglob
    if [[ "$bench_fail" -eq 0 ]]; then
        echo "  OK"
    else
        echo "  FAIL"
        fail=1
    fi
done

echo ""
echo "=============================================="
if [[ "$fail" -eq 0 ]]; then
    echo "All mode outputs match."
else
    echo "Some outputs differ or were missing."
    exit 1
fi
