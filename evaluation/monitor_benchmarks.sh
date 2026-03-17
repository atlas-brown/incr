#!/bin/bash
# Poll and display benchmark status. Run in a separate terminal.
# Usage: bash monitor_benchmarks.sh [--loop]
# Run from incr/: bash evaluation/monitor_benchmarks.sh

cd "$(dirname "$0")" || exit 1
BENCH_DIR="$(pwd)/benchmarks"
LOG_DIR="$(pwd)/parallel_logs"
RESULTS_DIR="$(pwd)/run_results_parallel"

# Use results to infer benchmarks (so --skip-dpt works: dpt won't be in results)
BENCHMARKS=(beginner bio covid dpt nginx-analysis nlp-uppercase nlp-ngrams poet spell unixfun weather word-freq)

status_of() {
    local bench=$1
    local mode=$2
    local log="$LOG_DIR/${bench}_${mode}.log"
    local timing="$RESULTS_DIR/$mode/${bench}-time.csv"
    if [[ -f "$timing" ]]; then
        local total=$(awk -F, 'NR>1 {s+=$3} END {printf "%.1f", s+0}' "$timing" 2>/dev/null)
        local lines=$(wc -l < "$timing" 2>/dev/null)
        echo "DONE (${total}s, $((lines-1)) scripts)"
    elif [[ -f "$log" ]] && [[ $(stat -c %Y "$log" 2>/dev/null || stat -f %m "$log" 2>/dev/null) -gt $(($(date +%s) - 120)) ]]; then
        echo "RUNNING"
    elif [[ -f "$log" ]]; then
        if grep -q "DONE" "$log" 2>/dev/null; then
            echo "DONE (no timing?)"
        else
            echo "RUNNING?"
        fi
    else
        echo "pending"
    fi
}

verify_outputs() {
    local bench=$1
    local out_dir="$BENCH_DIR/$bench/outputs"
    case "$bench" in
        dpt)
            local f="$out_dir/db.incr.txt"
            if [[ -f "$f" ]]; then
                local n=$(wc -l < "$f" 2>/dev/null)
                [[ $n -gt 0 ]] && echo "dpt OK ($n lines)" || echo "dpt BAD (empty db.incr.txt)"
            else
                echo "dpt ? (no outputs yet)"
            fi
            ;;
        bio)
            if [[ -d "$out_dir" ]]; then
                local n=$(find "$out_dir" -type f 2>/dev/null | wc -l)
                [[ $n -gt 0 ]] && echo "bio OK ($n files)" || echo "bio BAD (no output files)"
            else
                echo "bio ? (no outputs yet)"
            fi
            ;;
        *)
            if [[ -f "$out_dir/timing.csv" ]]; then
                local n=$(wc -l < "$out_dir/timing.csv" 2>/dev/null)
                echo "OK ($((n-1)) scripts)"
            else
                echo "? (no timing)"
            fi
            ;;
    esac
}

show_status() {
    clear
    echo "========== Benchmark Status $(date) =========="
    echo ""
    printf "%-16s %-25s %-25s %-20s\n" "Benchmark" "Default" "Observe" "Verify"
    echo "--------------------------------------------------------------------------------"
    for bench in "${BENCHMARKS[@]}"; do
        local def=$(status_of "$bench" "default")
        local obs=$(status_of "$bench" "observe")
        local ver=$(verify_outputs "$bench")
        printf "%-16s %-25s %-25s %-20s\n" "$bench" "$def" "$obs" "$ver"
    done
    echo ""
    echo "Logs: $LOG_DIR/"
    echo "Results: $RESULTS_DIR/"
    echo ""
    # Show recent errors from any log
    echo "--- Recent errors (last 5) ---"
    grep -h -l -i "error\|fail\|ENOENT\|ModuleNotFoundError\|command not found" "$LOG_DIR"/*.log 2>/dev/null | head -3 | while read f; do
        echo ">>> $(basename "$f")"
        grep -i "error\|fail\|ENOENT\|ModuleNotFoundError\|command not found" "$f" 2>/dev/null | tail -2
    done
    echo ""
}

if [[ "$1" == "--loop" ]]; then
    while true; do
        show_status
        sleep 60
    done
else
    show_status
fi
