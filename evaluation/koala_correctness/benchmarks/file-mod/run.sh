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
    --name file-mod \
    --size "$KC_SIZE" \
    --deps ffmpeg,convert,unrtf,zstd \
    --timeout-min 600 \
    --timeout-small 2400 \
    --timeout-full 10800 \
    --scripts compress_files encrypt_files img_convert to_mp3 thumbnail_generation
