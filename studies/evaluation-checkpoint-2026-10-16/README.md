# Consolidated evaluation measurements — 16 October 2026

All application benchmark execution and queued work covered by this archive was cancelled at the user's request. Those runs are not scheduled to resume. The separate synthetic microbenchmark study is tracked in `../observe-strengths-microbench/`. This directory is the canonical home for the detailed measurements from both Incr and Observe, historical qualification, diagnostics, failed attempts and current evaluation. Results are descriptive, with annotations off in the final cohorts; do not pool revisions or select the faster replicate.

## Final full reproduction (cancelled)

792 completed invocations passed validation; zero completed samples failed. Twelve historical families completed three paired repetitions. DPT has complete Bash repetitions 0/1, Observe repetitions 0/1, and original repetition 0, plus four valid original repetition-1 samples. The in-flight invocation was cancelled and has no timing sample. Historical scope was 828; supplemental scope was 45 and never started. A pre-cancellation running status in raw evidence is superseded by admin/cancellation.json.

Median whole-sequence seconds (three complete repetitions per mode). The first twelve rows come from the full reproduction; DPT comes from the completed final targeted run using the same binaries:

| Benchmark | Bash | Original Incr | Observe |
|---|---:|---:|---:|
| file-mod | 41.029 | 111.734 | 27.021 |
| word-freq | 10.313 | 6.223 | 4.072 |
| nlp-ngrams | 56.694 | 62.776 | 50.199 |
| poet | 189.995 | 82.895 | 52.276 |
| nlp-uppercase | 32.797 | 27.042 | 23.173 |
| covid | 39.500 | 26.745 | 19.950 |
| nginx-analysis | 223.083 | 58.856 | 37.314 |
| spell | 639.007 | 206.973 | 201.880 |
| bio | 283.686 | 265.444 | 164.345 |
| weather | 46.593 | 16.606 | 14.147 |
| beginner | 197.372 | 78.772 | 70.224 |
| unixfun | 100.735 | 110.852 | 106.148 |
| DPT (final targeted) | 5332.129 | 1204.950 | 1187.345 |

Across these thirteen completed same-binary benchmark results, Observe is faster than original Incr on all thirteen and faster than Bash on twelve. The DPT row does not imply that DPT completed in the cancelled full reproduction; cohorts remain separate in the detailed records. Unixfun remains about 5.4 seconds slower than Bash. Original Incr is slower than Bash on file-mod, nlp-ngrams and unixfun. Small differences are not evidence of statistical significance.

## Earlier final targeted run

The same exact Incr/Observe/original binary hashes were used for the final targeted cohort and the cancelled full reproduction. The earlier beginner/DPT run completed all 216 invocations, three paired repetitions, with strict native validation. Its whole-sequence medians were beginner 197.455 / 76.038 / 75.311 seconds and DPT 5332.129 / 1204.950 / 1187.345 (Bash/original/Observe). The new completed DPT sequences are roughly 4–7% faster across modes; preserve them as independent replication rather than combining selected samples. The valid targeted DPT results remain available despite cancellation of the later reproduction.

DPT medians excluding the first execution are **5004.948 / 809.597 / 797.346 seconds** (Bash/original/Observe), also from the three completed targeted repetitions. Observe is about **4.49× faster than Bash** over the whole sequence and **6.28×** excluding the first execution; its advantage over original Incr is about **1.5%**, a small difference. These values are recorded under `final-targeted` / `dpt` in `family-statistics.json`.

The older full checkpoint used different binaries, completed twelve families, and stopped on a narrowly identified TensorFlow compatibility notice in DPT. Its results remain explicitly labelled old-full. Published paper timings are contextual, not matched samples: reconstructed inputs, repairs, annotations and timing methodology differ.

## Re-execution figures

[Speedup comparison](figures/reexecution-speedup.png) compares Original Bash, Original Incr and Observe Incr, normalized to Bash = 1×. [Absolute-time panels](figures/reexecution-times.png) show the corresponding cumulative seconds with an independent linear axis per benchmark. Both exclude the first execution of each repetition, following the historical `evaluation/scripts/perf-bars-color.py` convention at commit `15d749a`. Bars use the median of three per-repetition totals; speedups are ratios of those medians, not averages of individual execution speedups. All final cohorts have annotations off. DPT uses the completed same-binary targeted cohort; the other twelve benchmarks use the new full reproduction. No samples are pooled across cohorts.

Observe has lower median re-execution time than original Incr on all thirteen benchmarks and than Bash on twelve; unixfun is about 1.2% slower than Bash. These are descriptive comparisons, not significance claims. PDF and SVG exports, exact plotted values in `figures/reexecution-data.csv`, source hashes and a standalone plotting script are included. Regenerate with `qualification/.venv/bin/python studies/evaluation-checkpoint-2026-10-16/figures/plot_reexecution.py` from the repository root. This only reads saved statistics and does not execute benchmarks.

## Detailed records

- `invocations.csv`: every completed invocation from the old-full, final-targeted and new-full cohorts, including resource dictionaries and validation fields. No sample from an incomplete sequence is silently promoted to a full-sequence statistic.
- `family-statistics.json`: all complete per-repetition sequence totals and edited totals excluding first execution, with medians only when all three repetitions exist.
- `files.jsonl.gz`: original path, size and SHA256 for each retained metadata/log/statistics record. `archive::member` identifies records recovered from earlier evidence bundles.
- `detailed-statistics.tar.gz`: content-addressed members `sha256/<hash>`; duplicate records share bytes. Read a path via the index, then extract its hash member. All members were hash/size verified after collection.
- `catalog.json`: collection scope, source roots, archive hashes, file counts and checkpoint revisions.
- `supplementary-statistics.tar.gz` and `supplementary-catalog.json`: 38 additional loose records from scratch diagnostics and early microbenchmarks, verified by member hashes.
- `admin/`: cancellation, service inventory, reproducible consolidation script and cleanup receipts.

Timing, CPU, RSS, filesystem counters, cache/work peaks, cache-entry counts, correctness summaries, exact-output fingerprints, configurations, source/binary fingerprints, input recipes, environment records, historical reports and failures are retained. RSS is maximum single-process RSS, not aggregate concurrent RAM; sampled disk/cache peaks are allocated bytes, filesystem output counters are blocks. Byte-identical repeated records are stored once; measurements are never numerically pooled across cohorts.

This is a statistics archive, not a runnable filesystem snapshot. Downloaded datasets/models, output datasets, caches, binary profiles, frozen executables, generated plots and duplicate old archives are intentionally excluded and removed during cleanup. Earlier full raw artifacts remain in Git history where previously committed. Paths inside historical records describe their original layout and need not exist after cleanup. Current runnable benchmark and correctness harnesses are documented in `../README.md`.

## Cleanup verification

The cleanup retains one benchmark runner and one full Bash runner, current regression/component tests, versioned minimum seeds and installed prerequisite programs. DPT model downloads and all evaluations are explicit. Runtime Rust/source implementation is unchanged. The reorganized harness passed 45 tests, Bash comparison/supervision passed 20 tests, and the two benchmark-component tests passed. Seven affected minimum seed preparation paths were checked and their scratch removed; full benchmarks were not rerun. See `admin/` for receipts. Published reference timings are retained separately under `references/`.
