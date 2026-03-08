# incr/agent

Agent-generated tooling and documentation for incr development. Use this directory for tests, benchmarks, and architecture docs. For user-facing usage (script mode, observe, fallback), see the main [README.md](../README.md).

## Structure

```
agent/
├── README.md
├── test_incr_observe.sh  # Run integration tests (→ tests/run.sh)
├── run_bench.sh          # Run benchmark (→ benchmarks/run.sh)
├── benchmarks/
│   ├── bench.sh          # Benchmark script (strace vs observe)
│   ├── run.sh            # Run and save to results.txt
│   ├── plot.py           # Generate bar chart from results
│   ├── results.txt       # Latest output
│   └── benchmark_plot.png
├── tests/
│   ├── run.sh            # Test runner
│   ├── common.sh         # Shared setup
│   ├── t_incr_basic.sh   # TraceFile, Sandbox, Observe
│   ├── t_incr_batch.sh   # Batch executor
│   ├── t_incr_cache_clean.sh  # Cache clean regression (batch_cache fix)
│   ├── t_incr_invalidation.sh  # cp + cache invalidation
│   ├── t_incr_pure.sh    # grep (pure)
│   ├── t_incr_multi.sh   # Multi-file write
│   ├── t_incr_edge.sh    # BrokenPipe, trace leak
│   └── t_incr_observe_robust.sh  # Exit codes, stderr, sed, mkdir, etc.
└── docs/
    ├── ARCHITECTURE_ANALYSIS.md
    ├── OBSERVE_INTEGRATION_REVIEW.md
    ├── EVALUATION_BENCHMARK_SUITE.md  # How to install, run, clean evaluation benchmarks (default + observe)
    └── FINDINGS.md           # Summary of all findings
```

## Usage

```bash
# From incr/

# Run integration tests
bash agent/test_incr_observe.sh
bash agent/test_incr_observe.sh edge    # filter

# Run benchmark
bash agent/run_bench.sh

# Generate plot (requires matplotlib)
python3 agent/benchmarks/plot.py agent/benchmarks/results.txt

# Full evaluation suite (14 benchmarks, default + observe modes)
# See docs/EVALUATION_BENCHMARK_SUITE.md for install, run, clean
bash evaluation/run.sh
```

## Tests

`test_incr_observe.sh` runs all integration tests (8 files, 22 scenarios). Coverage:

| File | Tests |
|------|-------|
| t_incr_basic | TraceFile (strace/observe), Sandbox, Observe write |
| t_incr_batch | Batch executor + observe |
| t_incr_cache_clean | Cache clean does not touch cwd (regression for batch_cache fix) |
| t_incr_invalidation | cp + cache invalidation |
| t_incr_pure | grep (TraceType::Nothing) |
| t_incr_multi | Multi-file write |
| t_incr_edge | BrokenPipe/head, trace file leak |
| t_incr_observe_robust | Exit codes, stderr, sed, failures, stdin, append, mkdir, batch stdin |

## Benchmarks

The benchmark compares incr with strace (fallback) vs observe across:

- **cat** (small, 100KB) – TraceFile, cold/warm
- **sed** – TraceFile, cold/warm
- **write** (echo > file) – Sandbox vs Observe, cold/warm
- **cp** – read+write, cold/warm
- **grep** – pure, cold
- **script: cp\|sed\|cat** – 3-command chain, cold/warm
- **script: echo\|cp\|grep** – 3-command write+read, cold/warm
- **batch write** – batch executor, cold/warm

Results are plotted with all scenarios on one chart. See main `README.md` for fallback (try + strace) vs observe mode.

## Dependencies

- **plot.py**: `pip install matplotlib`
