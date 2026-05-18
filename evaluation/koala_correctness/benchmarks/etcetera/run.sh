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

# etcetera/sieve.sh combines three patterns that incr cannot currently handle:
# user-defined shell functions called as commands (primes, gen_composites,
# sequence, sequence_2_to, sqrt, get_multiples), mkfifo + background &, and
# recursive function calls. The other script in this benchmark (try.sh) needs
# unionfs-fuse / FUSE. The whole benchmark is therefore skipped.
kc_run_benchmark \
    --name etcetera \
    --size "$KC_SIZE" \
    --skip-reason "incr: shell functions + mkfifo+& (sieve.sh); FUSE required (try.sh)"
