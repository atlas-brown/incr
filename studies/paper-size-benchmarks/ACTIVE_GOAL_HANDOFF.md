# Active unannotated evaluation handoff

The persistent goal is active. Qualification is complete; the final evidence
checkpoint is ready for commit/push, then full evaluation must actually finish.
Do not mark the goal complete at a checkpoint or substitute diagnostics for full
results. No jobs are live and no full-size evaluation of this implementation has
started. The old full attempts are historical, not current performance evidence.

## User requirements

- Finish without static annotations in BOTH engines first; annotated comparison
  is deferred. No command-specific algorithm replacement or performance hack.
- Preserve reasonable original scratch-filesystem assumptions and core reuse.
- All maintained Bash correctness groups must pass cold/warm on final binaries.
- Commit/push BOTH repos before full measurement. Run full historical and separate
  supplemental coverage, excluding only image annotation requiring an API key.
- Exact native-output validation, actual input sizes, frozen sources/binaries,
  repeated paired measurements, resources, progress monitoring, honest regressions.
- Compare against Bash and historical results; never claim huge speedups where
  shared computation/I/O dominates. Investigate substantial discrepancies.

## Current implementation and publication

Branches: Incr `observe`, Observe `main`. Pushed implementation parents:
Incr `5dd1fc3059e5f875cc6fc9620cd76229255e6b4b`,
Observe `a72d5ebc22a13d2566fabd115de2f234f525b685`.
The final uncommitted code changes are lint-only: equivalent range/Option checks,
test placement/conditional, and grouped dependency options at the tracer entry.
Cache format31 and Observe protocol11 are unchanged. No algorithms changed.

Qualified release SHA256:
- Incr `0cf040e55888e84121d725bb8c7e449d5d7409ef0b2b7ff1a25fdfb8ac933961`
- Observe `11e50b5eea0092cde1fcdc5b70f8f296383e03d2f062e92e99e99ee9b5c3507c`

Benchmark policy: final effects, native frontend, directory-access assumption,
content-validated workspace inputs, default disposable temporary paths, annotations
OFF. Content-input identity/ctime drift requires matching bytes and retained
mtime/access metadata; stat/access-only paths remain strict. Strict defaults remain
available. Original baseline is detached `4b8e5dd` in ../incr-main-qualification,
with ONLY reference/original-minimal-fixes.patch; doctor verifies the exact patch.
Do not modify/commit that baseline checkout.

## Verified qualification

See FINAL_UNANNOTATED_CHECKPOINT.json and checkpoint-evidence/manifest.json.
The eleven checksum-verified archives preserve raw validation/timing/source
records and distinguish final binaries, paired pre-style diagnostics and profiles.
Do not pool different binary hashes or diagnostic input sizes.

- Strict Clippy both repos, Rust37+1 explicitly ignored / Observe7, tracer424,
  AST11/native frontend8 pass. Current copied component logs and source hashes:
  ../bash-parity-audit-2026-10-08/results/final-cleanup-components/.
- Final full Bash: final-cleanup-system-bash-full-01,82/82 cold/warm,
  11,373/11,373 lines per phase; final-cleanup-defaults-full-02,83/83 cold/warm,
  12,234/12,234 lines. Independent analysis, no skips/variations/timeouts/survivors;
  both live/final focused regression policies pass. See that study's REPORT.md.
- Default run01 retained one failed native printf cold reference caused by a
  one-second clock boundary; native warm and both Observe runs matched expected.
  The complete fresh run02 passed. No comparison/corpus rules changed.
- Final minimum: final-cleanup-min-01,246/246,12 non-DPT families,1rep; every
  family faster than original,2.15–21.37x. Healthy monitor.
- Final larger: final-cleanup-128-01,42/42,1rep,valid provenance/healthy monitor.
  WF/Poet/COVID/weather original-over-Observe1.102/1.103/1.880/2.067;
  Bash-over-Observe2.569/3.362/1.882/2.356. Actual bytes136,315,010 /
  134,218,252 /134,400,000 /134,220,105. This verifies the rebuilt binary;
  earlier8/32/128 stages have TWO paired repetitions on the pre-style binaries.
- Final model archive: final-cleanup-dpt-archive-01,6/6,one real JPEG, supplied
  versions2/3a,valid provenance/healthy monitor. Native60.921/59.936s,
  original71.707/0.649s,Observe71.501/0.196s. Warm gain3.31x over original;
  whole-sequence near parity because cold model computation dominates.
- Final supplemental: final-cleanup-supplemental-min-01,30/30,2reps,
  healthy monitor. Web Bash1.981/original10.945/Observe2.274s;
  Tufte6.827/18.491/10.304s. Both minimum cases remain slower than Bash.
- Pre-style real-model ten-version minimum30/30 and three-image archive6/6
  also pass; archived separately. The three-image warm time is0.427 vs0.888s
  original, but whole-sequence gain only1.016x. No huge total claim.
- Cache-30 large-pipeline attribution shows cached prefixes replay correctly;
  stdin waiting/spooling/hashing/forwarding dominates warm bulk pipelines.
  Per-process phases overlap and must never be summed as wall time.

## Terminal handles and immediate next work

All qualification queues are terminal. Latest queue03 PID3184365/session63686
completed successfully; results/final-cleanup-qualification-03/qualification-queue.json.
Queue01 and idle queue02 preserve the native-reference failure and retry-driver
history. Do not wait on or restart those old handles.

1. Finish final diff review/format checks, stage current raw Bash results (including
   retained native-clock failure) and component/evidence files, then make a clean
   final commit in EACH repo and push both. Verify ls-remote heads and clean trees.
   Record push receipts under results/maintenance/; prior receipt is
   content-inputs-implementation-push.json. No runtime changes are needed.
2. Inspect and apply harness/cleanup.py's owned plan with --include-inputs before
   full preparation. Preserve evidence, recovery snapshots, shared models, minimum
   inputs and needed frozen builds. Obsolete build IDs must be explicit. Never
   delete recovery state blindly. Recheck resource headroom; reserve8GiB,
   work budget32GiB on a63GiB filesystem (about39GiB currently free).
3. Prepare ALL13 historical families separately using documented paper recipes.
   Record actual bytes; recipes take precedence over ambiguous nominal labels.
   Then launch a fresh full1rep with launch.py/systemd, all3 benchmark options,
   annotations off, immutable snapshots and native oracles. Use unique run IDs.
4. Inspect results and run >=2 further paired repetitions (reverse engine starting
   order) for >=3 total; add samples for unstable/borderline families. Preserve
   exact input fingerprints, source/binary configuration, per-version/sequence
   mean/median/spread and resources. Do not mix unlike sources or datasets.
5. Prepare/run full supplemental separately: entire supplied Wikipedia10g corpus
   and index, and seeded Tufte27cities x30*365days. Complete those evaluations too;
   do not silently drop or downscale them. Record unchanged-source repeats honestly.
6. Review Bash-relative and historical sanity, investigate discrepancies, publish
   complete reports/evidence, then audit every goal requirement before completion.

EVALUATION_PROTOCOL.json is authoritative methodology. Full workers have durable
heartbeat, disk/process guards and model hash checks outside timing. Do not overlap
benchmarks with tests/builds/preparation. Current study service and monitor timer
are inactive; monitor service still targets OLD historical-eval-02. Retarget it to
the actual fresh run before enabling the persistent five-minute monitor. User
linger is enabled. Historical CSV plus historical-sequence-sanity.json retain the
original results; old file-mod and Unix totals were already slower than Bash.
Original historical annotations were enabled, unlike the current fair default.
