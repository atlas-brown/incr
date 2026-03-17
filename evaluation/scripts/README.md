# Evaluation Scripts

Helper scripts for running and verifying benchmarks. Run from `incr/` root.

All scripts that run benchmarks **clean up on exit** (including Ctrl+C): they restore any benchmark scripts left in incr-instrumented state and remove stray artifacts.

| Script | Purpose |
|--------|---------|
| `run_parallel.sh` | Run all benchmarks in parallel (default + observe). `--skip-dpt` to skip longest. Cleans up on exit. |
| `monitor_benchmarks.sh` | Poll status of parallel run. `--loop` to refresh every 60s. |
| `verify_outputs.sh` | Verify default vs observe produce identical outputs. `--min` for faster run, `--no-cleanup` to keep artifacts. Cleans up on exit. |
| `run_smoke_min.sh` | Quick smoke test with `--min` inputs. Cleans up on exit. |
| `restore_benchmark_scripts.sh` | Restore benchmark scripts if left in incr mode. Removes `incr_script_*` files. Run manually if needed. |
| `run_bench_background.sh` | Run sequential benchmark suite in background. |
| `check_bench_progress.sh` | Check progress of background run. |

## Quick start

```bash
cd incr
bash evaluation/scripts/run_parallel.sh --skip-dpt
# In another terminal:
bash evaluation/scripts/monitor_benchmarks.sh --loop
```
