#!/bin/bash
# Restore benchmark scripts from *.incr_orig sentinels and remove stale incr_script_* sidecars.
# Uses run_lib.sh (same as run_all.sh). Run from incr/: bash evaluation/scripts/restore_sentinels.sh
set -euo pipefail
TOP="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$TOP" || exit 1
TOP="$(git rev-parse --show-toplevel)"
# shellcheck source=../benchmarks/run_lib.sh
source "$TOP/evaluation/benchmarks/run_lib.sh"
for d in "$TOP/evaluation/benchmarks"/*/scripts; do
  [[ -d "$d" ]] || continue
  restore_instrumented_scripts "$d"
done
