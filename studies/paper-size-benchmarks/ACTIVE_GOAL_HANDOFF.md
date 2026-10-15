# Active Observe optimization goal: handoff

Last updated: October 14, 2026 (America/New_York).

## Checkpoint review supersedes older implementation notes below

The user requires a general implementation: no command-specific performance
substitutions or benchmark-overfit overrides. The new byte-sort executor and
stdin-only cut annotation have been removed, together with the now-unused
partial-input executor entry point. External sort/cut parity and dependency tests
remain; the installed tools execute through the normal backends. Do not reintroduce
specialized sort algorithms, thresholds or counted numeric sorting. The salted
encryption bypass remains a correctness repair, applied to both baseline and
candidate, rather than a performance optimization.

General tracing, cache/dependency validation, bounded spooling, parser improvements
and the opt-in native shell frontend remain. Empty-input detection now rejects
write-only and O_PATH descriptors. New qualification must identify this revised
source: all earlier performance results below used a different implementation,
including the removed specializations, and do not qualify this checkpoint.

The persistent goal is active. First finish checkpoint validation, commit and push
both repositories. Then requalify minimum inputs including real-model DPT and
profile general backend overhead on scaled and representative inputs. Run a fresh
historical-size evaluation after explicit owned cleanup, preparation and inventory
inspection, initially one repetition as previously requested. Repeat paired runs
where needed to assess variance; a single repetition cannot establish statistical
significance. Report every slowdown and correctness failure honestly.

The paper matrix excludes web-search and Tufte weather for historical scope, but
the user now requests all benchmarks except image annotation requiring an OpenAI
API key. Inventory and evaluate applicable non-paper workloads separately using
the same correctness and provenance principles; do not silently omit them or mix
their statistics into the historical matrix.

No measurement is running. Owned study cleanup was planned, inspected and applied
without mounts or recovery snapshots; results, frozen sources/builds, minimum
inputs, dependencies and model weights were retained. Historical inputs/downloads
were already absent. The old audit service had a terminal shutdown error after a
successful evidence check because its timer was already gone; this was not a
benchmark failure. Inspect actual process/service state before any next run.

Validation evidence: [CHECKPOINT_VALIDATION.json](CHECKPOINT_VALIDATION.json).
The harness additionally catches unexpected nested application outputs and dangling
links; its 27 fault tests pass. Revised code passes 34 Rust units (one ignored),
68 final, 68 full-tracing, 68 live and 66 batch/compressed regressions (two skipped),
nine shell AST tests and six native frontend tests. Observe passes seven Rust units
and 414 integration assertions. No fresh benchmark timings have been collected.

## Earlier evidence and implementation history

The following records describe the pre-review implementation. The checkpoint
policy above takes precedence over its proposed next steps.

## Goal and completion criteria

Investigate regressions since the older faster Observe implementation, optimize current Incr+Observe rigorously, preserve correctness, then explicitly run one repetition of the historical-size evaluation. Compare Bash, pinned original Incr with only reviewed correctness fixes, and current Incr Observe. Exclude the benchmark requiring an OpenAI API key. Required outcome: significant Observe speedups over original Incr on every included benchmark, with all output checks passing. If any included benchmark is slower or wrong, continue iterating. The goal is active and incomplete.

User requirements: sequential measurements; start small and inspect correctness; review hangs and robustness; modular harness with multiple runs and detailed stats; clear task-owned caches/artifacts before fresh measurements to conserve disk; one repetition for full evaluation; preserve correctness. Keep cleanup, preparation and measurement as explicit separate actions. Do not launch the full evaluation until the slower families have been investigated.

## Live state and newest results

At the time of this update, systemd study service and audit timer are inactive; no measurement is running. Verify process/service status before starting another run.

| Result | Validity and performance |
| --- | --- |
| paper-size study results/native-transform-min-02 | 246/246 comparisons, all 12 non-DPT minimum families correct. Original/Observe total ratios: file-mod 6.131x, word-freq 1.553x, ngrams 8.175x, Poet 3.362x, uppercase 4.015x, COVID 2.844x, nginx 1.690x, spell 2.720x, bio 10.335x, weather 2.781x, beginner 4.140x, unixfun 4.746x. One minimum-size repetition only. |
| sibling regression results/scaled-thirtytwo-native-01 | 72/72 valid, provenance valid, two independent repetitions. Poet 2.097x, COVID 1.078x, weather 1.152x. Synthetic repetition of minimum fixtures, not paper data. |
| sibling regression results/scaled-128-native-bound64-01 | 36/36 valid, provenance valid. At 128 MiB: Poet original 20.765s, Observe 30.842s (0.673x); COVID 6.882s, 8.298s (0.829x); weather 2.563s, 2.675s (0.958x). Observe slower for all three. Synthetic inputs. This is the newest performance evidence and changes the next action: do not launch full evaluation yet. |

DPT was not included in the latest native-transform-min-02 qualification. Earlier results: min13 completed 30/30 DPT comparisons on an earlier frozen runtime, Observe 273.992s vs original 291.981s (1.066x). Other earlier evidence includes OPTIMIZATION_VALIDATION.json (276 minimum-size comparisons, earlier runtime only) and isolated SAM experiments. Requalify current source/binaries. Do not weaken output/filesystem validators; earlier classifier cache misses were caused by changed working-image timestamps.

## Repositories and code

Workspace: /users/jxia3/atlas. Main repo /users/jxia3/atlas/incr; sibling Observe repo /users/jxia3/atlas/observe; pinned original baseline /users/jxia3/atlas/incr-main-qualification.

Original baseline is detached at 4b8e5ddf8e275d947518c7cc0f5d2713fe992307 with only the reviewed two-file, 14-insertion/1-deletion correctness patch in reference/original-minimal-fixes.patch. It ensures salted OpenSSL work is freshly executed. The harness doctor verifies exact patch equality. Do not alter baseline performance or weaken checks.

Incr HEAD: b440cfc1f3702a81e644c8634a3a886afe23d55d; Observe HEAD: b5ad47a8d6155559d01f0fca616e72ab19d749e6. Both have uncommitted work. Nothing committed/pushed. Recheck git status and frozen source archives before editing.

Implemented work in current workspace:
- Observe ancestor dependency walking skips already checked ancestors. Rust units and 414 Observe integration cases passed; old/new min13 Observe had identical 77 dependencies and output/status. Preliminary paired SAM/TensorFlow import gain ~3–5%, not enough to explain sort bottlenecks.
- Skip cache index work for statically pure TraceType::Nothing; validate only selected stdin candidate; interruption-safe hashing.
- Detect known-empty stdin before child startup while retaining delayed producer handling.
- Observe protocol 9 distinguishes NotDirectory from absent; fixes Python egg-info probes that prevented SAM caching. Cache format 26. Conservative successful O_TRUNC overwrite dependencies preserve inode on replay.
- Spool returns to RAM after draining; 64 MiB per stream bound, spills above. Weather writes decreased in probes, but no established timing gain.
- Python transform startup: lazy libbash for non-Bash, shared immutable prefix AST, avoid private dataclass state, direct method code inspection with fallback.
- Narrow stdin-only GNU cut specialization, with locale/loader/executable guards.
- src/execution/byte_sort_executor.rs: bounded exact byte sorting for sort, sort -u, --unique in C/POSIX locale; current cap 64 MiB/8M records; allocation/bound fallback to GNU. Counted-record map is bounded. Numeric/field-keyed sorting remains GNU. 128 MiB evidence suggests investigating sort cost/coverage before increasing bounds.
- Opt-in native shell compiler via INCR_NATIVE_TRANSFORM=1 / study --native-transform, off by default. Pinned tree-sitter Bash, conservative CST whitelist, capability/helper/source checks, bounded parse and syntax check, ready marker, outer timeout and Python fallback. It changes shell transformation frontend as well as runtime/tracer; disclose this. Harness records option and validates on resume.
- Optional per-PID phase profiler, off by default.

Current verification logs/hashes are in results/native-transform-validation-01/: 36 Rust tests passed (one ignored), 9 shell AST tests, 70 final regressions, 6 native execution/fallback tests, 26 harness tests. Includes unsupported-syntax fallback, fake binary marker rejection and forced hanging control timeout.

Rejected/reverted experiments: nonblocking stdin pipe had no consistent gain; larger kernel pipe buffers, stdin sort spool and thread tuning also rejected. Do not resurrect without new measurements.

## Harness, safety and disk

Harness under studies/paper-size-benchmarks: run.sh, harness/study.py, prepare.py, cleanup.py, launch.py, monitor.py. Explicit stages: doctor, prepare min|paper, run, report, status, cleanup dry-run then --apply, launch a single chosen stage. Global nonblocking lock enforces serial measurements. It records Bash oracle, original and Observe results, strict validators, detailed resource/timing/cache stats, frozen binaries/source/helper/benchmark provenance, and strict resume. It supports multiple run IDs.

Synthetic scaling harness is ../observe-performance-regression/harness/scale.py; it repeats minimum fixtures and is not historical input. It hashes source/data and verifies around each variant, uses production validators/metrics and removes temporary generated inputs.

Machine: 64 GiB RAM, Xeon D-1548, 16 logical CPUs; last df showed ~41 GiB free. Harness reserves 8 GiB and caps work at 32 GiB. Never clear unrelated/global package/model caches or OS page cache. Cleanup only task-owned study scratch, caches, fixtures, captures, downloads and explicitly named old builds. Preserve immutable weights/dependencies and results/source evidence. Cleanup refuses mounts/recovery state and writes an audit record. Paper downloads/inputs were absent at last check; inspect before full run.

Before full evaluation: finish performance iteration and current-source DPT/min qualification; run doctor/build if needed; dry-run and inspect cleanup; apply owned cleanup including paper inputs/downloads while preserving result evidence and models; prepare historical profile separately; inspect provenance/disk; manually launch one repetition with selected native-transform option; run read-only five-minute audits; inspect all final output, status, resource and timing data. If any family is slower or incorrect, continue iteration.

## Next actions

1. Confirm no job/process/timer is active and retain the complete 128 MiB report and profiles.
2. Profile general tracing, caching, process startup, dependency validation and stream buffering costs. Change one general mechanism at a time; preserve exact command execution and lossless bounded I/O. Command-specific algorithm replacements are disallowed.
3. Compare frozen candidate vs current source with sequential 32/128 MiB and minimum fixtures; record hashes, repeat variance, resource data and exact validators. Retain only repeatable gains.
4. Re-run all-family min and DPT/current SAM qualification after changes. Aim for significant gains in every included family.
5. Then perform explicit owned cleanup, prepare historical-size inputs, inspect, and manually launch one-repetition full evaluation.

## Current no-go

Do not launch the historical full-size evaluation yet: the current 128 MiB result shows Observe slower on Poet, COVID and weather, and current-source DPT is unqualified. Minimum/synthetic evidence cannot establish all-family historical-size speedups.
