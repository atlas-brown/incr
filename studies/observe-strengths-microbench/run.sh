#!/usr/bin/env bash
set -euo pipefail
study=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
exec python3 -B "$study/harness/study.py" "$@"
