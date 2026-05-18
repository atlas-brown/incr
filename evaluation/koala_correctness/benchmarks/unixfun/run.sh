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

# Scripts 22 and 27 are placeholder stubs in koala; the koala execute.sh also
# disables them. Run the rest (1-21, 23-26, 28-36).
kc_run_benchmark \
    --name unixfun \
    --size "$KC_SIZE" \
    --timeout-min 600 \
    --timeout-small 2400 \
    --timeout-full 10800 \
    --scripts 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 \
              23 24 25 26 28 29 30 31 32 33 34 35 36
