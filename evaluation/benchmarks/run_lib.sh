#!/bin/bash
# Shared helpers for benchmark run.sh (and run_all.sh).

BENCHMARK_SCRIPTS_OVERRIDE=()

# Sets RUN_MODE, RUN_SIZE, BENCHMARK_SCRIPTS_OVERRIDE. Legacy: bash|incr|both|incr-observe|all, min|small|full.
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
  --mode=bash|incr|both|incr-observe|all   default: both
  --size=min|small|full   default: small
  --scripts=a.sh,b.sh     run only these script basenames (files under scripts/)
  incr = try+strace (INCR_OBSERVE=0); incr-observe = observe (INCR_OBSERVE=1)
  all = bash, then incr, then incr-observe per script
Legacy: bash|incr|both|incr-observe|all and min|small|full as bare words also work.
EOF
                exit 0
                ;;
            bash|incr|both|incr-observe|all) RUN_MODE=$arg ;;
            min|small|full) RUN_SIZE=$arg ;;
        esac
    done
}

# SCRIPTS from defaults or --scripts=; exit 1 if a basename is missing under script_dir.
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
    local mounts=()
    local mnt

    if command -v findmnt >/dev/null 2>&1; then
        while IFS= read -r mnt; do
            [[ -z "$mnt" ]] && continue
            case "$mnt" in
                /tmp/*.try-*|/tmp/incr_cache/sandbox_*|/tmp/incr_cache/sandbox_*/temproot/*|"$TOP"/evaluation/benchmarks/*/cache/sandbox_*|"$TOP"/evaluation/benchmarks/*/cache/sandbox_*/temproot/*)
                    mounts+=("$mnt")
                    ;;
            esac
        done < <(findmnt -rn -o TARGET 2>/dev/null)
    else
        while IFS= read -r mnt; do
            [[ -z "$mnt" ]] && continue
            case "$mnt" in
                /tmp/*.try-*|/tmp/incr_cache/sandbox_*|/tmp/incr_cache/sandbox_*/temproot/*|"$TOP"/evaluation/benchmarks/*/cache/sandbox_*|"$TOP"/evaluation/benchmarks/*/cache/sandbox_*/temproot/*)
                    mounts+=("$mnt")
                    ;;
            esac
        done < <(mount 2>/dev/null | awk '{print $3}')
    fi

    if [[ ${#mounts[@]} -eq 0 ]]; then
        return
    fi

    printf '%s\n' "${mounts[@]}" | awk '{ print length, $0 }' | sort -rn | cut -d' ' -f2- | while IFS= read -r mnt; do
        [[ -z "$mnt" ]] && continue
        sudo umount "$mnt" 2>/dev/null || sudo umount -l "$mnt" 2>/dev/null || true
    done
}

# Best-effort /tmp cleanup (incr try/sort temp files).
cleanup_tmp_artifacts() {
    rm -f /tmp/*.try-* 2>/dev/null || true
    rm -rf /tmp/sort.* 2>/dev/null || true
    find /tmp -maxdepth 1 -type f -name 'sort*' 2>/dev/null | while IFS= read -r f; do
        rm -f "$f"
    done || true
}

run_benchmark_scripts() {
    mkdir -p "$OUTPUT_DIR"
    echo "mode,script,time_sec" > "$TIME_FILE"

    local cache_dir="$BENCHMARK_DIR/cache"
    local scripts=("$@")
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

        # stdin from pipe never closes in some runners; ffmpeg etc. would block.
        if [[ "$mode" == "incr" ]]; then
            { time env INCR_OBSERVE=0 "$TOP/incr.sh" "$SCRIPT_DIR/$script" "$cache_dir" \
                < /dev/null >"$out_file" 2>"$err_file"; } 2>"$time_log"
        elif [[ "$mode" == "incr-observe" ]]; then
            { time env INCR_OBSERVE=1 "$TOP/incr.sh" "$SCRIPT_DIR/$script" "$cache_dir" \
                < /dev/null >"$out_file" 2>"$err_file"; } 2>"$time_log"
        else
            { time bash "$SCRIPT_DIR/$script" < /dev/null >"$out_file" 2>"$err_file"; } 2>"$time_log"
        fi
        rc=$?

        local time_output
        time_output=$(cat "$time_log")
        rm -f "$time_log"

        # grep uses 1 for no match; warn only on other non-zero exits.
        if [[ "$rc" -ne 0 && "$rc" -ne 1 ]]; then
            echo "[run] WARNING: $mode $script exited $rc (see $err_file)" >&2
        fi

        local elapsed
        elapsed=$(echo "$time_output" | grep real | awk '{print $2}' |
            awk -Fm '{if (NF==2){sub("s","",$2); print ($1*60)+$2}else{gsub("s","",$1); print $1}}')

        echo "$mode,$script,$elapsed" >> "$TIME_FILE"
        echo "[run] $mode $script: ${elapsed}s"

        cleanup_tmp_artifacts
    }

    # Per-script bash then incr (not all bash first — avoids huge stdout filling disk).
    if [[ "$RUN_MODE" == "both" ]]; then
        for script in "${scripts[@]}"; do
            echo "[run] Running $script with bash..."
            measure "bash" "$script"
            echo "[run] Running $script with incr..."
            measure "incr" "$script"
        done
    elif [[ "$RUN_MODE" == "all" ]]; then
        for script in "${scripts[@]}"; do
            echo "[run] Running $script with bash..."
            measure "bash" "$script"
            echo "[run] Running $script with incr..."
            measure "incr" "$script"
            echo "[run] Running $script with incr-observe..."
            measure "incr-observe" "$script"
        done
    elif [[ "$RUN_MODE" == "bash" ]]; then
        for script in "${scripts[@]}"; do
            echo "[run] Running $script with bash..."
            measure "bash" "$script"
        done
    elif [[ "$RUN_MODE" == "incr-observe" ]]; then
        for script in "${scripts[@]}"; do
            echo "[run] Running $script with incr-observe..."
            measure "incr-observe" "$script"
        done
    else
        for script in "${scripts[@]}"; do
            echo "[run] Running $script with incr..."
            measure "incr" "$script"
        done
    fi

}
