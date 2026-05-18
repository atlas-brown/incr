#!/bin/bash
if [[ -z "${KC_DIR:-}" ]]; then
    set -euo pipefail
    cd "$(dirname "${BASH_SOURCE[0]}")"
    source ../../lib.sh
    KC_RUN_ID="${KC_RUN_ID:-$(date +%Y%m%d-%H%M%S)-standalone}"
    KC_SIZE="${KC_SIZE:-min}"
    mkdir -p "$KC_WORK_DIR" "$KC_RESULTS_DIR/$KC_RUN_ID"
    trap 'kc_aggressive_cleanup' EXIT INT TERM HUP
fi

# Skip opt-parallel (needs chess dataset download even at --min) and the three
# mkfifo+background scripts: diff, set-diff, bi-grams. Those rely on named
# pipes with `&`, which incr's strace-based pipeline can't track and causes it
# to hang. The remaining scripts are straight `cmd | cmd > file` pipelines.
kc_run_benchmark \
    --name oneliners \
    --size "$KC_SIZE" \
    --deps dos2unix \
    --timeout-min 300 \
    --timeout-small 1800 \
    --timeout-full 7200 \
    --scripts nfa-regex sort top-n wf spell sort-sort uniq-ips comm
