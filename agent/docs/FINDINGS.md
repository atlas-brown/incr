# incr + observe: Summary of Findings

This document consolidates findings from the observe integration work, correctness review, benchmarks, and tests.

---

## 1. Integration Overview

**Observe** is a lightweight tracer that records file reads/writes and outputs JSON. incr uses it as an alternative to strace for write commands when `--observe <path>` is provided.

**Trace type selection** (when observe is available):
- Pure commands (grep, etc.) → TraceType::Nothing
- Read-only / stateless → TraceType::TraceFile (strace or observe)
- **Write commands** → **TraceType::Observe** (replaces Sandbox)

**Key difference**: Observe mode avoids the try overlayfs sandbox. Writes go to the real filesystem; observe records them; incr copies to outputs/upperdir and runs try commit.

---

## 2. Correctness Review

A manual review of the integration found **no correctness bugs**. Verified:

- **Cache hit + child kill**: Child is killed before joining capture threads; threads see EOF and return Completed.
- **Cache hit + BrokenPipe**: If downstream closes (e.g. `head`), join_stream_threads returns None; we return 141 without outputting cached data.
- **Cache miss + Observe**: Child runs to completion, trace file is parsed, capture_observe_output copies writes, commit applies.
- **Trace file cleanup**: Temp trace files are removed after parsing or on cache hit.
- **TraceFile vs Observe**: TraceFile (read-only) does not extract/capture; Observe has explicit branch.

See `OBSERVE_INTEGRATION_REVIEW.md` for details.

---

## 3. Benchmark Results

Preliminary benchmarks (5 iterations each) show:

| Workload | Cold: strace | Cold: observe | Warm: strace | Warm: observe |
|----------|--------------|---------------|--------------|----------------|
| cat (small) | ~9 ms | ~7 ms | ~3 ms | ~3 ms |
| cat (100KB) | ~9 ms | ~7 ms | ~3 ms | ~3 ms |
| sed | ~10 ms | ~7 ms | ~3 ms | ~3 ms |
| **write** | **~250 ms** | **~23 ms** | ~36 ms | ~18 ms |
| **cp** | **~250 ms** | **~22 ms** | ~35 ms | ~17 ms |
| grep | ~5 ms | ~5 ms | — | — |
| **batch write** | **~250 ms** | **~23 ms** | ~27 ms | ~17 ms |

**Takeaways**:
- **Write workloads**: ~11x speedup (cold), ~2–4x (warm). Observe avoids Sandbox/try overlayfs.
- **TraceFile (read-only)**: ~1.2–1.4x speedup from lighter tracing.
- **Pure (grep)**: Similar overhead; both use TraceFile then Nothing.

Run `bash agent/run_bench.sh` and `python3 agent/benchmarks/plot.py agent/benchmarks/results.txt` to regenerate.

---

## 4. Bug Fixes

- **cache.clean()** (batch_cache.rs): Previously used `Path::new("data.incr")`, removing the data file from the current working directory instead of the cache directory. Fixed to use `self.directory.join(&data_file)`.
- **dependency.rs**: Corrected `k == &mut DependencyKey::DoesNotExist` to `k == &DependencyKey::DoesNotExist` (unnecessary mutable reference).

**Note**: Avoid naming files `data.incr` in the working directory when running incr; use a distinct name (e.g. `preserve_me.txt`) for regression tests.

---

## 5. Test Coverage

`bash agent/test_incr_observe.sh` runs 8 test files, 22 scenarios:

| File | Scenarios |
|------|-----------|
| t_incr_basic | TraceFile (strace/observe), Sandbox, Observe write, cache hits |
| t_incr_batch | Batch executor + observe, cache hit |
| t_incr_cache_clean | Cache clean does not touch cwd files (regression for batch_cache fix) |
| t_incr_invalidation | cp + cache hit + invalidation on input change |
| t_incr_pure | grep (TraceType::Nothing) |
| t_incr_multi | Multi-file write |
| t_incr_edge | BrokenPipe with head, cache hit + head, trace file leak |
| t_incr_observe_robust | Exit codes, stderr, sed, failures, stdin, append, mkdir, batch stdin |

---

## 6. How incr Uses observe

1. **incr.sh** detects `../observe/target/release/observe` and passes `--observe-path` to insert.py.
2. **insert.py** adds `--observe <path>` to incr invocations in the transformed script.
3. **incr binary** receives `--observe`; when set, write commands use TraceType::Observe.
4. **Observe** is invoked as: `observe --json --output <file> --no-filter -- <cmd>`
5. **parse_observe** reads the JSON and extracts (read_set, write_set).
6. **capture_observe_output** copies written files to outputs/upperdir for try commit.

---

## 7. Architecture Notes

- **TraceType::Observe** is a new mode alongside Sandbox, TraceFile, Nothing.
- For TraceFile (read-only), incr can use strace or observe; both produce parseable output.
- For write commands, Observe replaces Sandbox when available.
- See `ARCHITECTURE_ANALYSIS.md` for full incr architecture.

---

## 8. Files in agent/

| Path | Purpose |
|------|---------|
| test_incr_observe.sh | Run all integration tests |
| run_bench.sh | Run benchmark |
| benchmarks/ | Bench script, plot, results |
| tests/ | Test files and runner |
| docs/ | Architecture, review, this summary |
