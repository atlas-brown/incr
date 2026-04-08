#!/bin/bash
# Shared helpers for benchmark run.sh (source after TOP and BENCHMARK_DIR).

# Set by parse_benchmark_run_sh_args; empty means use each benchmark's default script list.
BENCHMARK_SCRIPTS_OVERRIDE=()

# Parse shared flags for per-benchmark run.sh. Sets RUN_MODE, RUN_SIZE,
# BENCHMARK_SCRIPTS_OVERRIDE (comma list from --scripts=).
# Legacy positional words still work: bash|incr|both, min|small|full.
parse_benchmark_run_sh_args() {
    RUN_MODE=both
    RUN_SIZE=small
    BENCHMARK_SCRIPTS_OVERRIDE=()
    local arg _list _parts t
    for arg in "$@"; do
        case "$arg" in
            --mode=*) RUN_MODE="${arg#--mode=}" ;;
            --size=*) RUN_SIZE="${arg#--size=}" ;;
            --scripts=*)
                _list="${arg#--scripts=}"
                IFS=',' read -ra _parts <<< "$_list"
                for t in "${_parts[@]}"; do
                    t="${t#"${t%%[![:space:]]*}"}"
                    t="${t%"${t##*[![:space:]]}"}"
                    [[ -n "$t" ]] && BENCHMARK_SCRIPTS_OVERRIDE+=("$t")
                done
                ;;
            --mode|--size) ;;
            --help|-h)
                cat <<'EOF'
Per-benchmark run.sh:
  --mode=bash|incr|both   default: both
  --size=min|small|full   default: small
  --scripts=a.sh,b.sh     run only these script basenames (files under scripts/)
Legacy: bash|incr|both and min|small|full as bare words also work.
EOF
                exit 0
                ;;
            bash|incr|both) RUN_MODE=$arg ;;
            min|small|full) RUN_SIZE=$arg ;;
        esac
    done
}

# Build global SCRIPTS from defaults or --scripts override. Exits 1 if a file is missing.
# Usage: finalize_benchmark_scripts "$SCRIPT_DIR" "${DEFAULT_SCRIPTS[@]}"
finalize_benchmark_scripts() {
    local script_dir=$1
    shift
    local defaults=("$@")
    if [[ ${#BENCHMARK_SCRIPTS_OVERRIDE[@]} -eq 0 ]]; then
        SCRIPTS=("${defaults[@]}")
        return
    fi
    SCRIPTS=()
    local s
    for s in "${BENCHMARK_SCRIPTS_OVERRIDE[@]}"; do
        if [[ ! -f "$script_dir/$s" ]]; then
            echo "[run] ERROR: no script file: $script_dir/$s" >&2
            echo "[run] Pass basenames only, e.g. --scripts=spell-5.sh" >&2
            exit 1
        fi
        SCRIPTS+=("$s")
    done
}

restore_instrumented_scripts() {
    local script_dir="${1:-}"
    [[ -z "$script_dir" ]] && return
    for sentinel in "$script_dir"/*.incr_orig; do
        [[ -f "$sentinel" ]] || continue
        local original_script="${sentinel%.incr_orig}"
        echo "[cleanup] Restoring $original_script from sentinel"
        cp "$sentinel" "$original_script"
        rm -f "$sentinel"
    done
    for sidecar in "$script_dir"/incr_script_*.sh; do
        [[ -f "$sidecar" ]] || continue
        echo "[cleanup] Removing stale sidecar: $sidecar"
        rm -f "$sidecar"
    done
}

cleanup_overlay_mounts() {
    local stale
    stale=$(mount 2>/dev/null | grep "type overlay" | grep "/tmp\." | awk '{print $3}' || true)
    if [[ -n "$stale" ]]; then
        echo "$stale" | while IFS= read -r mnt; do
            [[ -z "$mnt" ]] && continue
            echo "[cleanup] Unmounting stale overlay: $mnt"
            sudo umount "$mnt" 2>/dev/null && echo "[cleanup] OK" || true
        done
    fi
}

# Best-effort scrub of incr/try/sort leftovers under /tmp (benchmark-dedicated machines).
cleanup_tmp_artifacts() {
    rm -f /tmp/*.try-* 2>/dev/null || true
    rm -rf /tmp/sort.* 2>/dev/null || true
    find /tmp -maxdepth 1 -type f -name 'sort*' 2>/dev/null | while IFS= read -r f; do
        rm -f "$f"
    done || true
}

# Args: script basenames. Needs TOP, BENCHMARK_DIR, SCRIPT_DIR, OUTPUT_DIR, RUN_MODE, TIME_FILE.
run_benchmark_scripts() {
    mkdir -p "$OUTPUT_DIR"
    echo "mode,script,time_sec" > "$TIME_FILE"

    local cache_dir="$BENCHMARK_DIR/cache"
    local scripts=("$@")
    # Use default system temp (/tmp) for sort(1), mktemp, etc. so paths match what incr expects.
    local old_tmp="${TMPDIR:-}"
    export TMPDIR=/tmp
    restore_tmpdir() {
        trap - RETURN
        if [[ -n "$old_tmp" ]]; then
            export TMPDIR="$old_tmp"
        else
            unset TMPDIR
        fi
    }
    trap restore_tmpdir RETURN

    measure() {
        local mode=$1
        local script=$2
        local out_file="$OUTPUT_DIR/${script}.${mode}.out"
        local err_file="$OUTPUT_DIR/${script}.${mode}.err"
        local time_log rc=0

        export mode="$mode"
        time_log=$(mktemp -p /tmp "incr-bench-time.XXXXXX") || return 1

        if [[ "$mode" == "incr" ]]; then
            { time "$TOP/incr.sh" "$SCRIPT_DIR/$script" "$cache_dir" \
                < /dev/null >"$out_file" 2>"$err_file"; } 2>"$time_log"
        else
            { time bash "$SCRIPT_DIR/$script" >"$out_file" 2>"$err_file"; } 2>"$time_log"
        fi
        rc=$?

        local time_output
        time_output=$(cat "$time_log")
        rm -f "$time_log"

        if [[ "$rc" -ne 0 ]]; then
            echo "[run] WARNING: $mode $script exited $rc (see $err_file)" >&2
        fi

        local elapsed
        elapsed=$(echo "$time_output" | grep real | awk '{print $2}' |
            awk -Fm '{if (NF==2){sub("s","",$2); print ($1*60)+$2}else{gsub("s","",$1); print $1}}')

        echo "$mode,$script,$elapsed" >> "$TIME_FILE"
        echo "[run] $mode $script: ${elapsed}s"

        cleanup_tmp_artifacts
    }

    # With mode=both, run bash then incr per script (not all bash then all incr).
    # All-bash-first fills the disk with huge stdout before incr runs heavy sorts.
    if [[ "$RUN_MODE" == "both" ]]; then
        for script in "${scripts[@]}"; do
            echo "[run] Running $script with bash..."
            measure "bash" "$script"
            echo "[run] Running $script with incr..."
            measure "incr" "$script"
        done
    elif [[ "$RUN_MODE" == "bash" ]]; then
        for script in "${scripts[@]}"; do
            echo "[run] Running $script with bash..."
            measure "bash" "$script"
        done
    else
        for script in "${scripts[@]}"; do
            echo "[run] Running $script with incr..."
            measure "incr" "$script"
        done
    fi

}
