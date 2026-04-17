# Observe Integration Review

> **Evaluation suite:** End-to-end runs use `evaluation/benchmarks/run_all.sh` with `--run-mode incr-observe` or `all` (see `EVALUATION_BENCHMARK_SUITE.md`).

Review of the observe integration in incr, focusing on correctness and edge cases. When observe is not available, incr falls back to try + strace (Sandbox for writes); see main `README.md`.

## Flow Summary

### Trace Type Selection (mod.rs)
- **TraceType::Observe** chosen when `observe_command.is_some()` and command may write (not pure/stateless/read-only)
- Replaces Sandbox for write commands when observe is available

### Stream Executor (stream_executor.rs)
1. `create_child_runtime`: For Observe, uses `observe_{key}.json` in cache dir (temp path)
2. `spawn`: Runs `observe --json --output <file> --no-filter -- <cmd>`
3. `load_cache_data`: Cache hit → kill child, clean runtime, return Valid; Cache miss → wait for child, return Invalid
4. `join_stream_threads`: Waits for stdin/stdout/stderr capture threads
5. **Cache hit**: `output_cached_data` — output from cache, commit if writes
6. **Cache miss**: `save_command_data` — parse_trace, capture_observe_output, commit, save

### Batch Executor (batch_executor.rs)
- Uses cache paths (batch_<hash>/observe.json) for trace file
- Same Observe handling in save path: capture_observe_output, commit

### parse_trace (mod.rs)
- `.json` extension → parse_observe; else → parse_strace
- TraceFile and Observe both use the same parse path (file path differs)
- Removes trace file after parsing

### capture_observe_output (batch_cache.rs)
- Copies written files from real FS to outputs/upperdir
- Skips non-existent paths
- Creates structure try commit expects (upperdir, ignore)

## Invariants Verified

1. **Cache hit + child kill**: We kill the child before joining threads. Threads see EOF, return Completed. No orphan processes.

2. **Cache hit + BrokenPipe**: If capture threads got BrokenPipe (downstream closed) before we killed child, join_stream_threads returns None. We clean and return BROKEN_PIPE_CODE. We never call output_cached_data. Correct.

3. **Cache miss + Observe**: Child (observe) runs to completion. Trace file exists. parse_trace reads it. capture_observe_output copies writes. commit applies. Correct.

4. **Trace file cleanup**: parse_trace removes the trace file after parsing. clean_child_runtime removes temp trace file on cache hit. No leaks.

5. **TraceFile vs Observe in save_command_data**: TraceFile falls through to `_ => {}` (no extract/capture). Observe has explicit branch. Correct.

## Potential Edge Cases (Low Risk)

1. **Observe writes to file that no longer exists**: capture_observe_output skips. write_set still contains path. try commit gets empty/missing file. Behavior may vary; low priority.

2. **Observe crashes before writing JSON**: parse_observe fails. Error propagated. Command fails. Correct.

3. **short_circuit + head**: When downstream (head) closes, capture returns BrokenPipe. join_stream_threads returns None. We return 141. Correct. (Tested in t_incr_edge.sh)

## No Bugs Found

After tracing through stream executor (cache hit/miss, BrokenPipe), batch executor, parse_trace, and capture_observe_output, no correctness bugs were identified. The integration preserves existing invariants.
