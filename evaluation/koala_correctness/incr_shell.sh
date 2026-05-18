#!/bin/bash
# Drop-in replacement for `bash` exported as $KOALA_SHELL.
# Forwards all arguments to incr.sh. The cache directory is taken from
# $INCR_CACHE_DIR; $INCR_TOP overrides incr.sh's default repo discovery
# (which uses `git rev-parse --show-toplevel` and would otherwise resolve to
# the surrounding koala repo when called from a koala script).
#
# stdin is redirected from /dev/null because incr's stream executor reads
# (and hashes) all of stdin even when the wrapped command does not consume it.
# Koala's execute.sh runs `while IFS= read -r name; do $KOALA_SHELL ...; done
# <<< "$names"`, and without this redirect incr drains the here-string after
# the first iteration so the read loop exits early. The koala benchmark
# scripts pass inputs via file-path arguments, not stdin, so this redirect
# matches bash's effective behavior at the script-execution boundary.
set -euo pipefail

if [[ -z "${INCR_REPO:-}" ]]; then
    echo "incr_shell: INCR_REPO is unset" >&2
    exit 2
fi

export INCR_TOP="$INCR_REPO"
exec "$INCR_REPO/incr.sh" "$@" </dev/null
