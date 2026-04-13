#!/bin/bash
set -e

TOP="$(git rev-parse --show-toplevel)"
export INCR_CACHE_DIR="${INCR_CACHE_DIR:-/tmp/incr_cache}"

exec "$TOP/incr.sh" -b "$@"
