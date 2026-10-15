# Active evaluation handoff

The persistent goal remains active. Implementation checkpoints are recorded in
Git history. Remaining real-model/supplemental qualification, the final evidence
checkpoint and full evaluations remain open.
Earlier handoff history is retained in Git. This file describes current state.

## Latest state: implementation reopened (2026-10-15)

All prior queues are terminal. Real full-workflow DPT archive diagnostic
`general-dpt-archive-02` validated six outputs but exposed warm Observe 16.323s
versus original 0.631s (native 58.799s). Identical ZIP extraction changes ctime;
original ignores it, Observe correctly invalidates but recomputes the model.
Generic archive fault probe showed simply dropping ctime would allow stale data.

General opt-in `--content-validated-inputs` is now under qualification, NOT final.
Cache format 31, Observe `--content-opens` protocol 11; strict defaults unchanged.
Only successfully opened read-only regular files in the workspace qualify;
content, mtime, size, mode, uid/gid, links/access remain checked. Identity/ctime
drift rehashes bytes; metadata-only dependencies remain strict. No command names.
Both repos compile. Incr Rust: 37 passed, 1 ignored; Observe: 7 units and
424/424 integration assertions pass. Focused batch/final content replacement
regression passes. Generic `general-archive-content-01` proves identical-extract
hits and preserved-mtime changed-content invalidation; baseline stale behavior
is retained explicitly. Real-model `general-dpt-archive-content-01` completed: 6/6 exact outputs,
provenance valid. Native 59.325/58.164s, original 72.124/0.616s, Observe
69.770/0.175s. Warm segment/classify profiles confirm replay (classify validation
19.5ms); see its ANALYSIS.md. This is one sample, not a full performance claim.
The main serial queue completed successfully at
`results/content-inputs-qualification-02/qualification-queue.json`, former PID
2524647/session1886; `/tmp/incr-content-inputs-qualification-queue-02.log`. It passed
stream-final content regression and 31 paper + 7 supplemental harness tests.
The complete 82-group Bash 5.1 corpus passed with benchmark options: 82/82
cold and warm, 11,373/11,373 lines each phase, 73 raw-exact groups; no skips,
variations, native golden differences, timeouts or survivors. Live/final focused
regressions both pass. Independent analysis completed; elapsed 750.769s.
Evidence: `bash-parity-audit-2026-10-08/results/content-inputs-system-bash-full-01`.
The complete 83-group default Bash 5.2 corpus also passed: 83/83 cold and warm,
12,234/12,234 lines each phase, 73 raw-exact groups; no skips, variations,
timeouts or survivors. Native golden differences only builtins/execscript;
live/final regressions pass. Independent analysis completed; elapsed 773.150s.
Evidence: `bash-parity-audit-2026-10-08/results/content-inputs-defaults-full-01`.
The 12 non-DPT minimum families completed: `content-inputs-min-01`, 246/246
valid, no failures, one repetition. Every family is faster than original:
2.292x–18.189x. These remain diagnostics; native Bash still beats tiny new work
in some families. The terminal independent monitor is healthy.
The 8 MiB stage `content-inputs-8-01` completed 84/84 with valid provenance and
healthy monitor (two paired repetitions). Original/Observe ratios WF 2.205,
Poet 2.753, COVID 6.482, weather 9.544; Bash/Observe 2.202, 2.426, 0.735,
1.220 respectively. COVID is still slower than Bash at this modest size.
Actual bytes WF 10,485,770 (same as minimum), Poet 8,389,864, COVID 8,800,000,
weather 8,389,113. The next 32/128 MiB stages provide real WF scaling.
The 32 MiB stage `content-inputs-32-01` completed 84/84 with valid provenance
and healthy monitor (two paired repetitions). Original/Observe ratios WF 1.299,
Poet 1.578, COVID 3.429, weather 3.765; Bash/Observe 2.359, 3.268, 1.400,
1.639. Actual bytes: 41,943,080 / 33,556,194 / 33,600,000 / 33,556,452.
Original is slower than Bash for COVID/weather at this size; keep that visible.
The 128 MiB stage `content-inputs-128-01` completed 84/84 with valid provenance
and healthy independent monitor, two paired repetitions. Actual bytes WF
136,315,010; Poet 134,218,252; COVID 134,400,000; weather 134,220,105.
Original/Observe ratios 1.0776 / 1.1011 / 1.8379 / 1.8471; Bash/Observe
2.5121 / 3.4656 / 1.7775 / 2.2297. Mean sequence seconds:
WF Bash45.237/original19.405/Observe18.007;
Poet106.518/33.844/30.736; COVID13.048/13.492/7.341;
weather6.017/4.985/2.699. Original is faster than Bash on three; COVID is
3.4% slower (near parity). Word-frequency edited-version remains near parity
between Incr engines; do not claim a huge gain where shared I/O dominates.
Main queue PID2524647/session1886 is terminal SUCCESS (08:35:09 UTC). Earlier idle queue 01
was stopped before any stage for a provenance field-name fix; evidence preserved.
The tail queue is now running at
`results/content-inputs-tail-01/qualification-queue.json`, PID 2592299, session
97889; `/tmp/incr-content-inputs-tail-01.log`. Its active stage is all 10 DPT minimum
versions with real models, a three-distinct-JPEG fixed-timestamp archive diagnostic
(two supplied versions, six exact invocations), and two repetitions of both
supplemental minimum families. No automatic commit/push/full evaluation is queued.
The three-image driver and tail queue are archived alongside their status.
Current component evidence is `bash-parity-audit-2026-10-08/results/content-inputs-components`.
Prior 82/83 Bash and all scaling results are previous-source evidence and need
new final-source qualification. The content-input implementation checkpoint is ready; the final evidence
checkpoint and full evaluations remain pending.
Logs: `/tmp/incr-content-inputs-{check,tests,build}.log`,
`/tmp/observe-content-opens-{check,build,unit,integration}.log`.

## User requirements and execution rules

- Finish the complete unannotated comparison first: static annotations disabled
  in BOTH original Incr and Incr+Observe. An equally annotated comparison is later.
- General implementation improvements only. No replacement sort/cut algorithms,
  command-specific performance shortcuts, or benchmark-specific output stripping.
- Retain reasonable original scratch-filesystem assumptions. Benchmark options:
  final effect policy, native shell compiler, directory-access assumption; static
  annotations off. Record all assumptions and actual input bytes.
- Qualify all maintained Bash groups cold and warm, then progressively larger
  inputs and real-model DPT. Commit and push BOTH repositories again before full
  evaluations. Do not overlap builds/tests/measurements or edit guarded sources
  while the serial qualification queue runs.
- Full historical matrix plus separate web-search and Tufte supplemental coverage;
  exclude only image annotation requiring an OpenAI API key. Preserve correctness,
  failures and slowdowns. Compare against native Bash and the original results.
  Investigate substantial Bash regressions rather than calling them minor.
- Full evaluations need a clean owned workspace, frozen sources/binaries/inputs,
  repeated paired samples, exact output checks, resources and durable monitoring.
  Do not substitute diagnostic scaling for historical/full datasets.

## Repositories and implementation

- Incr branch `observe`, pushed first checkpoint:
  `37a8e2886f5c0f05c9a5be4abfb0f4db6e854114` (implementation parent `a14c8c8`).
- Observe branch `main`, pushed first checkpoint:
  `a26e759a86e3ff6f8c3b0e192b8ab23e681e4288`.
- Original baseline: detached `../incr-main-qualification` at
  `4b8e5ddf8e275d947518c7cc0f5d2713fe992307`, with exactly the reviewed
  `reference/original-minimal-fixes.patch`. Salted encryption runs fresh; static
  pure/read-only/stateless shortcuts require `-a`. Doctor verifies that patch.

Candidate cache format is 30. Annotation, scratch and directory policies enter
cache identity. Default scratch excludes /tmp, /var/tmp and non-root absolute
TMPDIR; `--track-temporaries` restores tracking. A canonical-root TMPDIR alias is
not excluded. Directory stat/access can use existence/access/ownership while
listings retain full dependencies; Observe protocol 10 records this explicit
assumption, protocol 9 remains strict/default standalone behavior.

The finite-stdin prototype was removed after whole-pipeline regressions. Old
tracer transport timings were similar to the current tracer. Earlier large
apparent advantages depended on unequal purity annotations, and older correctness
probes failed preserved-mtime edits, files0 lists, parent-link retargets and cache
corruption. Those shortcuts were not restored.

Uncommitted final-source fixes preserve shell source introspection, including
function bodies and extdebug/declare-F locations. Compiler diagnostics/failure
fall back to untouched source, so the selected Bash owns syntax behavior. The
comparator no longer strips printed instrumentation prefixes. It normalizes only
reviewed source locations, diagnostic line numbers and diagnostic PIDs, preserving
signal labels and command text. No arbitrary values or diagnostic order are
normalized. Observe runtime is unchanged; its current design/context docs are
refreshed, with older notes retained under docs/historical-*.md.

## Previous source serial qualification (terminal history)

Controller: tool session **82299**, PID **2223413**. Script:
`/tmp/incr-continue-qualification.py`, archived as
`results/unannotated-checkpoint-01/qualification-queue-final-source.py`.
Authoritative stage/status: `results/unannotated-checkpoint-01/qualification-queue.json`.
Per-stage logs are beside it; outer log `/tmp/incr-continue-qualification.log`.
Verify the actual PID/session before treating a job as live or stopped. Never
restart solely because an observation timed out. The queue guards runtime,
measurement-harness and corpus metadata hashes and stops on failure.

Ordered queue stages:

1. `function-locations-system-bash-full-01` — **passed** all 82 official Bash
   5.1.16 groups on installed /bin/bash 5.1.16, native frontend successfully
   probed, directory assumption enabled, static annotations off.
2. Independent analysis — **passed**: 11,373/11,373 transcript lines in each
   phase, 73 raw-exact groups, no insertions/deletions/replacements, timeouts or
   surviving descendants. Live/final regressions both exit 0. Total 747.984s.
3. `function-locations-defaults-full-01` — **passed** all 83 official Bash
   5.2.37 groups on the verified custom Bash 5.2.37, default configuration.
   Log: `results/unannotated-checkpoint-01/function-locations-default-bash-full.log`.
4. Independent defaults analysis — **passed**: 12,234/12,234 transcript lines
   per phase, 73 raw-exact groups, no timeouts/survivors/skips/variation. Both
   focused regression policies pass. Total 772.056s.
5. `general-unannotated-128-01` — word frequency, Poet, COVID, weather;
   **passed**, 84/84 exact comparisons, unchanged provenance, two paired
   repetitions. Actual inputs: word frequency 136,315,010; Poet 134,218,252;
   COVID 134,400,000; weather 134,220,105 bytes. Original/Observe sequence
   ratios 1.069x / 1.161x / 1.824x / 2.074x. Bash/Observe ratios
   2.683x / 3.460x / 1.765x / 2.256x. Original is faster than Bash on three
   families; COVID is a 3.3% mean slowdown (0.968x), a near-parity case.
6. `general-unannotated-dpt-min-01` — **running**, all ten versions, one real-model
   minimum repetition, followed by terminal monitoring. First native stage took
   60.391 seconds with real SAM inference; do not mistake its CPU work for a stall.
7. Additional profile diagnostic waits for the main queue to complete: session
   **1312**, PID **2431998**, `/tmp/incr-profile-large-pipeline.py`; status
   `results/unannotated-checkpoint-01/pipeline-profile-queue.json`, outer log
   `/tmp/incr-profile-large-pipeline.log`, archived driver beside that status.
   It recreates exactly the larger word-frequency input, validates six invocations
   against native Bash, and enables existing INCR_PROFILE_DIR only as a separate
   diagnostic. No source or primary timing samples are changed. Result ID
   `general-unannotated-profile-128-01`. Inspect per-process phases; nested and
   concurrent phase durations must not be summed as wall time. Correlate profile
   file modification times to invocation end events to distinguish cold/edit.
   Word-frequency edited means: original 1.107s, Observe 1.137s, Bash 23.270s.
   The 2.7% mean difference with two samples is near parity, not a proven
   regression or huge speedup. Explain this from actual phase data before deciding
   whether any general optimization is justified. Do not add command-specific
   workarounds or weaken corruption detection merely to improve a ratio.

The installed shell and official corpus must match major/minor release. The
5.1.16 archive has SHA256
`5bac17218d3911834520dad13cd1f85ab944e1c09ae1aba55906be1f8192f558`, 625 test files,
82 groups; build `qualification/.work/bash-5.1.16`. Custom 5.2.37 retains all 83
maintained groups. Runner/setup accept --corpus-provenance and archive metadata.

Earlier 5.2-corpus-on-5.1 exploration stopped on a native read timeout. Of 68
completed groups, independent comparison matched 66 in each phase; jobs and
quotearray also varied between the native cold/warm runs themselves. Raw evidence
and scope notes remain under `parser-fallback-system-bash-full-01`; it is not final
proof. `version-matched-system-bash-full-01` was intentionally stopped after 45
matching groups to fix function-location introspection before final qualification.
Older prefix-stripping comparison results are explicitly superseded for the gate.

## Completed diagnostics and component evidence

All ratios below are original/Observe whole-sequence time unless stated otherwise.
These runs are diagnostics, not final full-size performance evidence.

- `general-unannotated-min-01`: 246/246 exact comparisons across 12 non-DPT
  historical families, one repetition, healthy terminal monitor; all faster,
  2.336x–20.716x. This predates final shell-only source-preservation fixes.
- `general-unannotated-one-01`: 84/84, two repetitions, unchanged provenance.
  Word frequency 2.253x, Poet 8.836x, COVID 14.928x, weather 13.029x.
- `general-unannotated-eight-01`: 84/84, two repetitions, unchanged provenance.
  Ratios 2.271x/2.925x/5.923x/8.641x respectively. Actual bytes:
  10,485,770 / 8,389,864 / 8,800,000 / 8,389,113.
- Important correction: nominal 1 and 8 MiB used the SAME word-frequency
  minimum, already 10,485,770 bytes. They are not a scaling result for that family.
- `general-unannotated-thirtytwo-01`: 84/84, two repetitions, unchanged provenance.
  Ratios: word frequency 1.237x, Poet 1.492x, COVID 3.308x, weather 3.749x.
  Actual bytes: 41,943,080 / 33,556,194 / 33,600,000 / 33,556,452.
  Bash/Observe sequence ratios: 2.407x / 3.140x / 1.306x / 1.575x.
  Original Incr is slower than Bash for COVID/weather at this size (0.395x/0.420x).
  Word-frequency cold Observe 5.330s vs original 6.301s; edited 0.388s vs original
  0.769s and Bash 7.155s. Keep cold, edited and sequence claims separate.
- `general-unannotated-supplemental-min-01`: 30/30 valid, two repetitions,
  healthy terminal monitor. Web-search 4.921x, Tufte 1.786x. Tufte is slower than
  Bash: new final-version plotting dominates (native 6.929s of a 6.976s sequence,
  Observe 9.938s, original 15.579s). Plotting first appears in version three;
  do not claim reuse of nonexistent prior plots or hide its overhead.

Final source component records and copied logs:
`studies/bash-parity-audit-2026-10-08/results/final-source-components/`.
AST 11 passed; native frontend 8 passed; paper/supplemental harnesses 38 each
passed. The function-location regression failed before the fix and passes now.
The AST script needs its direct entrypoint; an earlier combined module invocation
had an import-path error, corrected by the recorded proper commands. Bash helper
checks pass 20. Earlier implementation qualification passed Rust 36+1 ignored,
final/full 71, live 70+1 skip, compressed batch 69+2 skips; unchanged Observe passed
7 Rust units and 420 integration assertions. Current full Bash runs also rerun
live/final regressions against current sources.

## Next checkpoint and full evaluation

After both queues complete, refresh the unchanged AST/native frontend component
checks serially, then inspect every result and native comparison. Curate previous
function-location raw Bash trials into the indexed local historical retention
while staging the new complete content-inputs 82/83 proof. Investigate
lost speedups or invalid outputs; no automatic commit, push or full launch is
queued. Finalize concise qualification records/report and handoff, stage current
raw Bash evidence with its scope, then make clean simple commits and push BOTH
repositories. Verify remote heads and clean worktrees before full evaluations.

`EVALUATION_PROTOCOL.json` is the full methodology contract. The new supplemental
manifest is separate from historical statistics. Web full uses the entire supplied
offline Wikipedia10g corpus/index, plus a labeled identical-source warm repeat;
Tufte full uses the supplied seed-42 generator, 27 cities and 30*365 days. Node
and modules are frozen. Independent validators cover article visits/postings and
every expected Tufte city-year PNG. Shared models are hash-checked outside timing.
Archived interrupted attempts remain visible but do not invalidate a successful
resumed sequence; current failures still invalidate it (36-test harness evidence).

Inspect and apply `harness/cleanup.py`'s owned plan before historical preparation.
Preserve results, recoveries, source models and required frozen builds. Prepare
full inputs from documented recipes; disclose actual sizes (recipes take precedence
over nominal paper labels). Launch the full historical matrix and supplemental
coverage separately with launch.py/systemd. Start with one full repetition, then
at least two paired followups with reversed engine starting order; add samples for
unstable/borderline results. Raw per-version timings, resource data and exact
native-output validation must remain available. Means alone do not prove a gain.

The old monitor timer is stopped and its service points to historical-eval-02.
Update its target to the actual new run before enabling it. Full workers already
write live heartbeats and enforce disk/process guards. `incr-bench-study.service`
is currently reserved for the later full evaluation; the qualification queue runs
directly. Direct diagnostic monitor checks may report inactive service while live;
terminal checks must be healthy. Do not classify an observed timeout as a dead job.

Review historical differences against `reference/historical-timings.csv` and its
hashed `historical-sequence-sanity.json`. The old sequence data already show
file-mod and unixfun slower than Bash. Reconcile actual inputs, annotations,
hardware and timing semantics; never fabricate agreement or omit current regressions.
