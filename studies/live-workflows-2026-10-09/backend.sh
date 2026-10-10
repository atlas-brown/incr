#!/usr/bin/env bash
set -euo pipefail
case "$DEMO_MODE" in
    native) exec "$@" ;;
    observe)
        exec "$DEMO_INCR" --cache "$DEMO_CACHE" --try "$DEMO_TRY" \
            --observe "$DEMO_OBSERVE" --effect-policy live -- "$@" ;;
    incr)
        exec "$DEMO_INCR" --cache "$DEMO_CACHE" --try "$DEMO_TRY" \
            --effect-policy live -- "$@" ;;
    sandbox)
        # No Incr, tracing, cache, or replay: only private execution + end commit.
        sandbox=$(mktemp -d "$DEMO_CACHE/try.XXXXXXXX")
        status=0
        "$DEMO_TRY" -D "$sandbox" -- "$@" || status=$?
        "$DEMO_TRY" commit "$sandbox"
        exit "$status" ;;
    *) echo "Unknown backend: $DEMO_MODE" >&2; exit 2 ;;
esac
