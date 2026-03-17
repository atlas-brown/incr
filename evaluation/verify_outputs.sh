#!/bin/bash
# Verify default vs observe produce identical outputs for speedup benchmarks.
# Run from incr/: bash evaluation/verify_outputs.sh [--min]
# Uses --small by default; --min for faster run (bio, nlp-ngrams, etc.)

cd "$(dirname "$0")" || exit 1
BENCH_DIR="$(pwd)/benchmarks"
VERIFY_DIR="$(pwd)/verify_outputs"
SIZE="--small"
[[ "$1" == "--min" ]] && SIZE="--min"

mkdir -p "$VERIFY_DIR/default" "$VERIFY_DIR/observe"

run_and_save() {
    local bench=$1 mode=$2
    export INCR_OBSERVE=$([ "$mode" = "observe" ] && echo 1 || echo 0)
    sudo rm -rf "$BENCH_DIR/$bench/cache" "$BENCH_DIR/$bench/outputs" 2>/dev/null || true
    mkdir -p "$BENCH_DIR/$bench/outputs"
    (cd "$BENCH_DIR" && bash "./$bench/execute.sh" $SIZE --incr-only) >/dev/null 2>&1
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
        [[ "$rel" == "timing.csv" ]] && continue
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
echo "Verification complete. Inspect $VERIFY_DIR for details."
echo "=============================================="
