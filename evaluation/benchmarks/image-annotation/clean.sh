#!/bin/bash
cd "$(dirname "$0")" || exit 1

rm -rf cache
rm -rf outputs
rm -f scripts/incr_script_* 2>/dev/null || true
rm -rf /tmp/sort* /tmp/tmp* 2>/dev/null || true