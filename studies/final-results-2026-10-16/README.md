# Final application and synthetic measurements

All measurement jobs are complete. Application medians use three repetitions per mode; re-execution excludes the first execution within each repetition. Annotations are off. Cohorts remain explicit: twelve new-full families, completed same-binary targeted DPT, and the separately labelled live image API study. Do not pool them or the earlier historical checkpoints.

| Benchmark | Cohort | Bash total / re-execution (s) | Original total / re-execution (s) | Observe total / re-execution (s) |
|---|---|---:|---:|---:|
| file-mod | new-full | 41.029 / 37.638 | 111.734 / 83.889 | 27.021 / 21.771 |
| word-freq | new-full | 10.313 / 5.377 | 6.223 / 0.646 | 4.072 / 0.243 |
| nlp-ngrams | new-full | 56.694 / 47.949 | 62.776 / 47.888 | 50.199 / 38.654 |
| poet | new-full | 189.995 / 189.974 | 82.895 / 81.104 | 52.276 / 52.210 |
| nlp-uppercase | new-full | 32.797 / 29.415 | 27.042 / 19.844 | 23.173 / 18.074 |
| covid | new-full | 39.500 / 31.487 | 26.745 / 20.431 | 19.950 / 16.172 |
| nginx-analysis | new-full | 223.083 / 221.154 | 58.856 / 52.488 | 37.314 / 35.042 |
| spell | new-full | 639.007 / 631.042 | 206.973 / 196.722 | 201.880 / 193.104 |
| bio | new-full | 283.686 / 278.681 | 265.444 / 257.140 | 164.345 / 158.109 |
| weather | new-full | 46.593 / 37.527 | 16.606 / 10.936 | 14.147 / 9.754 |
| beginner | new-full | 197.372 / 181.037 | 78.772 / 61.852 | 70.224 / 54.927 |
| unixfun | new-full | 100.735 / 91.512 | 110.852 / 96.872 | 106.148 / 92.607 |
| dpt | final-targeted | 5332.129 / 5004.948 | 1204.950 / 809.597 | 1187.345 / 797.346 |
| image-annotation | image-api-final | 241.704 / 203.767 | 78.586 / 10.193 | 57.513 / 3.172 |

## Synthetic workloads

All 17 scenarios × three scales × three repetitions × three modes × six phases completed: **2,754 output-validated timings**. [Full 51-comparison table](../observe-strengths-microbench/measurements/final-01/REPORT.md) and verified raw evidence remain in their original study. `microbenchmark-results.csv` contains all mode medians; `microbenchmark-resources.csv` contains all 2,754 named resource records. These synthetic strengths and controls are not representative application claims. Observe does not win every case or phase; all results are retained.

## Evidence and limits

- [Canonical application evidence](../evaluation-checkpoint-2026-10-16/README.md) retains all historical and current cohorts and figures.
- [Live image study](../image-annotation-api-2026-10-16/README.md) completed 63/63 with image-payload validation. Generated titles/filenames may differ, and latency depends on the remote service. A shared filename-prefix repair prevents title collisions. These are not strict deterministic-output results.
- [Micro instrumentation diagnosis](../observe-strengths-microbench/measurements/final-01/instrumentation-review.json) explains zero retained cache metadata for artifact installation: extended attributes prevent replay. The original failed cache-presence audit is preserved; all native-output/capture/coverage checks passed. No runtime shortcut was added.
- `application-invocations.csv` collects all selected completed application samples with their original resource records. `application-statistics.json` retains each of the three per-mode repetition totals; CSVs are derived projections. `verification.json` records source and runtime hashes. Three repetitions provide descriptive comparisons, not significance claims.
- GNU time RSS is maximum single-process RSS, not aggregate concurrent memory; filesystem counters are blocks; cache/work peaks are sampled allocations.

Regenerate these tables with `python3 studies/final-results-2026-10-16/collect.py` from the Incr root. Collection reads saved evidence and never executes benchmarks.
