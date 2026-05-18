#!/bin/bash
# Run the koala correctness suite: each in-scope koala benchmark twice
# (bash, then incr) at the chosen --size, diff outputs, write a summary.
#
# Usage:
#   run.sh [--size=min|small|full] [--only=name,name,...]
#          [--list] [--install-light] [--purge-work]
set -euo pipefail

cd "$(dirname "$0")"
source ./lib.sh

KC_SIZE=min
KC_ONLY=()
KC_LIST=0
KC_INSTALL_LIGHT=0
KC_PURGE_WORK=0

for arg in "$@"; do
    case "$arg" in
        --size=*)        KC_SIZE="${arg#--size=}" ;;
        --only=*)
            IFS=',' read -ra _only <<<"${arg#--only=}"
            for n in "${_only[@]}"; do
                n="${n#"${n%%[![:space:]]*}"}"
                n="${n%"${n##*[![:space:]]}"}"
                [[ -n "$n" ]] && KC_ONLY+=("$n")
            done
            ;;
        --list)          KC_LIST=1 ;;
        --install-light) KC_INSTALL_LIGHT=1 ;;
        --purge-work)    KC_PURGE_WORK=1 ;;
        --help|-h)
            sed -n '2,9p' "$0"
            exit 0
            ;;
        *) kc_err "unknown arg: $arg"; exit 2 ;;
    esac
done
export KC_SIZE

case "$KC_SIZE" in
    min|small|full) ;;
    *) kc_err "--size must be min|small|full"; exit 2 ;;
esac

KC_RUN_ID="$(date +%Y%m%d-%H%M%S)-$KC_SIZE"
export KC_RUN_ID
mkdir -p "$KC_RESULTS_DIR/$KC_RUN_ID"
KC_SUMMARY="$KC_RESULTS_DIR/$KC_RUN_ID/summary.txt"

# Patches are reverted only at end-of-run, not between benchmarks; per-benchmark
# cleanup focuses on incr's caches/sentinels/mounts.
trap 'kc_aggressive_cleanup; kc_revert_koala_patches' EXIT INT TERM HUP

# Discover available benchmarks from the benchmarks/ directory; ordering is
# alphabetical so runs are reproducible.
mapfile -t KC_ALL_BENCHMARKS < <(
    find "$KC_DIR/benchmarks" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort
)

if [[ "$KC_LIST" -eq 1 ]]; then
    printf 'Available benchmarks:\n'
    printf '  %s\n' "${KC_ALL_BENCHMARKS[@]}"
    exit 0
fi

if [[ "$KC_INSTALL_LIGHT" -eq 1 ]]; then
    kc_log "Installing lightweight apt deps..."
    sudo apt-get update -qq
    sudo apt-get install -y --no-install-recommends \
        ffmpeg unrtf imagemagick jq dos2unix bsdmainutils zstd \
        samtools minimap2 bcftools tcpdump
fi

if [[ "$KC_PURGE_WORK" -eq 1 ]]; then
    kc_log "Purging $KC_WORK_DIR"
    rm -rf "$KC_WORK_DIR"
fi
mkdir -p "$KC_WORK_DIR"

if [[ ${#KC_ONLY[@]} -gt 0 ]]; then
    KC_TARGETS=()
    for n in "${KC_ONLY[@]}"; do
        if [[ ! -d "$KC_DIR/benchmarks/$n" ]]; then
            kc_err "unknown benchmark: $n (use --list)"
            exit 2
        fi
        KC_TARGETS+=("$n")
    done
else
    KC_TARGETS=("${KC_ALL_BENCHMARKS[@]}")
fi

kc_log "================================================================"
kc_log "Koala correctness suite (incr)"
kc_log "  size=$KC_SIZE  benchmarks=${KC_TARGETS[*]}"
kc_log "  run_id=$KC_RUN_ID"
kc_log "  results=$KC_RESULTS_DIR/$KC_RUN_ID"
kc_log "================================================================"

# Stale-state recovery: clean before the first benchmark. Defensive — covers
# any prior interrupted run that didn't get to its trap.
kc_aggressive_cleanup

# Overlay the koala-script patches under koala_patches/ so this harness works
# against an upstream-pristine koala repo. They're reverted by the EXIT trap.
kc_apply_koala_patches

for name in "${KC_TARGETS[@]}"; do
    bench_runner="$KC_DIR/benchmarks/$name/run.sh"
    [[ -f "$bench_runner" ]] || { kc_err "missing runner: $bench_runner"; continue; }
    # Inner trap so a failure in this benchmark still gets cleaned up
    # before we move on.
    (
        set +e
        source "$bench_runner"
    ) || kc_warn "$name: runner exited non-zero"
    kc_aggressive_cleanup
done

# Build summary from per-benchmark reports.
{
    printf '=== Koala correctness vs incr (size=%s, run=%s) ===\n' "$KC_SIZE" "$KC_RUN_ID"
    printf '\n'
    pass=0 fail=0 skip=0
    for name in "${KC_TARGETS[@]}"; do
        report="$KC_RESULTS_DIR/$KC_RUN_ID/$name.report"
        if [[ ! -f "$report" ]]; then
            printf '  %-14s NO-REPORT\n' "$name"
            continue
        fi
        status=$(awk -F= '$1=="STATUS"{print $2; exit}' "$report")
        reason=$(awk -F= '$1=="REASON"{print $2; exit}' "$report")
        case "$status" in
            PASS) printf '  %-14s PASS\n' "$name"; pass=$((pass + 1)) ;;
            SKIP) printf '  %-14s SKIP  %s\n' "$name" "$reason"; skip=$((skip + 1)) ;;
            *)    printf '  %-14s FAIL  %s\n' "$name" "${reason:-unknown}"; fail=$((fail + 1)) ;;
        esac
    done
    printf '\nchecked=%d  passed=%d  failed=%d  skipped=%d\n' \
        "${#KC_TARGETS[@]}" "$pass" "$fail" "$skip"
    printf '\nPer-benchmark reports: %s/\n' "$KC_RESULTS_DIR/$KC_RUN_ID"
} | tee "$KC_SUMMARY"

if grep -q '  FAIL  ' "$KC_SUMMARY"; then
    exit 1
fi
exit 0
