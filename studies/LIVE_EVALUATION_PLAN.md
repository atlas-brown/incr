# Live-policy evaluation plan

Prepared 2026-11-04. Initial review below is retained for rationale. The user subsequently authorized implementation, minimal smoke tests, background execution, and commit/push after completed audits. The execution plan is amended below; original results remain untouched.

## Approved execution refinement

Use the maintained supervisors with explicit live policy and one serial systemd campaign. Run the changed harness unit tests, live regressions, word-frequency minimum sequence, all synthetic scenarios at tiny diagnostic scale, and one image minimum sequence. Do not run a full Bash audit or repeat minimum runs for every application. Retain ordinary native output validation, deadlines, disk reserve and process cleanup in the measured runs. This replaces the broader qualification schedule proposed in section 4.

Fresh scope is 828 deterministic application, 2,754 synthetic and 63 image invocations. Supplemental is excluded because it was not part of the completed historical results. The campaign's separate study directories hold frozen runner copies, smoke evidence and new results; no old cohort is resumed. Prepare and measure one application family at a time. Stop on failure, without automatic measurement retries. Compile/install before timings. At completion, verify and archive evidence, clean owned workspaces, commit only the campaign and its implementation, push without force, and verify the remote commit. Stop publication if repository HEAD, implementation files or staged changes no longer match launch state. The service survives window closure, not host shutdown.

## Findings and evidence

The final reported Observe-backed measurements used **effect policy `final`**. “Final results” is a publication/completion label; “live image API” means real API requests, not live effect policy.

- Applications: `paper-size-benchmarks/EVALUATION_PROTOCOL.json` declares final policy. The maintained `harness/study.py::environment` explicitly sets `INCR_EFFECT_POLICY=final`. I also read the content-addressed archived configuration/setup records through `evaluation-checkpoint-2026-10-16/files.jsonl.gz`, verifying SHA256 before interpreting them. The historical reproduction selection yielded 114 setup records, all final. These include the incomplete DPT portion; this count is not a completed-sample count. The targeted-run records recovered through loose and nested archive references also recorded final. This was a policy/provenance inspection, not a fresh exhaustive validation of every archived sample.
- Images: all nine `paper-02` sequence setup records in `measurements/detailed-evidence.tar.gz` were checked against the catalog hashes and explicitly set final policy.
- Synthetics: `measurements/final-01/provenance.json` explicitly records `effect_policy: final`; both `freeze` and execution environment construction in the synthetic harness hardcode final.
- Setting `INCR_EFFECT_POLICY=live` outside these harnesses is insufficient: their environment construction overrides it. The launchers do not currently expose a policy argument.
- `incr-formalization/paper/data/remeasured/` exports the saved results; it is not another evaluation runner. Its 891 application and 2,754 synthetic samples correspond to the selected cohorts below.

Architecture relevant to this experiment: the shell frontend wraps commands in Incr; Incr validates dependencies/stdin and manages cache replay; Observe traces live filesystem accesses and coordinates the effect gate. Final policy can stop writers and restore speculative state before installing cached outputs. Live policy forbids cancellation after the first live effect. Final-only overwrite validation and relaxed rename/unlink replay barriers also differ. Consequently live is a semantic change that can reduce reuse, not merely an alternative background-launch setting.

Current Incr HEAD is `3d3c77613967a6b5dfe44273568395a0f092e38d`; Observe HEAD is `16666457494115cd018ae507dd74849ed7fd4275`. Comparing `src`, Cargo manifests/locks, and the Incr wrapper against measured revisions `c75ee1fa9223ad3b45cd76580b398f9cf9495ec9` and `257a6d40c185a158e444a530fbe5f268529e3ff0` showed no changes. This supports source-level replication; it does not establish identical newly built binaries, installed tools, inputs, or host conditions.

## Freeze the scope before running

| Cohort | Fresh live experiment | Settings preserved apart from policy |
|---|---|---|
| Main applications | 13 families, 92 ordered script versions, 3 modes × 3 repetitions = 828 invocations | Paper recipes; annotations off; native transform, directory-access assumption, content-validated inputs on |
| Synthetic strengths | 17 scenarios × 3 scales × 3 repetitions × 3 modes × 6 phases = 2,754 invocations | Same counts/rows and six phases; shared Python frontend with coverage check; directory-access assumption on; content validation off; profiling off |
| Image API | 7 versions × 3 modes × 3 repetitions = 63 invocations | Repaired filenames; historical ten-image recipe; native transform and directory-access assumption on; content validation off; isolated llm 0.36 client |
| Supplemental extension | Separate 45-invocation full cohort, if included | web-search and weather-Tufte; retain separate label and original full recipes |

The main+image+synthetic target is **3,645 measured invocations**, excluding qualification and pilots. Supplemental would make 3,690. Supplemental was never completed in the archived full reproduction, so it must be described as additional coverage, not a rerun of completed results.

The old application table combines twelve completed `new-full` families, DPT from `final-targeted`, and the separate `image-api-final` cohort. The cancelled full reproduction had 792 validated invocations out of 828 and must never be resumed or presented as complete. A fresh live campaign can complete all thirteen deterministic families and preserve links to those old comparison sources.

Keep native Bash and pinned original Incr as contemporaneous controls. Original is `4b8e5ddf8e275d947518c7cc0f5d2713fe992307` plus the recorded minimal baseline patch; it does not acquire Observe's live-policy semantics. Label the candidate `observe/live`. Do not substitute the current try backend for the original baseline.

## 1. Reconstruct and record prerequisites

The reviewed machine has approximately 50 GiB free on the workspace filesystem and 62 GiB RAM. FUSE exists and noninteractive sudo succeeds. No matching evaluation worker or loaded `incr*` user unit was found. `loginctl` reports `Linger=no`. The parser/ML virtual environment, release binaries, and sibling original baseline checkout are absent. Missing checked tools include ffmpeg, samtools, minimap2, gnuplot, and ImageMagick's mogrify. These are observed launch prerequisites, not assumptions that historical setup still exists.

Recreate the documented baseline worktree and exact patch; build all three binaries with `cargo build --release --locked`. Reconstruct parser versions libbash 0.1.14, libdash 0.5.2 and shasta 0.5, and use archived environment/package records for ML/tool versions. Explicitly obtain and hash-check DPT's real models, including for minimum qualification. Install the dictionary and record its hash. Install the pinned Bash corpus/builds for correctness gates. Supplemental additionally requires its pinned Node runtime and modules.

Run the maintained doctor after setup. Record OS/kernel, CPU, RAM, filesystem, package/tool versions, source hashes, patches and binary hashes. Compare actual reconstructed input inventories to archived inventories and explain mismatches. Never claim exact historical input-byte identity merely from a recipe. Preserve the DPT local HTTP fixture mirror and model/cache namespace isolation.

Build and freeze once for the campaign, with a durable checksum manifest. Per-family workers must consume or verify the same frozen build. No rebuilding, dependency installation, source changes, preparation, or bulk archiving while timings are active. Historical frozen executable copies were deliberately removed; rebuilt hashes need not match the archived binaries.

## 2. Make policy explicit throughout the existing infrastructure

Make narrow infrastructure changes, keeping runtime/workload code fixed:

1. Add validated `--effect-policy {final,live}` options to application `study.py`, `launch.py`, and synthetic `study.py`; retain final as the compatibility default. Pass the explicit value into each candidate execution. Wire image background execution through the same option.
2. Save requested and effective policy in configuration, provenance, sequence setup, sample metadata and reports. Ensure the frozen wrapper receives live and the actual candidate binary accepts it. Require agreement between configuration and execution evidence in the monitor/audits.
3. Add policy to application resume matching and `cohort_report.py::fingerprint`, plus synthetic audit checks. Reject mixing policies even when the harness/source hashes match. Reject missing policy in new campaigns; interpret old evidence only through its documented setup/provenance rather than guessing from a directory name.
4. Replace cache-entry-only instrumentation verdicts with distinct evidence for backend execution, cacheability and reuse. The application harness currently marks an all-zero-cache Observe sequence as bypass; the synthetic audit's nine artifact-generation cold samples already triggered this problem due to extended attributes. A correctly traced live execution can be uncacheable. Keep warnings and raw counts, require separate untimed backend-profile evidence, and never turn an unexplained zero count into a silent pass or a reuse claim.
5. Preserve native validation, fdguard, script-coverage checks and all paired-order rules. Profiling remains confined to pilots. Live-mode slowness is a result, not grounds to enable annotations, change input sizes, or drop cases.
6. Give final collectors/exporters explicit source/destination and policy labels. The current final collector writes the historical result locations; do not run it unmodified against new evidence. Keep the existing paper dataset intact and export live results separately.

Tests must establish policy propagation through the frozen launch path, conflict rejection on resume/reporting, rejection of mixed policies, actual Observe backend use despite inherited instrumentation descriptors, and preservation of historical default behavior.

## 3. Use one serial background controller around the maintained runners

The existing robust components are `paper-size-benchmarks/harness/common.py::supervise`, application `study.py`, `launch.py`, `monitor.py`, `cleanup.py`, and the synthetic harness. There is no general all-suite robust orchestrator entry point in these checkouts. Extend these components with a small durable serial controller instead of recreating measurement/validation logic.

The controller should own a campaign manifest, immutable queue, status JSON, event log, service name and a single campaign lock. Integrate a shared measurement lock into every participating entry point so a separately launched application, image or synthetic job cannot overlap. Existing application and synthetic locks protect different paths, and the image runner's wait-on-one-service logic does not provide general exclusion. Specify lock ownership/delegation to avoid a parent holding a lock that its child tries to acquire again.

Use the existing systemd user-service pattern with lingering enabled, explicit absolute Python/Cargo/dependency paths, durable stdout/stderr logs, `KillMode=control-group`, and `Restart=no`. Retain per-invocation supervision, deadlines, descendant adoption/reaping and failure receipts. Set a measured, adequate stop grace period so cleanup can finish before systemd's final kill; verify this with fault injection. Service execution survives editor/chat/SSH closure, but a transient service does not automatically resume after reboot or host shutdown. Record interrupted state and require an explicit recovery action.

Queue stages: preflight → qualification → live pilots → one application family at a time (prepare, run all paired repetitions, audit, release) → synthetic final matrix → separately configured image study → optional supplemental extension → final audits/export → owned cleanup. Persist successful gates before proceeding. A failed correctness/resource/instrumentation gate stops the campaign and leaves the failed attempt labelled; no automatic retry, promotion, or restart of old cancelled cohorts.

Make monitor service identity configurable: it currently checks the fixed `incr-bench-study.service`. Use lightweight status/heartbeat checks during execution and complete evidence audits between stages. The supervisor updates long-running invocations roughly every ten seconds; monitor setup/validation stages too so stale-status checks do not mistake legitimate preparation for a hung timing. Save terminal systemd status because `--collect` can remove a completed unit.

Before a full launch, verify a tiny service survives launcher exit, stop kills the complete process tree, failures stop subsequent stages, and duplicate launches fail without touching existing evidence. Publish exact status/log/stop commands using the campaign's selected unit name.

## 4. Qualify live semantics and instrumentation before full timings

Run maintained component tests and the policy matrix serially, explicitly covering live. Run full Bash cold/warm correctness configurations with the intended policy and benchmark assumptions. Preserve documented comparison normalizations; do not reuse final-policy qualification as proof of live-policy execution.

Run all 276 deterministic application minimum invocations (92 versions × three modes, one repetition), with real DPT models. Include supplemental's 15 minimum invocations only when that extension is enabled. Exercise live effect ordering/shared-file/FIFO behavior using existing regressions; final-output equality alone cannot prove preservation of intermediate effects.

Pilot all 17 synthetics at small scale with diagnostic backend profiles, then representative medium/large cases to establish space/deadline feasibility. Preserve complete static instrumentation checks and exclude pilot profiles from final timings. Reproduce/label the install extended-attribute barrier and distinguish traced execution from actual cache hits. Do not weaken the current audit just to obtain a green summary.

Image API needs fresh isolated credentials and a fresh live-policy minimum gate (21 invocations). Do not reuse the old final-policy checkpoint via `INCR_IMAGE_REUSE_API_MINIMUM`. Keep credentials outside Git and logs; preserve the collision regression and payload-based validation. Its results depend on provider/model behavior and remain separate from deterministic equality claims.

## 5. Bound disk use and keep state clean

Retain the application 32 GiB workspace budget and 8 GiB free reserve, and the synthetic 8 GiB workspace budget plus 8 GiB reserve. These are sampled guards, not filesystem quotas: free space is checked roughly every second and workspace allocation about every ten seconds during long calls. Add campaign-level accounting for evidence, download staging, models, build artifacts, package caches and temporary files outside a child's WORK tree. Check free space before preparation, validation, packaging and transitions as well as timing.

Prepare one full application family at a time, outside timers; keep one immutable prepared input plus the active mode fixture/cache. Retain cache and outputs across the ordered versions within each mode/repetition; start each new mode/repetition with a fresh fixture/cache. Cold means an empty Incr cache, not a flushed OS page cache. Do not add global cache flushes.

Use the bounded historical recipes: avoid generic 17.8/22.4 GB NLP/weather archives, recursive downloads, and cumulative beginner input doubling. Record actual selected bytes. Budget DPT weights/framework installation and supplemental's 10 GB corpus separately before their stages; 50 GiB currently free is not a guarantee that every dependency plus dataset fits simultaneously.

After durable validation/audit, release the completed family's prepared inputs and owned fixture/cache. Retain shared models/toolchains as prerequisites while needed. Use cleanup's dry-run inventory and receipts; reject mounted trees/path escapes and preserve `.recovery` state for inspection. The current cleanup script covers paper inputs/downloads and explicitly selected builds, but not every job snapshot, min/full tree or synthetic-owned artifact: extend explicit ownership coverage rather than adding a broad deletion command.

Retain timing/resource records, statuses, logs, input manifests, source snapshots, frozen hashes, failed-attempt diagnostics and synthetic raw capture evidence. Package/hash-verify between timed stages, then remove only verified duplicates and explicitly disposable large state. Never delete caches midway through a development episode to meet a budget; fail and diagnose instead. Record final mount/process/service inventory and storage before/after cleanup. No recurring monitor timers should be left behind.

## 6. Acceptance and comparison

Require exact matrix coverage, three complete paired repetitions per mode, finite positive times, successful native validation, policy agreement, unchanged inputs/sources where required, no surviving descendants, and complete resource/provenance records. Keep incomplete/failed cohorts out of full-sequence aggregates while retaining their evidence.

Report each repetition, median/mean/spread, cold execution, unchanged phase where applicable, re-execution and edited totals, whole-sequence totals, all slowdowns and sampled space/resource metrics. Application re-execution excludes the first version; synthetic re-execution excludes cold, while edited totals exclude both cold and unchanged. RSS is maximum single-process RSS; sampled disk peaks are not exact instantaneous maxima. Three repetitions support descriptive comparisons, not broad significance claims.

The primary fresh comparison is Bash vs original vs Observe/live on this reconstructed environment. Comparing these numbers with the archived final-policy results also includes environment/time drift. To attribute a difference specifically to effect policy, add a separately labelled fresh final-policy control using the same frozen binaries, inputs and host, with a predefined paired/counterbalanced schedule. Do not silently double the requested scope or mix that control with the live cohort.

Completion means verified live evidence and a separate report/export, plus a cleanup receipt and no active worker. Implementation, dependency setup, qualification and launch remain future steps of this plan.
