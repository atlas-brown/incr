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

# Skip tuft-weather: it generates matplotlib plots, which add Python/matplotlib
# as a hard dependency and produce nondeterministic image metadata.
kc_run_benchmark \
    --name weather \
    --size "$KC_SIZE" \
    --timeout-min 180 \
    --timeout-small 900 \
    --timeout-full 3600 \
    --scripts max-temp
