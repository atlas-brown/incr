#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"
TOP="$(git rev-parse --show-toplevel)"
INCR="$TOP/incr.sh"
export INPUT="$TOP/evaluation/war-and-peace/book-large.txt"

baseline_file="$(mktemp)"
incr_cold_file="$(mktemp)"
incr_warm_file="$(mktemp)"
cleanup() {
    rm -f "$baseline_file" "$incr_cold_file" "$incr_warm_file"
}
trap cleanup EXIT

echo "Running baseline..." >&2
start="$(date +%s%3N)"
bash ./count-freq.sh >"$baseline_file"
elapsed=$(( $(date +%s%3N) - start ))
echo "Baseline elapsed: ${elapsed}ms" >&2

echo "Running incr (cold start)..." >&2
start="$(date +%s%3N)"
"$INCR" count-freq.sh >"$incr_cold_file"
elapsed=$(( $(date +%s%3N) - start ))
echo "Incr cold elapsed: ${elapsed}ms" >&2

echo "Running incr (incremental replay)..." >&2
start="$(date +%s%3N)"
"$INCR" count-freq.sh >"$incr_warm_file"
elapsed=$(( $(date +%s%3N) - start ))
echo "Incr warm elapsed: ${elapsed}ms" >&2

if diff -u "$baseline_file" "$incr_warm_file"; then
    echo "Baseline and warm incr outputs match." >&2
else
    echo "Baseline and warm incr outputs differ." >&2
    exit 1
fi

if diff -u "$baseline_file" "$incr_cold_file"; then
    echo "Baseline and cold incr outputs match." >&2
else
    echo "Baseline and cold incr outputs differ." >&2
    exit 1
fi
