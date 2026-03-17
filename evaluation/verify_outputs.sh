#!/bin/bash
# Verify default vs observe produce identical outputs for speedup benchmarks.
# Run from incr/: bash evaluation/verify_outputs.sh [--min]
# Uses --small by default; --min for faster run (bio, nlp-ngrams, etc.)
# Cleans up all artifacts (verify_outputs, benchmark cache/outputs, /tmp) on exit.

cd "$(dirname "$0")" || exit 1
BENCH_DIR="$(pwd)/benchmarks"
VERIFY_DIR="$(pwd)/verify_outputs"
SIZE="--small"
NO_CLEANUP=false
for arg in "$@"; do
    [[ "$arg" == "--min" ]] && SIZE="--min"
    [[ "$arg" == "--no-cleanup" ]] && NO_CLEANUP=true
done
TIMEOUT_PER_BENCH=180
command -v timeout >/dev/null 2>&1 || TIMEOUT_PER_BENCH=0

mkdir -p "$VERIFY_DIR/default" "$VERIFY_DIR/observe"

cleanup() {
    [[ "$NO_CLEANUP" == "true" ]] && return
    echo ""
    echo "Cleaning up artifacts..."
    rm -rf "$VERIFY_DIR"
    for b in beginner bio covid nginx-analysis nlp-uppercase nlp-ngrams poet spell unixfun weather word-freq; do
        sudo rm -rf "$BENCH_DIR/$b/cache" "$BENCH_DIR/$b/outputs" 2>/dev/null || true
    done
    rm -rf /tmp/sort* /tmp/tmp* /tmp/cache* /tmp/incr_bench* 2>/dev/null || true
    echo "Done."
}
trap cleanup EXIT INT TERM

run_and_save() {
    local bench=$1 mode=$2
    export INCR_OBSERVE=$([ "$mode" = "observe" ] && echo 1 || echo 0)
    sudo rm -rf "$BENCH_DIR/$bench/cache" "$BENCH_DIR/$bench/outputs" 2>/dev/null || true
    mkdir -p "$BENCH_DIR/$bench/outputs"
    if [[ "$TIMEOUT_PER_BENCH" -gt 0 ]]; then
        timeout "$TIMEOUT_PER_BENCH" bash -c "cd '$BENCH_DIR' && bash './$bench/execute.sh' $SIZE --incr-only" >/dev/null 2>&1 || true
    else
        (cd "$BENCH_DIR" && bash "./$bench/execute.sh" $SIZE --incr-only) >/dev/null 2>&1
    fi
    cp -r "$BENCH_DIR/$bench/outputs" "$VERIFY_DIR/$mode/$bench" 2>/dev/null || true
}

# Compare outputs, excluding timing.csv and .err
compare_bench() {
    local bench=$1
    local def="$VERIFY_DIR/default/$bench"
    local obs="$VERIFY_DIR/observe/$bench"
    local failed=0

    [[ ! -d "$def" ]] && echo "  No default outputs" && return 1
    [[ ! -d "$obs" ]] && echo "  No observe outputs" && return 1

    while IFS= read -r rel; do
        [[ -z "$rel" ]] && continue
        local f1="$def/$rel" f2="$obs/$rel"
        if [[ ! -f "$f2" ]]; then
            echo "  MISSING in observe: $rel"
            ((failed++)) || true
            continue
        fi
        if ! diff -q "$f1" "$f2" >/dev/null 2>&1; then
            echo "  DIFF: $rel"
            ((failed++)) || true
        fi
    done < <(find "$def" -type f 2>/dev/null | while read f; do
        rel="${f#$def/}"
        [[ "$(basename "$rel")" == "timing.csv" ]] && continue
        [[ "$rel" == *.err ]] && continue
        echo "$rel"
    done)

    return $failed
}

echo "=============================================="
echo "Verifying default vs observe output correctness"
echo "Size: $SIZE | Results: $VERIFY_DIR"
echo "=============================================="

BENCHMARKS=(beginner bio covid nginx-analysis nlp-uppercase nlp-ngrams poet spell unixfun weather word-freq)
for bench in "${BENCHMARKS[@]}"; do
    echo ""
    echo ">>> $bench"
    echo "  Running default..."
    run_and_save "$bench" "default"
    echo "  Running observe..."
    run_and_save "$bench" "observe"
    echo "  Comparing..."
    if compare_bench "$bench"; then
        echo "  OK: outputs match"
    else
        echo "  FAIL: outputs differ"
    fi
done

echo ""
echo "=============================================="
echo "Verification complete. Artifacts will be cleaned on exit."
echo "=============================================="
