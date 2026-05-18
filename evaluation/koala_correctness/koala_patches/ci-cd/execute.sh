#!/usr/bin/env bash
set -eu

BASE_DIR="$(dirname "$(readlink -f "$0")")"
TESTS_DIR="${BASE_DIR}/makeself/test"
LOGFILE="${BASE_DIR}/run_results.log"
KOALA_SHELL="${KOALA_SHELL:-bash}"
export BENCHMARK_CATEGORY="ci-cd"

selected_scripts=""
run_min=false

while [ $# -gt 0 ]; do
    case "$1" in
        --min)
            run_min=true
            shift
            ;;
        -s|--scripts)
            shift
            while [ $# -gt 0 ] && [ "$(echo "$1" | cut -c1)" != "-" ]; do
                if [ -z "$selected_scripts" ]; then
                    selected_scripts="$1"
                else
                    selected_scripts="$selected_scripts $1"
                fi
                shift
            done
            ;;
        *)
            shift
            ;;
    esac
done

should_run() {
    script_name=$1
    if [ -z "$selected_scripts" ]; then
        return 0
    fi
    for selected in $selected_scripts; do
        if [ "$selected" = "$script_name" ]; then
            return 0
        fi
    done
    return 1
}

if should_run "makeself"; then
    echo "Starting test execution..." > "${LOGFILE}"

    for test_script in "${TESTS_DIR}"/*/*.sh; do
        test_dir="$(dirname "${test_script}")"
        test_name="$(basename "${test_dir}")"
        test_log="${test_dir}/test_results.log"

        echo "Running test: ${test_name}" >> "${LOGFILE}"
        BENCHMARK_SCRIPT="$(realpath "$test_script")"
        export BENCHMARK_SCRIPT
        if $KOALA_SHELL "${test_script}" >> "${test_log}" 2>&1; then
            echo "PASS: ${test_name}" >> "${LOGFILE}"
        else
            echo "FAIL: ${test_name}" >> "${LOGFILE}"
        fi
    done

    echo "Test execution completed. Results in ${LOGFILE}"

    # Copy the PASS/FAIL summary (no temp-dir paths) to outputs/ so the
    # correctness harness can snapshot and diff it between bash and incr runs.
    mkdir -p "${BASE_DIR}/outputs"
    cp "${LOGFILE}" "${BASE_DIR}/outputs/makeself-summary.log"
fi

TOP="$(git rev-parse --show-toplevel)"
eval_dir="${TOP}/ci-cd/riker"

KOALA_SHELL=${KOALA_SHELL:-bash}

min_benchmark=(
    "xz-clang"
)

if [ "$run_min" = true ]; then
    for bench in "${min_benchmark[@]}"; do
        if should_run "$bench"; then
            script_path="$eval_dir/$bench/execute.sh"
            if [ -x "$script_path" ]; then
                export BENCHMARK_SCRIPT="$script_path"
                $KOALA_SHELL $script_path
            else
                echo "Error: $script_path not found or not executable."
                exit 1
            fi
        fi
    done
    exit 0
fi

for bench in "$eval_dir"/*; do
    bench_name="$(basename "$bench")"
    if should_run "$bench_name"; then
        export BENCHMARK_SCRIPT="$bench/execute.sh"
        $KOALA_SHELL "$bench/execute.sh"
    fi
done
