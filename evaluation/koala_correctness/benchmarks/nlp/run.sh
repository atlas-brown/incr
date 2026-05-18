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

kc_run_benchmark \
    --name nlp \
    --size "$KC_SIZE" \
    --timeout-min 300 \
    --timeout-small 1800 \
    --timeout-full 7200
