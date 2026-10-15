# Active unannotated evaluation handoff

The persistent goal remains active. Implementation and qualification have passed;
the qualification checkpoint must be committed and pushed in BOTH repositories
before launching the final full evaluations. No measurement jobs are live at this
checkpoint. Diagnostic results must not be pooled into final evaluation statistics.

See REPLAY_QUALIFIED_CHECKPOINT.json and checkpoint-evidence/replay-qualified/manifest.json.
The prior REPLAY_REUSE_CHECKPOINT.json and its evidence retain implementation tests
and failed diagnostics. All archived members have verified SHA256 hashes.

## Qualified implementation

Implementation parents: Incr observe branch 7d77b1900a5e014b7587006247163c9e48423126;
Observe main branch ec35e0ea8f379a694f6e9b1b257da623b7cbb134. Release binary hashes
are recorded in the qualification JSON. Cache format33, effects manifest4,
guarded-descriptor protocol12. This checkpoint changes evidence/documentation only.

General changes preserve replay mtimes, distinguish tracer write-precondition
checksums from program reads, guard inherited read-only regular descriptors, and
make cancellation/rollback reliable. No benchmark-specific command replacements.
The conservative descriptor cache key can cause extra misses when an inherited
file is unused; cross-context reuse remains unimplemented and requires proof.

Benchmark policy: annotations OFF in both engines, native frontend,
directory-access assumption, content-validated workspace inputs, disposable
temporary paths, final effects. Strict defaults remain available. Original Incr
is frozen at4b8e5dd in ../incr-main-qualification with exactly the recorded
reference/original-minimal-fixes.patch; do not modify that baseline checkout.

## Completed qualification

- Full maintained Bash: defaults83/83 cold/warm,668 source files; benchmark
  configuration82/82 cold/warm,625 source files. Both focused regression policies
  pass; live has one existing policy-specific skip. First printf clock-boundary
  failure retained; unchanged entire rerun passed.
- Incr Rust37 plus explicitly run foreign-ownership case; Observe Rust8;
  strict Clippy both; tracer integration435 assertions including200 cancellation
  cases; focused final73/live72+1skip; guarded descriptors6 groups.
- All13 historical minimum families:276/276 exact comparisons, healthy monitor.
  Observe beats original on every whole-family total. Small native wins retained.
- Supplemental minimum:30/30, two paired repetitions, healthy monitor. Observe
  beats original on web-search4.95–5.00x and weather-tufte1.77–1.80x, but both
  remain slower than Bash at minimum size.
- Four synthetic128MiB families:84/84, two paired repetitions, healthy monitor.
  Original/Observe: word-freq1.056–1.075, poet1.089–1.162,
  covid1.774–1.906, weather2.041–2.200. All also beat Bash on sequence totals.
- Real bio scaling:9.83MB21/21,90.87MB42/42(two paired repetitions),
  full706,126,963-byte input21/21(single diagnostic repetition).
  Full sequence Bash291.627s/original260.761s/Observe167.806s.
  Version4-0 remains a regression: Observe68.949s/original50.643s; versions4–6
  recover reuse. All regressions remain in raw per-version evidence.

## Required next steps

1. Review staged evidence/docs, commit and push BOTH repos, verify remote heads
   and clean worktrees. Preserve qualified runtime binary hashes.
2. Start a fresh frozen historical cohort: all13 families,92 script versions,
   three modes, at least3 paired repetitions:828 invocations. Prepared full
   historical inputs are in .work/data/paper; preserve original recipes and DPT
   nested archive paths. Use serial execution, exact independent output checks,
   resource limits and durable monitoring. No builds/tests/preparation during timing.
3. Prepare and evaluate FULL supplemental web-search and weather-tufte separately:
   complete offline corpus/index and all27 cities,30 years, all supplied versions;
   at least3 paired repetitions:45 invocations. Inspect disk reserve before preparing.
   Only image annotation requiring an OpenAI key is excluded. Minimum runs do not count.
4. Use harness/cohort_report.py for matched complete repeated cohorts. Keep raw
   samples/spread, cold/edited/per-version/sequence totals, all slowdowns, actual
   sizes/provenance and historical/native sanity. Do not claim all workloads are
   hugely faster. Preserve interrupted/failed evidence separately.
5. Archive final outputs/provenance/reports, commit/push both repositories, and
   audit every requirement before marking the goal complete.

Ignored results/maintenance/final-evaluation-plan.json contains prepared commands
and explicit launch gates. results/maintenance/active-evaluation.json is the mutable
live handoff; inspect service MainPID and current results before assuming a job is
stopped. Current diagnostic controllers are terminal complete-review-required.
