#!/bin/bash
# Run all incr + observe integration tests.
# Covers: TraceFile, Sandbox, Observe mode, batch executor, cache invalidation,
#         pure commands, multi-file write, BrokenPipe, exit codes, stderr, etc.
# Usage: bash test_incr_observe.sh [filter]
exec bash "$(dirname "$0")/tests/run.sh" "$@"
