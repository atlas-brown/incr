# Qualified unannotated checkpoint — 16 October 2026

All 216 full-size beginner/DPT invocations passed native output validation, terminal monitoring and strict paired-cohort review. These are three independent paired sequences per mode. Medians are seconds summed over all ordered versions within each repetition, then the median over repetitions.

| Scope | Benchmark | Bash | Original Incr | Observe |
|---|---|---:|---:|---:|
| Whole sequence | beginner | 197.455 | 76.038 | 75.311 |
| Whole sequence | DPT | 5332.129 | 1204.950 | 1187.345 |
| Excluding first execution | beginner | 179.720 | 61.256 | 61.658 |
| Excluding first execution | DPT | 5004.948 | 809.597 | 797.346 |

The previous material beginner slowdown is resolved. Original Incr and Observe are near parity: Observe's whole median is 0.96% lower, while its edited median is 0.66% higher. Three samples do not establish significance for these small differences. DPT Observe is about 1.4% faster than original and 4.5 times faster than Bash overall. Every per-version regression and sample spread remains in the detailed report.

The general fix queues speculative stdin in RAM, following original Incr, rather than writing large speculative inputs to disk. It preserves byte order, cancellation, EOF and error handling. Sufficient RAM is assumed; ordered speculative output still has a 64 MiB spill threshold. Trusted private cache payloads no longer incur redundant integrity hashing. Application dependency validation remains. There are no command-specific algorithm replacements or enabled purity annotations.

Both maintained full Bash configurations passed cold and warm: 83 default groups and 82 benchmark-option groups, including regression policies and scratch cleanup. All 276 historical and 15 supplemental minimum checks passed. The qualification record covers 22 successful stages, both binaries, 63 runtime source files and 138 frozen measurement files. Bash comparisons retain existing documented presentation/path normalization; this is not a claim that every raw upstream driver status is identical. DPT ignores only the precisely identified benign TensorFlow compatibility notice, retaining genuine errors and native output checks.

[CHECKPOINT.json](CHECKPOINT.json) pins the receipts. [Detailed review](checkpoint-evidence/trusted-cache-2026-10-16-03/final-review.json) contains every sample, spread, historical comparison flag and resource interpretation. [Sequence resources](checkpoint-evidence/trusted-cache-2026-10-16-03/sequence-resources.csv) preserves timing, cache/disk peaks, CPU and RSS. GNU time RSS is maximum single-process RSS, not aggregate concurrent memory; cache/work peaks are sampled allocated bytes, and filesystem output counters are blocks.

For beginner, median cache peaks are 2,905,169,920 bytes original and 2,224,336,896 Observe; maximum-process RSS medians are 918,964 and 858,060 KiB. DPT cache medians are 49,168,384 and 41,222,144 bytes; RSS medians are 14,358,940 and 14,358,988 KiB. DPT changed/new-image versions dominate wall time; tracing-versus-model costs were not separately measured. Versions 1, 2, 3a and 3b use the five root images; version 4 onward recursively includes all nine. Models and image scope were preserved.

## Earlier results remain separate

The [older preliminary report](checkpoint-evidence/preliminary-final-paper-01/report.json) covers 12 completed families on older binaries, with incomplete DPT. It is not the full evaluation of this new implementation. The following medians are historical checkpoint results only:

| Benchmark | Bash | Original Incr | Observe |
|---|---:|---:|---:|
| file-mod | 41.030 | 111.393 | 27.683 |
| word-freq | 10.654 | 5.800 | 4.331 |
| nlp-ngrams | 59.389 | 64.167 | 50.049 |
| poet | 190.770 | 82.576 | 53.569 |
| nlp-uppercase | 32.418 | 26.913 | 23.603 |
| covid | 39.348 | 27.813 | 21.328 |
| nginx-analysis | 225.457 | 57.609 | 40.419 |
| spell | 637.079 | 206.194 | 208.379 |
| bio | 284.121 | 263.712 | 168.931 |
| weather | 47.190 | 16.243 | 17.161 |
| beginner | 174.026 | 77.574 | 90.058 |
| unixfun | 98.777 | 109.594 | 112.123 |

Original Incr does not consistently beat Bash without annotations; Observe does not consistently beat original. These facts are retained. Published paper timings are contextual rather than matched pairs: reconstructed inputs, workload repairs, annotation settings and timing methodology differ. Current DPT totals are reasonably close to published totals; beginner Bash is substantially faster on the reconstructed current workload. All 19 flagged per-version historical differences remain disclosed in the detailed review. Do not pool old and new samples or claim an exact paper reproduction.

## Evidence and next run

[Archive instructions](checkpoint-evidence/README.md) describe all old/new successful, failed and incomplete cohorts. Source evidence remains on disk; disposable old prepared inputs were removed only after packaging, with a cleanup receipt. The fresh [reproduction controller](../observe-reproduction/README.md) runs all 828 historical invocations and then 45 full supplemental invocations serially after both final checkpoint pushes. Live state is generated under that study's ignored results directory. This committed checkpoint does not itself claim that fresh full evaluation has finished.
