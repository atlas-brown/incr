#!/bin/bash
TOP=$(git rev-parse --show-toplevel)
DIR="$TOP/evaluation/war-and-peace"

rm -rf "$TOP/cache"
rm -rf "$DIR/test_cache"
rm -f "$TOP/baseline.txt" "$TOP/incr.txt"
rm -rf /tmp/sort* /tmp/tmp*
