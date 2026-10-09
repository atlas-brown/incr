#!/usr/bin/env bash
set -euo pipefail
study_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
exec python3 -B -u "$study_dir/harness/runner.py" "$@"
