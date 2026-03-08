#!/bin/bash
# Wrapper: run benchmark and save results.
exec bash "$(dirname "$0")/benchmarks/run.sh" "$@"
