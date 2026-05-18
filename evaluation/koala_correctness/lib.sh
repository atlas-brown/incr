#!/bin/bash
# Shared helpers for the koala-correctness harness.
# Sourced by run.sh and by each benchmark's runner under benchmarks/<name>/run.sh.

# Resolve absolute paths once.
KC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INCR_REPO="$(cd "$KC_DIR/../.." && pwd)"
KOALA_REPO="$(cd "$INCR_REPO/../koala" && pwd)"
export KC_DIR INCR_REPO KOALA_REPO

KC_WORK_DIR="$KC_DIR/work"
KC_RESULTS_DIR="$KC_DIR/results"
KC_INCR_SHELL="$KC_DIR/incr_shell.sh"
KC_PATCHES_DIR="$KC_DIR/koala_patches"
KC_PATCH_APPLIED=0

# State for cleanup. Populated as benchmarks run; never cleared.
declare -ga KC_VISITED_BENCHMARKS=()
declare -ga KC_VISITED_CACHE_DIRS=()

kc_log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }
kc_warn() { printf '[%s] WARN: %s\n' "$(date +%H:%M:%S)" "$*" >&2; }
kc_err() { printf '[%s] ERROR: %s\n' "$(date +%H:%M:%S)" "$*" >&2; }

# Mark a benchmark / cache directory as touched so aggressive_cleanup can find them
# even if the run is interrupted before we finish.
kc_remember_benchmark() {
    local name=$1
    for existing in "${KC_VISITED_BENCHMARKS[@]:-}"; do
        [[ "$existing" == "$name" ]] && return 0
    done
    KC_VISITED_BENCHMARKS+=("$name")
}

kc_remember_cache_dir() {
    local dir=$1
    for existing in "${KC_VISITED_CACHE_DIRS[@]:-}"; do
        [[ "$existing" == "$dir" ]] && return 0
    done
    KC_VISITED_CACHE_DIRS+=("$dir")
}

# Overlay our koala_patches/ over the target koala repo. Idempotent — safe to
# call multiple times. Originals are preserved as <file>.kc_orig so
# kc_revert_koala_patches can restore them.
kc_apply_koala_patches() {
    [[ -d "$KC_PATCHES_DIR" ]] || return 0
    if ! "$KC_PATCHES_DIR/apply.sh" --apply "$KOALA_REPO" >/dev/null; then
        kc_warn "koala_patches: --apply reported errors (see apply.sh --check)"
    fi
    KC_PATCH_APPLIED=1
}

# Restore koala files from <file>.kc_orig backups left by kc_apply_koala_patches.
kc_revert_koala_patches() {
    [[ "$KC_PATCH_APPLIED" -eq 1 ]] || return 0
    [[ -d "$KC_PATCHES_DIR" ]] || return 0
    "$KC_PATCHES_DIR/apply.sh" --revert "$KOALA_REPO" >/dev/null || true
    KC_PATCH_APPLIED=0
}

# Restore koala/<b>/scripts/* from any *.incr_orig sentinels left by incr.sh and
# remove any incr_script_*.sh sidecars. Safe to call repeatedly.
kc_restore_instrumented_scripts() {
    local script_dir=$1
    [[ -d "$script_dir" ]] || return 0
    local sentinel original_script sidecar
    for sentinel in "$script_dir"/*.incr_orig; do
        [[ -f "$sentinel" ]] || continue
        original_script="${sentinel%.incr_orig}"
        cp "$sentinel" "$original_script"
        rm -f "$sentinel"
    done
    for sidecar in "$script_dir"/incr_script_*.sh; do
        [[ -f "$sidecar" ]] || continue
        rm -f "$sidecar"
    done
}

# umount any OverlayFS sandboxes left behind under our work/ tree or under
# /tmp by incr's try mechanism. Idempotent.
kc_cleanup_overlay_mounts() {
    local listed=() mnt
    if command -v findmnt >/dev/null 2>&1; then
        while IFS= read -r mnt; do
            [[ -z "$mnt" ]] && continue
            case "$mnt" in
                /tmp/*.try-*|"$KC_WORK_DIR"/*/cache/sandbox_*|"$KC_WORK_DIR"/*/cache/sandbox_*/temproot/*)
                    listed+=("$mnt") ;;
            esac
        done < <(findmnt -rn -o TARGET 2>/dev/null)
    else
        while IFS= read -r mnt; do
            [[ -z "$mnt" ]] && continue
            case "$mnt" in
                /tmp/*.try-*|"$KC_WORK_DIR"/*/cache/sandbox_*|"$KC_WORK_DIR"/*/cache/sandbox_*/temproot/*)
                    listed+=("$mnt") ;;
            esac
        done < <(mount 2>/dev/null | awk '{print $3}')
    fi
    [[ ${#listed[@]} -eq 0 ]] && return 0
    printf '%s\n' "${listed[@]}" | awk '{print length, $0}' | sort -rn | cut -d' ' -f2- |
        while IFS= read -r mnt; do
            [[ -z "$mnt" ]] && continue
            sudo umount "$mnt" 2>/dev/null || sudo umount -l "$mnt" 2>/dev/null || true
        done
}

# Remove incr's /tmp scratch (try sandboxes, sort spill files).
kc_cleanup_tmp_artifacts() {
    rm -rf /tmp/*.try-* 2>/dev/null || true
    rm -rf /tmp/sort.* 2>/dev/null || true
}

# Single idempotent teardown. Wired to EXIT/INT/TERM/HUP in run.sh and called
# explicitly between benchmarks. Safe to call any number of times.
kc_aggressive_cleanup() {
    local name dir sentinel
    for name in "${KC_VISITED_BENCHMARKS[@]:-}"; do
        # Recursively restore scripts across the entire benchmark tree. Some
        # benchmarks (ci-cd) spread scripts across nested subdirectories rather
        # than a single scripts/ directory, so we use find instead of a fixed-
        # depth glob.
        while IFS= read -r sentinel; do
            [[ -f "$sentinel" ]] || continue
            cp "$sentinel" "${sentinel%.incr_orig}" 2>/dev/null || true
            rm -f "$sentinel"
        done < <(find "$KOALA_REPO/$name" -name '*.incr_orig' 2>/dev/null)
        find "$KOALA_REPO/$name" -name 'incr_script_*.sh' -delete 2>/dev/null || true
    done
    kc_cleanup_overlay_mounts
    for dir in "${KC_VISITED_CACHE_DIRS[@]:-}"; do
        [[ -z "$dir" ]] && continue
        if [[ -d "$dir" ]]; then
            rm -rf "$dir" 2>/dev/null || sudo rm -rf "$dir" 2>/dev/null || true
        fi
    done
    if [[ -d "$KC_WORK_DIR" ]]; then
        find "$KC_WORK_DIR" -maxdepth 3 -type d -name cache -prune -exec rm -rf {} + 2>/dev/null || true
    fi
    kc_cleanup_tmp_artifacts
}

# Check that every named binary is on PATH; print missing names on stdout.
kc_missing_deps() {
    local missing=() c
    for c in "$@"; do
        command -v "$c" >/dev/null 2>&1 || missing+=("$c")
    done
    printf '%s\n' "${missing[@]:-}" | sed '/^$/d'
}

# Best-effort `koala/<b>/clean.sh`. Some clean.sh use sudo internally; we tolerate
# failure because outputs/ are also wiped explicitly below.
kc_koala_clean() {
    local name=$1
    local bench_dir="$KOALA_REPO/$name"
    [[ -x "$bench_dir/clean.sh" ]] || return 0
    ( cd "$bench_dir" && bash ./clean.sh ) >/dev/null 2>&1 || true
}

# Fetch min-size inputs if not already present. Each koala fetch.sh is
# idempotent for sizes that already exist, so calling unconditionally is safe.
kc_koala_fetch() {
    local name=$1 size=$2
    local bench_dir="$KOALA_REPO/$name"
    [[ -x "$bench_dir/fetch.sh" ]] || return 0
    ( cd "$bench_dir" && bash ./fetch.sh "--$size" )
}

# Run koala/<b>/execute.sh under bash or incr for one (benchmark, mode, size).
# Captures stdout/stderr, enforces timeout, snapshots outputs/. Echoes the
# resulting status (PASS / EMPTY / TIMEOUT / FAIL) on stdout.
kc_run_mode() {
    local name=$1
    local mode=$2
    local size=$3
    local timeout_s=$4
    shift 4
    local -a script_args=("$@")

    local bench_dir="$KOALA_REPO/$name"
    local work_dir="$KC_WORK_DIR/$name/$size"
    local snapshot_dir="$work_dir/$mode"
    local cache_dir="$work_dir/cache"
    local stdout_log="$work_dir/$mode.stdout"
    local stderr_log="$work_dir/$mode.stderr"
    local time_log="$work_dir/$mode.time"

    mkdir -p "$work_dir"
    rm -rf "$snapshot_dir"
    mkdir -p "$snapshot_dir"
    rm -rf "$bench_dir/outputs"
    mkdir -p "$bench_dir/outputs"

    kc_restore_instrumented_scripts "$bench_dir/scripts"

    local rc=0
    if [[ "$mode" == "incr" ]]; then
        kc_remember_cache_dir "$cache_dir"
        rm -rf "$cache_dir"
        mkdir -p "$cache_dir"
        (
            cd "$bench_dir"
            export KOALA_SHELL="$KC_INCR_SHELL"
            export INCR_REPO
            export INCR_CACHE_DIR="$cache_dir"
            timeout --kill-after=15s "${timeout_s}s" \
                bash ./execute.sh "--$size" "${script_args[@]}" \
                </dev/null >"$stdout_log" 2>"$stderr_log"
        ) || rc=$?
    else
        (
            cd "$bench_dir"
            export KOALA_SHELL="bash"
            timeout --kill-after=15s "${timeout_s}s" \
                bash ./execute.sh "--$size" "${script_args[@]}" \
                </dev/null >"$stdout_log" 2>"$stderr_log"
        ) || rc=$?
    fi
    printf '%d\n' "$rc" > "$time_log"

    kc_restore_instrumented_scripts "$bench_dir/scripts"

    if [[ -d "$bench_dir/outputs" ]]; then
        cp -a "$bench_dir/outputs/." "$snapshot_dir/" 2>/dev/null || true
    fi
    rm -rf "$bench_dir/outputs"

    if [[ "$mode" == "incr" ]]; then
        rm -rf "$cache_dir" 2>/dev/null || sudo rm -rf "$cache_dir" 2>/dev/null || true
    fi

    if [[ "$rc" -eq 124 || "$rc" -eq 137 ]]; then
        echo TIMEOUT
        return
    fi

    local stdout_size snapshot_size
    stdout_size=$(wc -c <"$stdout_log" 2>/dev/null || echo 0)
    snapshot_size=$(du -sb "$snapshot_dir" 2>/dev/null | awk '{print $1}')
    snapshot_size=${snapshot_size:-0}
    if [[ "$stdout_size" -eq 0 && "$snapshot_size" -le 4096 ]]; then
        echo EMPTY
        return
    fi

    if [[ "$rc" -ne 0 ]]; then
        echo "FAIL($rc)"
        return
    fi

    echo PASS
}

# Diff two mode snapshots; returns 0 on identical, 1 on mismatch. On mismatch,
# appends a short summary (file count, first few differing files) to $3.
kc_diff_snapshots() {
    local bash_dir=$1
    local incr_dir=$2
    local report_file=$3

    if ! diff -r --brief "$bash_dir" "$incr_dir" >/dev/null 2>&1; then
        {
            echo "diff -r summary:"
            diff -r --brief "$bash_dir" "$incr_dir" 2>&1 | head -20 | sed 's/^/    /'
            local first_diff
            first_diff=$(diff -r --brief "$bash_dir" "$incr_dir" 2>/dev/null |
                awk -F': ' '/^Files / {print $2; exit}')
            if [[ -n "$first_diff" ]]; then
                local incr_first
                incr_first=$(echo "$first_diff" | awk '{print $NF}')
                local bash_first
                bash_first=$(echo "$first_diff" | awk '{print $1}')
                echo ""
                echo "First differing file (truncated):"
                diff -u "$bash_first" "$incr_first" 2>/dev/null | head -30 | sed 's/^/    /'
            fi
        } >>"$report_file"
        return 1
    fi
    return 0
}

# Top-level driver invoked by each benchmark's run.sh. Args:
#   --name <n> --size <s> --scripts <s1 s2 ...> --deps <d1,d2,...>
#   --timeout-min N --timeout-small N --timeout-full N
#   --skip-reason <text>   declare this benchmark unsupported; record SKIP and return
kc_run_benchmark() {
    local name="" size="min" deps="" skip_reason=""
    local timeout_min=300 timeout_small=1500 timeout_full=7200
    local -a scripts=()

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --name)           name=$2; shift 2 ;;
            --size)           size=$2; shift 2 ;;
            --deps)           deps=$2; shift 2 ;;
            --skip-reason)    skip_reason=$2; shift 2 ;;
            --timeout-min)    timeout_min=$2; shift 2 ;;
            --timeout-small)  timeout_small=$2; shift 2 ;;
            --timeout-full)   timeout_full=$2; shift 2 ;;
            --scripts)
                shift
                while [[ $# -gt 0 && "$1" != --* ]]; do
                    scripts+=("$1")
                    shift
                done
                ;;
            *) kc_err "kc_run_benchmark: unknown arg: $1"; return 2 ;;
        esac
    done

    [[ -z "$name" ]] && { kc_err "kc_run_benchmark: --name required"; return 2; }

    if [[ -n "$skip_reason" ]]; then
        local report="$KC_RESULTS_DIR/$KC_RUN_ID/$name.report"
        mkdir -p "$(dirname "$report")"
        kc_log "SKIP  $name  $skip_reason"
        {
            echo "STATUS=SKIP"
            echo "REASON=$skip_reason"
        } > "$report"
        return 0
    fi

    local timeout_s
    case "$size" in
        min)   timeout_s=$timeout_min ;;
        small) timeout_s=$timeout_small ;;
        full)  timeout_s=$timeout_full ;;
        *) kc_err "unknown --size: $size"; return 2 ;;
    esac

    kc_remember_benchmark "$name"

    local report="$KC_RESULTS_DIR/$KC_RUN_ID/$name.report"
    mkdir -p "$(dirname "$report")"
    : > "$report"

    if [[ -n "$deps" ]]; then
        local -a dep_array=()
        IFS=',' read -ra dep_array <<<"$deps"
        local missing
        missing=$(kc_missing_deps "${dep_array[@]}")
        if [[ -n "$missing" ]]; then
            local missing_oneline
            missing_oneline=$(echo "$missing" | tr '\n' ',' | sed 's/,$//')
            kc_log "SKIP  $name  missing-deps:$missing_oneline"
            echo "STATUS=SKIP" >>"$report"
            echo "REASON=missing-deps:$missing_oneline" >>"$report"
            return 0
        fi
    fi

    local bench_dir="$KOALA_REPO/$name"
    if [[ ! -d "$bench_dir" ]]; then
        kc_log "SKIP  $name  missing-koala-dir"
        echo "STATUS=SKIP" >>"$report"
        echo "REASON=missing-koala-dir" >>"$report"
        return 0
    fi

    local -a script_args=()
    if [[ ${#scripts[@]} -gt 0 ]]; then
        script_args=(-s "${scripts[@]}")
    fi

    kc_log "RUN   $name  size=$size timeout=${timeout_s}s scripts=${scripts[*]:-ALL}"

    kc_koala_clean "$name"
    if ! kc_koala_fetch "$name" "$size" >/dev/null 2>&1; then
        kc_warn "$name: fetch.sh --$size failed (continuing; inputs may already exist)"
    fi

    local bash_status incr_status overall
    bash_status=$(kc_run_mode "$name" bash "$size" "$timeout_s" "${script_args[@]}")
    kc_log "      bash  -> $bash_status"

    if [[ "$bash_status" != "PASS" ]]; then
        kc_log "FAIL  $name  bash mode produced $bash_status; skipping incr comparison"
        {
            echo "STATUS=FAIL"
            echo "REASON=bash-$bash_status"
            echo ""
            echo "bash stderr (last 20 lines):"
            tail -20 "$KC_WORK_DIR/$name/$size/bash.stderr" 2>/dev/null | sed 's/^/    /'
        } >>"$report"
        return 0
    fi

    kc_koala_clean "$name"
    incr_status=$(kc_run_mode "$name" incr "$size" "$timeout_s" "${script_args[@]}")
    kc_log "      incr  -> $incr_status"

    if [[ "$incr_status" != "PASS" ]]; then
        kc_log "FAIL  $name  incr mode produced $incr_status"
        {
            echo "STATUS=FAIL"
            echo "REASON=incr-$incr_status"
            echo ""
            echo "incr stderr (last 20 lines):"
            tail -20 "$KC_WORK_DIR/$name/$size/incr.stderr" 2>/dev/null | sed 's/^/    /'
        } >>"$report"
        return 0
    fi

    if kc_diff_snapshots "$KC_WORK_DIR/$name/$size/bash" "$KC_WORK_DIR/$name/$size/incr" "$report"; then
        kc_log "PASS  $name  outputs match"
        echo "STATUS=PASS" >>"$report"
        overall=0
    else
        kc_log "FAIL  $name  outputs differ (see $report)"
        sed -i '1i STATUS=FAIL\nREASON=output-mismatch\n' "$report"
        overall=0
    fi
    return $overall
}
