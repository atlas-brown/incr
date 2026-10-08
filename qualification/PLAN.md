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
- [ ] Install real minimum-size dependencies and validate all benchmark outputs.
- [ ] Measure Bash, pinned main, updated try/strace, updated Observe: 3 ordinary cold/warm pairs; 1 real-model DPT pair per variant.
- [ ] Save raw timing/validation data, medians, variability, speedups, and report.
- [ ] Run compiler/style checks and remove only owned temporary execution artifacts.

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
