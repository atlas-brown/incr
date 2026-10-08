# Incr + Observe minimum-size qualification

Persistent goal: deliver correct, maintainable Incr with Observe, preserving streaming,
batching, chunking, compression, introspection, short-circuiting and cache reuse;
qualify shared-file/FIFO interactions, Bash semantics and main-branch parity;
run all real minimum-size benchmarks except image annotation (user exclusion) and save cold/warm comparisons. Larger inputs
are deferred. Unexplained differences, skipped cases and timeouts are not passes.

## Checklist
- [x] Pin baseline revisions (see results/2026-10-07/revisions.txt).
- [x] Add bounded process-tree supervisor and fail-closed qualification reporting.
- [x] Audit/fix branch parity, tracing, dependency keys, replay and process lifecycle.
- [x] Fix empty-directory replay and qualify filesystem effects and interactions.
- [x] Add focused regression tests for confirmed defects, running them first.
- [x] Pass Observe tests, Incr tests and Bash equivalence suite (per-case deadlines; native clock-boundary recheck documented).
- [x] Inventory benchmarks from both branches; reconcile every script.
- [x] Install real minimum-size dependencies and validate all benchmark outputs.
- [x] Measure Bash, pinned main, updated try/strace, updated Observe: 3 ordinary cold/warm pairs; 1 real-model DPT pair per variant.
- [x] Save raw timing/validation data, medians, variability, speedups, and report.
- [x] Run compiler/style checks and remove only owned temporary execution artifacts.

## Execution policy
Use 30s focused-test, 120s Bash-case, 300s ordinary benchmark, 900s model/API
benchmark, and 1200s setup deadlines. TERM then KILL after 5s; terminate descendants
including separate process groups. No unattended stdin or interactive sudo. Report
progress at least every 30s. Diagnose one bounded reproduction before retrying; never
wait indefinitely or silently inflate a timeout. Preserve evidence and continue
independent work when external dependencies block a case. Cleanup only owned paths.

## Correctness contract
Bash is the reference, not an incorrect main-branch result. Compare stdout/stderr,
exit status and filesystem manifests, including deletions, empty directories, links,
metadata and input invalidation. Require proven cache hits. Preserve live visibility
for interacting commands and prevent speculative rollback/replay from corrupting
another command's effects. Do not globally replace streaming with batch execution.

## Measurement contract
Pin revisions and dependency versions; use equivalent initial state and paths,
separate backend caches, serial rotated mode order, 3 independent ordinary cold/warm pairs. DPT uses one
cold/warm pair per mode and variant because one real image requires about two
minutes of model inference per invocation; report those as single samples.
Exclude setup from timings. Exact comparisons for deterministic cases;
image annotation is excluded at the user’s request. Missing resources for remaining
benchmarks remain blockers. Save failed cases as well as passes.

User steering: image-annotation is explicitly excluded (no API key); this is not a blocker for the remaining qualification.


## Expanded goal: streaming effects, optimization and full code review

The user expanded the goal after the first source commits. Completing the original
minimum-size matrix is a baseline, not completion of this expanded goal.

- [ ] Finish and publish the current frozen-build qualification, including raw
  measurements and cleanup evidence. Preserve this baseline for comparison.
- [ ] Build tiny deterministic experiments for cache reuse after live writes:
  private output, append/read-modify-write, open descriptors/hardlinks, FIFO and
  shared-file producer/consumer handshakes, concurrent writers, slow/infinite stdin,
  and stdin-dependent output. Demonstrate the safety boundary of final-file replay.
- [ ] Compare concrete implementation approaches: lookup before effects when input
  is already available; bounded coordination at an effect boundary; operation-level
  replay with applied-prefix accounting; and explicit private-output contracts.
  Reject approaches that hide interactions, deadlock feedback pipelines, duplicate
  effects, or merely disable streaming. Do not silently introduce weaker semantics.
- [ ] Implement useful safe effectful cache reuse, qualify actual cache hits and
  speedups, and retain live execution for cases that cannot be replayed safely.
- [ ] Review every source module in both repositories, record the coverage and
  findings, and simplify dead paths, duplicated code and fragile lifecycle logic.
- [ ] Audit each optimization against pinned main: streaming, batch, chunking,
  compression, annotations, introspection, short-circuiting and concurrent caches.
  Add focused behavioral tests for enabled optimizations and justify any restriction.
- [ ] Run the full fast regression matrix and shell/Observe suites on stabilized
  code, then rerun all minimum-size benchmark correctness and timing comparisons.
- [ ] Commit and push tested source and final curated evidence with brief subject-only
  messages (Observe main, Incr observe); remove owned execution artifacts and verify
  no owned mounts/processes remain. Preserve reusable dependencies and models.

Iteration policy: use tiny fixtures and per-test process-tree deadlines for design
experiments. Build only changed code, run the smallest relevant tests first, then
broaden after a coherent change passes. Do not repeatedly run the real DPT models
during development. Keep expensive final timings serial and run them only after the
implementation stabilizes. Record measurements and failures rather than inferring
cache hits from runtime alone. Image annotation remains excluded; full-size inputs
remain deferred.


User policy clarification: aggressively install cached regular-file contents whenever
possible, even when correctness relies on only final outputs mattering. This authorizes
an explicit final-output policy that does not preserve intermediate file observations.
Retain and test a live-interaction policy for FIFO/shared-file handshakes. Tests and
reports must identify the policy; do not present final-output equivalence as universal
interaction equivalence. Validate pre-write inputs, quiesce/terminate writers before
installation, preserve meaningful final file semantics, and demonstrate actual reuse.
