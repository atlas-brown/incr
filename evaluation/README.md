# incr Evaluation Suite

## Modes

- **default**: incr with try + strace (fallback, no observe)
- **observe**: incr with observe when available (~10x faster for write commands)

Set `INCR_OBSERVE=0` to force default mode; `INCR_OBSERVE=1` or unset to use observe.

## Running

From `incr/`:

```bash
# Benchmarks (all 15 benchmarks)
bash evaluation/run.sh              # both modes
bash evaluation/run.sh default      # default only
bash evaluation/run.sh observe      # observe only

# War-and-peace
bash evaluation/war-and-peace/with_cache.sh         # default
bash evaluation/war-and-peace/with_cache_observe.sh # observe
bash evaluation/war-and-peace/without_cache.sh     # baseline
```

Results: `evaluation/run_results/default/` and `evaluation/run_results/observe/`.
