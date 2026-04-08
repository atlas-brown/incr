#!/bin/bash
# Diff bash/incr stdout; empty outputs; disk-full in *.err; htslib-style lines in *.err (skip file-mod).
# Usage: [--size min|small|full] [--mode easy|full]. Default easy+min (same as run_all.sh).
set -uo pipefail
cd "$(dirname "$0")" || exit 1

TOP=$(git rev-parse --show-toplevel)
SIZE=min
MODE=easy

for arg in "$@"; do
    case "$arg" in
        --size=*) SIZE="${arg#--size=}" ;;
        --mode=*) MODE="${arg#--mode=}" ;;
        min|small|full) SIZE=$arg ;;
        easy|full) MODE=$arg ;;
    esac
done

EASY_BENCHMARKS=(
    beginner bio covid file-mod nginx-analysis
    nlp-ngrams nlp-uppercase poet spell unixfun weather word-freq
)
COMPLEX_BENCHMARKS=(dpt image-annotation)

if [[ "$MODE" == "full" ]]; then
    BENCHMARKS=("${EASY_BENCHMARKS[@]}" "${COMPLEX_BENCHMARKS[@]}")
else
    BENCHMARKS=("${EASY_BENCHMARKS[@]}")
fi

overall_pass=true
total_checked=0
total_mismatched=0
total_skipped=0

echo "verify_outputs: size=$SIZE mode=$MODE"
echo ""

for benchmark in "${BENCHMARKS[@]}"; do
    out_dir="$TOP/evaluation/benchmarks/$benchmark/outputs/$SIZE"
    if [[ ! -d "$out_dir" ]]; then
        echo "SKIP  $benchmark  (no outputs/$SIZE)"
        (( total_skipped++ )) || true
        continue
    fi

    for err in "$out_dir"/*.err; do
        [[ -f "$err" ]] || continue
        if grep -qi 'no space left on device' "$err" 2>/dev/null; then
            echo "FAIL  $benchmark  ($(basename "$err"): disk full — free space and re-run)"
            overall_pass=false
        fi
    done

    bench_pass=true
    bench_checked=0
    bench_mismatched=0
    bench_skipped=0
    mismatch_details=""

    for bash_out in "$out_dir"/*.bash.out; do
        [[ -f "$bash_out" ]] || continue
        script=$(basename "$bash_out" .bash.out)
        incr_out="$out_dir/${script}.incr.out"
        bash_err="$out_dir/${script}.bash.err"
        incr_err="$out_dir/${script}.incr.err"

        if [[ ! -f "$incr_out" ]]; then
            (( bench_skipped++ )) || true
            continue
        fi

        bs=$(wc -c <"$bash_out")
        is=$(wc -c <"$incr_out")
        if [[ "$bs" -eq 0 && "$is" -gt 0 ]]; then
            overall_pass=false
            bench_pass=false
            mismatch_details+="    EMPTY bash, non-empty incr: $script\n"
            (( bench_mismatched++ )) || true
            (( total_mismatched++ )) || true
            continue
        fi
        if [[ "$is" -eq 0 && "$bs" -gt 0 ]]; then
            overall_pass=false
            bench_pass=false
            mismatch_details+="    EMPTY incr, non-empty bash: $script (check $incr_err)\n"
            (( bench_mismatched++ )) || true
            (( total_mismatched++ )) || true
            continue
        fi

        (( bench_checked++ )) || true
        (( total_checked++ )) || true

        if ! diff -q "$bash_out" "$incr_out" &>/dev/null; then
            bench_pass=false
            overall_pass=false
            (( bench_mismatched++ )) || true
            (( total_mismatched++ )) || true
            mismatch_details+="    MISMATCH: $script\n"
            diff_line=$(diff "$bash_out" "$incr_out" | head -5 | sed 's/^/      /')
            mismatch_details+="$diff_line\n"
        fi
    done

    if [[ $bench_checked -eq 0 && $bench_skipped -gt 0 ]]; then
        echo "SKIP  $benchmark  (need incr outputs; use --run-mode both)"
        (( total_skipped++ )) || true
    elif [[ $bench_checked -eq 0 ]]; then
        echo "SKIP  $benchmark  (no .bash.out files)"
        (( total_skipped++ )) || true
    elif $bench_pass; then
        echo "PASS  $benchmark  ($bench_checked scripts)"
    else
        echo "FAIL  $benchmark  ($bench_mismatched/$bench_checked)"
        printf "%b" "$mismatch_details"
    fi
done

echo ""
echo "checked=$total_checked mismatched=$total_mismatched skipped=$total_skipped"

if [[ "$total_checked" -eq 0 ]]; then
    echo "Nothing to verify (no paired .bash.out/.incr.out). Re-run with outputs present." >&2
    exit 1
fi

# htslib/samtools failures in *.err (stdout can still match). file-mod skipped (ffmpeg stderr).
stderr_fail=false
for benchmark in "${BENCHMARKS[@]}"; do
    [[ "$benchmark" == "file-mod" ]] && continue
    out_dir="$TOP/evaluation/benchmarks/$benchmark/outputs/$SIZE"
    [[ -d "$out_dir" ]] || continue
    for err in "$out_dir"/*.err; do
        [[ -f "$err" ]] || continue
        [[ -s "$err" ]] || continue
        if grep -E -q '\[E::hts_open|Failed to open file|failed to open .*: No such file or directory|cannot be usefully indexed' "$err" 2>/dev/null; then
            echo "FAIL  stderr indicates missing/bad inputs: $benchmark/$(basename "$err")" >&2
            head -5 "$err" | sed 's/^/  /' >&2
            stderr_fail=true
        fi
    done
done

if $overall_pass && [[ "$stderr_fail" == false ]]; then
    echo "OK: all outputs match"
    exit 0
fi
[[ "$stderr_fail" == true ]] && echo "FAIL: stderr checks (missing/bad inputs?)" >&2
! $overall_pass && echo "FAIL: mismatches or disk errors" >&2
exit 1
