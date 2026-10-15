## Latest steering: fair default without static annotations

Prioritize complete correctness and end-to-end evaluation with static performance annotations disabled in BOTH Incr and Observe. The user separately authorized an annotated comparison later, with annotations enabled on both sides. Earlier comparisons with different static annotation coverage are diagnostic only, not fair speedup evidence. Learned introspection remains part of each implementation. Finite stdin staging was rejected after whole-pipeline regressions; archived diagnostic results are retained.

Fresh fair diagnostic: `general-unannotated-one-01` completed 84/84 exact comparisons over two repetitions at 1 MiB, unchanged provenance, static annotations off on both sides, native frontend and directory-access assumption enabled. Whole-sequence original/Observe ratios: word-freq 2.253x, Poet 8.836x, COVID 14.928x, weather 13.029x. These synthetic repeated minimum records do not qualify historical sizes or all families. Full Bash and fresh all-family minimum checks remain pending.

Checkpoint qualification complete: `general-unannotated-min-01` passes 246/246 comparisons across all twelve non-DPT families (one repetition), terminal monitor healthy. Every family is faster: 2.336x–20.716x original/Observe. `UNANNOTATED_CHECKPOINT.json` records exact scope and test counts. Final/full 71 focused regressions pass; live 70+1 skip, compressed batch 69+2 skips; Observe 7 units and 420 integration assertions pass. Full official 83-group Bash correctness, DPT, progressive scaling and historical-size evaluation are still outstanding. Bash runner now accepts and records `--native-transform` and `--assume-directory-access`, enabling explicit qualification of the benchmark configuration as well as defaults. Observe implementation checkpoint is a26e759a86e3ff6f8c3b0e192b8ab23e681e4288; the corresponding Incr checkpoint records this handoff. Next: verify clean/pushed branches, then medium/larger measurements and full Bash gates.

# Active Observe optimization goal: handoff

Last updated: October 14, 2026 (America/New_York).

## Required ordered workflow (latest user instructions)

1. Iterate quickly and sequentially on small inputs to confirm and improve Observe performance on essentially all applicable benchmarks. Compare original Incr and older Observe, preserve reasonable original assumptions and core caching/replay optimizations, and focus on eliminating try/overlayfs/strace overhead. No custom sort or other command-specific algorithm replacements.
2. Once implementations are basically finalized, validate, make clean checkpoint commits in **both** repositories, and push both.
3. Increase input sizes progressively through medium/larger scales, checking correctness, variance, reuse and resource/provenance evidence. **All maintained Bash correctness tests must pass cold and warm on the final implementation and relevant configurations.** Iterate on failures or lost speedups, then commit and push both repos again.
4. Only after these gates pass, run the complete applicable full evaluations from clean owned workspaces, with fair frozen baselines, reliable statistics, strict validation, durable results and progress monitoring. Keep non-paper coverage separate. Exclude only the API-key image-annotation workload from the overall coverage goal.

Expected architecture: Observe replaces try/overlayfs plus strace while retaining Incr's general caching and replay optimizations. Avoid elaborate optimizations that do not address measured overhead. Do not claim the full Bash gate from the focused regression suite. The official maintained Bash workflow is studies/bash-parity-audit-2026-10-08/run.sh (83 groups, native/Observe, cold/warm), with independently recheckable raw evidence. Use new result destinations and inspect lifecycle/coverage failures as well as normalized comparisons.

The previous persistent goal was explicitly cleared by the user; a new active persistent goal now records this entire ordered workflow, including BOTH commit/push checkpoints and the full Bash correctness gate.

Current implementation: finite stdin staging has been removed after the whole-pipeline regressions in `general-finite-eight-01` (84/84 exact comparisons, unchanged provenance). Candidate and pinned original now gate static pure/read-only tracing shortcuts on the existing `-a` flag; default comparisons disable annotations on both sides. Candidate cache format is 30 and includes annotation policy, temporary policy and directory-access policy. Rust units pass 36 tests, one ignored. Focused correctness, fresh fair timings and the full Bash gate remain necessary; inspect live processes before scheduling measurements.

Small-scale evidence: general-eight-01 completed 84/84 valid comparisons over two repetitions with unchanged provenance. Original/Observe whole-sequence ratios: word-freq 0.890x, Poet 0.886x, COVID 1.404x, weather 2.046x. Therefore the speedup gate is unmet; do not launch full evaluation. general-fd-transport-01 completed 24/24 valid transport/tracer diagnostics over three repetitions. Current dependency-traced sorting means: regular stdin 0.625s, piped stdin 0.966s; older tracer 0.598/0.996s. This attributes a transport penalty and shows the older tracer is not intrinsically much faster in this probe. These synthetic diagnostics are not benchmark-family qualification.

Current directory-access assumption remains explicit and opt-in, preserving directory-open/listing dependencies; Observe passes all 420 integration assertions. Full maintained Bash qualification has not yet been rerun on these changes. Both repositories have uncommitted implementation/diagnostic work, so the next requested checkpoint commits are still outstanding.

## Current follow-up: smaller-scale diagnosis

The checkpoint was committed and pushed: Incr ee5283b on origin/observe and
Observe cb347d6 on origin/main; both were clean. `general-min-01` then completed
246/246 valid comparisons of all twelve non-DPT minimum families on that frozen
checkpoint with the native frontend enabled. Eleven families were faster, but
word frequency was 0.886x (original 1.247s vs Observe 1.408s). The terminal monitor
reported health=ok. DPT remains pending on current source.

The user now prioritizes smaller-scale iteration and attribution against the older
Observe pair (Incr 4f8723e, Observe a95ca6b), and explicitly authorizes original-style
temporary-filesystem assumptions. General implementation changes only: no custom
sorting/cut algorithms or command-specific performance replacements.

Current uncommitted runtime change: Observe-backed Incr assumes /tmp, /var/tmp and
absolute non-root TMPDIR are scratch, excluded from dependencies/effect replay.
`--track-temporaries` / INCR_TRACK_TEMPORARIES=true restores tracking. Policy is
keyed in cache version 27; the Observe wire protocol and effect format are unchanged.
The default tracer noisy-path filter is used unless temporary tracking is selected.
Tests preserve explicit temporary-input invalidation and default scratch reuse.

35 Rust units pass (one ignored). All 69 final and 69 full-tracing regressions pass;
live passes 68 with one policy-specific skip; compressed batch passes 67 with two
unbounded-input skips. Small benchmark qualification of this revised source is
still pending. No DPT/full-size evaluation is running.

`general-old-profile-01` passed 60 diagnostic cold/warm cases with unchanged
provenance on the pre-scratch checkpoint. At 8 MiB, stdin sort cold old/current
0.663/1.051s and warm 0.0282/0.0368s; payload checks 3--5ms do not explain the cold
gap. Older code treats all sort/grep/cut forms as pure and omits /tmp dependencies.
Four isolated non-temporary correctness probes against the old pair fail: preserved
mtime content edits, sort file-list invalidation, parent-link retargeting, and
corrupt cached stdout. These differences cannot justify dropping ordinary file
correctness checks, even though temporary scratch assumptions are now authorized.

`general-scratch-micro-01` and `general-scratch-cpu-02` are explicitly invalidated:
the probe had put application input/output in TMPDIR, violating the new contract.
The repaired probe uses fixture/tmp and removes the application output before warm
write-file replay. `general-scratch-micro-02` then passed 30/30 exact comparisons
with unchanged provenance (diagnostic profiling, one sample only). More repeated
unprofiled comparisons are required before claiming a speedup. The rejected data
and raw perf recording remain for diagnosis. Root perf was used without changing
machine-wide perf settings; the measured program still ran as the normal user.

Micro probes now retain decoded cache metadata and optional phase profiles, accept
input size and selected comparison modes, and preserve per-case directory mismatch
diagnostics. Inspect `general-scratch-directories-01` before restarting it. The
next focus is attributing cold tracing/transport cost and missed general replay,
then small paired repeats against the frozen checkpoint; requalify DPT and full
historical sizes only after this iteration.

A supplemental coverage draft for web-search/Tufte weather is archived locally at
results/coverage-planning/supplemental-draft.patch and is NOT implemented/qualified.
Finish the smaller-scale performance investigation before expanding the harness.

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
