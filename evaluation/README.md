# incr Evaluation Suite

## Modes

- **default**: incr with try + strace (fallback, no observe)
- **observe**: incr with observe when available (~10x faster for write-heavy benchmarks)

Set `INCR_OBSERVE=0` to force default mode; `INCR_OBSERVE=1` or unset to use observe.

## Structure

```
evaluation/
├── run.sh                    # Sequential benchmark run (creates run_results/)
├── benchmarks/               # Per-benchmark dirs (execute.sh, scripts/, etc.)
├── scripts/                  # Helper scripts (parallel, verify, monitor, restore)
├── analysis/                 # Plotting (compare_default_observe.py)
├── run_results_parallel/     # Results from parallel run (primary baseline)
└── agent/docs/BENCHMARK_RUN_CONTEXT.md  # Detailed run guide
```

## Running

From `incr/`:

```bash
# Sequential (default + observe)
bash evaluation/run.sh              # both modes
bash evaluation/run.sh default       # default only
bash evaluation/run.sh observe       # observe only

# Parallel (faster; --skip-dpt to skip longest benchmark)
bash evaluation/scripts/run_parallel.sh --skip-dpt
bash evaluation/scripts/monitor_benchmarks.sh --loop   # monitor

# Verify outputs match between modes
bash evaluation/scripts/verify_outputs.sh --min
```

Results: `run_results_parallel/` (primary; from run_parallel.sh). See BENCHMARK_RUN_CONTEXT.md for error checking and baseline comparison.
