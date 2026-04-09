#!/bin/bash
set -euo pipefail

TOP=$(git rev-parse --show-toplevel)
DIR="$TOP/evaluation/war-and-peace"

rm -rf /tmp/incr_cache
rm -rf "$DIR"/sandbox_*
rm -rf /tmp/sort* /tmp/tmp*