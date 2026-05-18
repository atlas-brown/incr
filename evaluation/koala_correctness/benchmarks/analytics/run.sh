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

# Skip port-scan (Go + zannotate + routeviews MRT) and ray-tracing (long).
kc_run_benchmark \
    --name analytics \
    --size "$KC_SIZE" \
    --deps jq,tcpdump \
    --timeout-min 300 \
    --timeout-small 1500 \
    --timeout-full 7200 \
    --scripts nginx pcaps
