# Observe performance regression investigation

Current checkpoint (October 14, 2026, America/New_York): command-specific sort
execution and the new cut annotation have been removed at the user's request.
Only general execution/tracing/cache/frontend optimization is authorized going
forward. Earlier measurements below retain their original implementation scope;
they do not qualify the revised source. See the
[active handoff](../paper-size-benchmarks/ACTIVE_GOAL_HANDOFF.md).


Current comparison policy: static pure/read-only/stateless performance annotations
are disabled by default in both original Incr and Incr+Observe. The existing `-a`
option now gates those shortcuts as well as chunking. Learned introspection and
semantic native execution remain part of each implementation. Prior comparisons
with unequal annotation coverage are diagnostic only. Finish the unannotated
end-to-end evaluation first; a comparison with annotations on both sides is deferred.

`general-unannotated-one-01` passes 84/84 exact comparisons across two repetitions
of 1 MiB repeated-record fixtures, with unchanged provenance. Whole-sequence
original/Observe ratios: word frequency 2.253x, Poet 8.836x, COVID 14.928x,
weather 13.029x. The native frontend and explicit directory-access assumption
were enabled. These are synthetic diagnostics, not historical-size qualification.
The finite-stdin prototype was removed: although component sort timing improved,
`general-finite-eight-01` showed worse complete pipelines from lost overlap.

Persistent objective: make Observe significantly faster than original Incr across
all included benchmark families while preserving Bash-equivalent outputs and the
existing correctness fixes. Do not treat unsafe reuse or invalid baseline output
as a speedup. The interrupted historical-size run and its evidence remain intact.

Workflow:
1. Small serial probes compare Bash, pinned original Incr, current Incr using try,
   and current Incr using Observe, all under stable environments and final policy.
2. Compare pre-audit implementations from history in isolated checkouts; older
   outputs are diagnostic evidence, never the correctness oracle.
3. Attribute overhead using profiles and focused probes. Add correctness
   regressions for changed behavior, then run focused tests and broader checks.
4. Expand the small benchmark-family matrix, including cold starts and complete
   ordered development sequences. Keep per-edit and total-sequence metrics separate.
5. Once evidence supports clear improvements for every family, explicitly prepare
   and launch one full-size repetition. Investigate and iterate on any performance
   regression or correctness failure. Do not mark the goal achieved prematurely.

`harness/micro.py --id <unique-id>` runs 32 small cold/warm probes sequentially
without downloading data. It compares exact stdout and output-file hashes to Bash.
Its process-tree supervisor has a 20-second deadline, an 8 GiB disk reserve, and a
32 GiB workspace budget. Command timing is recorded separately from supervisor
polling overhead. Cache and capture paths are outside application working data.
These single-sample probes locate bottlenecks; they are not publication results.

Initial evidence: `baseline-02` passes all 32 probes. `baseline-01` used coarse
supervisor timing and is retained only as initial correctness evidence. No runtime
correctness checks have been removed or relaxed.

## Findings and changes in progress

- `candidates-before` vs `candidates-after`: skip pre-execution candidate scans for
  statically pure commands. Their selected cache entry is still integrity-checked
  after hashing stdin and before replay. Median warm time in the 8 MiB multi-input
  probe decreased from approximately 56 ms to 30 ms; original Incr remains about
  23–24 ms. This is progress, not the all-family goal.
- `crypto-large-before`: 128 MiB salted encryption corrupts the warm output in
  both original and current Observe streaming replay. `crypto-large-after` passes
  all four cold/warm encryptions after making `openssl enc` execute fresh. This
  narrow correctness fix is applied identically to the candidate and original
  baseline; the baseline patch is retained in the historical-size study reference.
- Stream integrity hashing now uses 64 KiB reads with explicit interrupted-read
  handling. Its performance contribution is still being measured; checks are kept.
- Supervisor timing now records completion using a waiter thread and excludes
  initial workspace enumeration. An injected slow-inventory test verifies the
  boundary. Fourteen harness fault tests pass.
- A tiny FFmpeg trace exposes an important next investigation: its output pathname
  is recorded as absent before the initial truncating write. The file exists after
  that run, so the dependency can prevent reuse of an otherwise idempotent overwrite.
  Any optimization here must retain permissions, hardlinks, partial writes,
  exclusive creation, and read/modify/write correctness; simply dropping all write
  preconditions would be unsafe.

The full evaluation and monitor remain stopped. Fresh full measurements are gated
on all-family correctness and performance checks, with one repetition selected by
the user. Disposable fixtures/caches and obsolete builds will be cleared before
that evaluation. Compact diagnostic evidence remains separate from disposable work.

## Next checkpoint

`optimization-min-01` passes all 69 comparisons across six benchmark families
with the minimally repaired baseline. Its mixed performance is not a success gate.
The next runtime iteration adds protocol-8 overwrite classification and cache-23
completed-file preconditions in final mode, preserving inode identity during
replay of verified full truncations. Earlier content/existence reads, partial
writes, exclusive creation, entry replacement and changed permissions remain
strict. Empty stdin can now select and validate a cache entry before starting a
speculative child; buffered and delayed pipes retain streaming behavior.

Current checks: 412 Observe integration assertions pass. Focused final/live/batch
regressions pass, including append, permissions, hardlinks, cache corruption,
changed stdin and repeated overwrites. Final timing/performance qualification for
this iteration is still pending. No full evaluation has been relaunched.

`optimization-min-02` passes 27/27 fresh comparisons. Whole-sequence music time is
2.146 s Observe vs 12.443 s repaired original (5.80×); word frequency is 1.828 s
Observe vs 1.316 s original (0.72×). These are single minimum-input repetitions,
not stable full-size results. Music confirms the overwrite/empty-input work helps
an actual family. Word frequency remains the next bottleneck: profile command
startup, tracing, stdin spooling, cache hashing and pipeline overlap before adding
more optimizations. The all-benchmark goal remains active and unachieved.

Before the next full evaluation, repeat owned-workspace cleanup and record its
inventory/free-space evidence. The previous cleanup freed approximately 4.95 GiB;
minimum fixtures and dependency/model installations are reusable setup inputs.

## October 14 follow-up

The known-size stdin-only sort experiment was removed: the 8 MiB, three-repeat
word-frequency probe did not establish a speedup. Sorting continues through the
existing traced executor. No custom sort comparator or weaker dependency checks
are used. Earlier experiment results are diagnostic history, not current behavior.

The streaming spool now returns to its bounded memory queue once its disk backlog
has been fully consumed. The old implementation kept spilling subsequent bytes
for the lifetime of that stream. A concurrent regression verifies ordered delivery,
descriptor release, and subsequent memory buffering. `spool-reset-before` and
`spool-reset-after` each pass all 36 comparisons and their end-of-run provenance
checks; timings do not show a clear improvement. Treat this as reducing avoidable
spill lifetime, not an established speedup.

Dash transformation now defers importing the Bash parser until Bash parsing is
requested. Along with sharing immutable inserted prefix nodes, this avoids work
on each script invocation. `parser-equivalence-01` records identical generated
bytes for all 92 study scripts against the previous transformation. Nine shell
AST tests and all 66 final-mode execution regressions pass. Runtime unit checks
pass 30 tests with one intentionally ignored ownership test. Earlier in this
follow-up, live and compressed batch modes passed their applicable 66 regressions;
those checks precede the final spool/parser changes and should be repeated before
broader qualification.

Small probes now acquire the same exclusive lock as the main study. They record
all source files (including new files), Cargo inputs, shell entrypoints, binaries,
and measurement helpers, then verify those fingerprints after execution. A
mismatch invalidates the summary. New source bytes are archived alongside tracked
patches. A fault test confirms source/entrypoint edits invalidate results. Invalid
case names, result IDs, sizes and repetition counts are rejected before allocating
fixtures. Profiling is opt-in and disabled for performance probes.

`wordfreq-spool-reset-01` and `wordfreq-lazy-parser-01` each pass 18/18 comparisons
at 8 MiB over three repetitions, but Observe is still slower than repaired original
Incr. These small actual-pipeline probes do not meet the all-family performance
gate. The persistent optimization goal remains active; full measurements and the
old monitoring timer remain stopped. Repeat owned-artifact cleanup before the
future fresh one-repetition full evaluation, keeping compact historical evidence
separate from disposable caches, captures, fixtures and builds.

The latest live-mode and compressed-batch checks also pass (one and two expected
skips respectively). `parser-startup-02` passes all 24 paired comparisons with
identical generated output: median transformer time is 116.2 ms before and
112.2 ms after lazy imports. This small startup improvement is not a claim about
whole-benchmark speed. The preceding `parser-startup-01` failed preflight without
running measurements; its failed summary is retained.

`optimization-min-03` freezes the latest runtime/helpers and passes 42/42 native
Bash comparisons across four actual families. Whole-sequence original/Observe
ratios are 6.51× music, 10.47× n-grams, 4.81× uppercase, and 0.80× word frequency.
Word frequency totals 1.583 s Observe vs 1.262 s original. These single minimum
repetitions validate correctness and isolate the remaining regression; do not
extrapolate these ratios to full-size runs. Each mode started with an empty cache,
retained it only across its family's ordered scripts, and cleaned disposable
artifacts afterward. The run ended complete without any failed sequences.

## Bounded buffering and plain byte-sort specialization

The 256 KiB private-pipe experiment was reverted: the paired actual-pipeline
probe did not demonstrate a convincing improvement. Native sort thread-count
experiments also did not beat GNU's default, so no thread override was retained.

The stream queue's memory limit is now 8 MiB per stream, allocated on demand;
larger backlogs still spill to unlinked owned files. In `wordfreq-spool8-paired-01`,
all 24 comparisons and provenance checks pass. Filesystem output blocks decrease
from approximately 219K to 105K per two-script sequence. Mean sequence time improves
about 6% over the 1 MiB queue, with substantial timing noise. The actual minimum
sequence `optimization-min-04` passes 6/6 checks: Observe 1.469 s vs original
1.243 s. This resource improvement alone does not meet the speedup goal.

The current runtime additionally specializes **plain stdin-only `sort`**, with no
arguments, under explicitly selected C/POSIX locale and the installed system-tool
identity. Other flags, file operands, locales, shadowed programs, loader overrides,
live mode, full tracing, batch mode and compression retain their existing paths.
It orders arbitrary byte records, preserves NUL/non-UTF bytes and duplicates,
and adds the terminal newline exactly as GNU sort does. For repeated data, a
bounded randomized dictionary counts full byte records before sorting distinct
records and emitting each count. A mostly unique sample or dictionary limit selects
comparison sorting instead. No custom numeric comparator or locale collation is
implemented. The radix prototype was not integrated because its modest gain did
not justify the additional algorithmic complexity.

Input is bounded at 64 MiB and 8M records; the input/index path uses roughly
128 MiB at its bound. Counting uses at most 512K distinct entries. Allocation
pressure, the input bound or record bound resumes the ordinary traced GNU executor
with every consumed prefix byte preserved. The ordinary path retains its tracing
configuration. Cache output integrity is still verified; specialization entries
have no filesystem effects and do not enter speculative candidate indexes. Cache
format is now 25. This is a general Incr runtime optimization; measurements of
Incr with Observe include it and therefore do not isolate tracer-only speedups.

Evidence: 207 initial and 249 radix diagnostic edge/randomized inputs match GNU
sort. The counted prototype matches the actual minimum text's token stream in all
six timed comparisons; its median is 0.166 s vs GNU 0.597 s. These are standalone
algorithm probes. `optimization-min-05` validates the initial comparison-sort
integration (6/6 correct) but only reaches near parity: Observe 1.259 s vs original
1.293 s. The adaptive counted implementation passes 33 runtime unit tests (one
ownership test intentionally ignored), all 68 final-mode regressions, and an extra
focused warm/corrupt-counted-cache check. Large regressions independently cross
both fallback limits and compare exact output to GNU sort. Live and compressed
batch checks passed before counting was added; their paths exclude specialization.
The fresh combined minimum run is `optimization-min-06`.

Probe drivers now retain per-command CPU, memory, context-switch and output-block
stats and can compare a copied, hashed previous candidate binary using identical
current helpers. Local input copies are hashed and checked. The main study also
archives the three runtime source trees, including newly added files, under each
result's `sources/`; this closes the gap where git diff omitted new source files.
Fifteen harness tests pass, including source-archive inclusion/cache exclusion.
No full-size evaluation has been relaunched. The full all-family performance goal
remains active, and owned caches/artifacts must be cleaned before that fresh run.

`optimization-min-06` passes 42/42 fresh comparisons with adaptive counting.
Whole-sequence original/Observe ratios: music 6.64×, word frequency 1.23×,
n-grams 9.24× and uppercase 4.63×. Word frequency totals 1.040 s Observe vs
1.276 s original. A separate three-repeat actual-text pipeline probe,
`wordfreq-counted-real-01`, passes all 18 comparisons and provenance checks:
Observe mean 1.093 s vs original 1.281 s (1.17×). The modest improvement is
consistent in direction across these three sequences, but remains minimum-input
evidence, not proof of a large historical-size speedup.

The fallback tests were then strengthened to leave unread bytes after the saved
prefix, rather than crossing the limit only at EOF. A two-byte reader unit test
checks both nonempty remaining input and final-record overflow at EOF. End-to-end
regressions use a 65 MiB long record and a record-limit overflow with an additional
128 KiB tail. Both compare exact native GNU output and pass, along with the
counted-cache warm/corruption check. Runtime units still pass 33 tests (one ignored).
Only test bodies changed after min-06; its archived production byte-sort source
matches the current production implementation, although the rebuilt binary hash
differs. A final unified candidate qualification is still required before full eval.

`optimization-min-07` passes 48/48 comparisons on additional minimum families:
poet Observe 0.612 s vs original 0.590 s (0.96×), COVID 0.846 s vs 0.778 s
(0.92×), spelling 1.190 s vs 1.504 s (1.26×). Thus seven families have fresh
correctness evidence, but the all-family performance goal is not met. Poet and
COVID's tiny inputs expose fixed startup costs; inspect their code and profiles
before assuming larger inputs eliminate that gap. Remaining fresh minimum
coverage: nginx-analysis, bio, weather, beginner, unixfun and DPT. No full-size
study or monitoring timer is active. Approximately 42 GiB remains free.

## Follow-up: startup, stdin cut, and byte-order unique sort

Transformer imports now avoid dataclass construction for the private Bash state
container and avoid importing inspect for an ordinary Python method signature
(the decorated/extension fallback retains inspect). `startup-imports-01` runs 24
paired frozen-helper measurements with identical generated bytes: median startup
110.2 ms before vs 100.3 ms after. Nine shell AST tests and all 69 final-mode
regressions pass after the combined changes below.

The old original annotation treated cut broadly as pure; the corrected runtime
had removed that annotation. A narrow C/POSIX stdin-only cut annotation is now
restored for literal byte/character/field selectors and delimiters. File operands,
unknown options, other locales, shadowed tools and loader overrides remain traced.
Native GNU cut still implements the operation. Tests compare binary/unterminated
stdin outputs and prove changed file operands invalidate their cached results.
The bounded byte sorter now additionally supports exactly -u or --unique, without
other options/operands. Plain and counted representations deduplicate exact byte
records; numeric and locale sorting continue through GNU. Focused cold/warm native
comparisons cover the counted unique path as well as corrupt cache payloads.

`optimization-min-08` passes 162/162 comparisons across six families. Total
original/Observe ratios are poet 1.00×, COVID 1.05×, nginx 1.63×, weather 0.91×,
beginner 1.21× and unixfun 1.51×. Tiny weather remains slower and poet/COVID are
near parity; larger-size speedups must not be assumed from these results.

`optimization-min-09` explicitly launches only prepared minimum bio and DPT in
incr-bench-study.service. Bio completes 21/21 checks: original 44.889 s vs Observe
4.482 s (10.01×). DPT uses the real SAM/classifier models; its Bash-reference
sequence was still running at 23:05 UTC, with every completed sample passing.
Read-only five-minute audits run in incr-bench-optimization-monitor.timer using
this run's frozen monitor, and manual audits also report health=ok. Stop this
new timer after the run reaches a terminal state; the old incr-bench-monitor.timer
remains disabled. Do not launch other measurements/builds while the service runs.

DPT diagnosis remains open. Although Observe emits unlink/rename replay barriers,
Incr's existing final policy already filters those two barriers, so their presence
in raw tracer code alone does not explain the regression. Do not weaken these
rules speculatively. Inspect actual saved barriers/dependency failures instead.
`harness/cache_barriers.py` is a read-only fixed-format prefix decoder for live
Observe cache metadata (schema 25); it rejects other live modes and never changes
cache decisions. Use it during the DPT Observe phase before disposable caches are
removed. Remaining barriers (e.g. ownership/timestamp changes or hard links),
strict directory metadata, and environment/input differences are hypotheses until
actual evidence identifies the cause. Full evaluation remains gated and unlaunched.

At 23:08 UTC, min-09 had finished all ten real-model DPT Bash references and
started the original-Incr sequence; all 32 completed samples (including bio) were
valid. The read-only audit was upgraded to preserve schema-25 cache-barrier prefixes
during the live Observe phase before cleanup. The active timer is now
`incr-bench-optimization-audit.timer`, invoking the task-owned wrapper at
`.work/jobs/optimization-min-09/audit.py`. It runs every five minutes and stops
itself on complete/failed/error/interrupted status. The earlier
`incr-bench-optimization-monitor.timer` has been stopped. Monitor history and
cache-audits remain in the min-09 result directory. The study service was confirmed
active with MainPID 1151831; do not start competing tests, builds or measurements
until it is terminal. No runtime/source change has been made during these timings.


The min-09 DPT diagnostic was deliberately stopped at 23:19 UTC after identifying
an actual invalidation defect; it is interrupted, not a completed evaluation.
Both former diagnostic timers were stopped. Python package discovery probes
entry_points.txt beneath regular-file egg-info paths: the kernel returns ENOTDIR.
Observe previously classified these as uncacheable, preventing SAM cache saves.
Protocol 9 / cache schema 26 records NotDirectory distinctly from ENOENT; changing
the parent into a directory must invalidate this dependency. Observe passes
414/414 assertions and Incr passes 70 final regressions, including that transition.

A second defect was measurement namespace interference: sibling capture/cache
creation changed metadata of directories observed by Python realpath. Disposable
runner artifacts now live under .work/runner, separate from .work/fixture;
Matplotlib configuration is outside the application's temporary-file directory.
Directory validation remains strict. Seventeen harness tests pass, including
ancestor metadata stability and bounded cache inventory without sandbox traversal.

sam-imports-enotdir-layout-01 validates 18 real-import probes. The corrected,
isolated layout replays in about 14 ms versus roughly 12 seconds cold.
sam-model-isolated-01 validates actual one-image SAM outputs against native Python:
native 55.226 s, Observe cold 65.008 s, Observe warm 0.0221 s, all three exact.
These are single-stage results, not a completed DPT sequence or full evaluation.

optimization-min-10 completes 246/246 valid comparisons across all twelve non-DPT
families using the same current frozen build. Total original/Observe ratios:
bio 11.01x, file-mod 6.83x, ngrams 9.97x, uppercase 4.97x, word frequency 1.46x,
nginx 1.70x, spell 1.39x, beginner 1.20x, unixfun 1.48x, COVID approximately 1.00x,
poet 0.88x and weather 0.97x. The speedup goal remains unmet. One repetition does
not establish significance, and minimum timings do not establish full-size gains.

At 23:52 UTC optimization-min-11 explicitly launches only the full minimum DPT
sequence, one repetition, in incr-bench-study.service. It recreates native Bash
references and checks original and Observe serially with fresh per-mode caches.
The task-owned five-minute incr-bench-optimization-audit.timer rechecks durable
validation/resource evidence and captures cache dependency diagnostics; its wrapper
stops the timer on terminal study status. No builds or other measurements may run
concurrently. Full historical-size evaluation remains gated and unlaunched.


Correction to the preceding launch checkpoint: min-11 failed in preflight before
any measurements because user-systemd did not inherit the invoking shell's Cargo
PATH. launch.py now explicitly preserves PATH. All 18 harness tests pass,
including a mocked systemd-launch regression for the dependency search path.
The replacement is optimization-min-12, launched at 23:52 UTC; manual audit reports
health=ok with its first real-model native reference running. Its five-minute audit
wrapper explicitly sets INCR_BENCH_STUDY before importing frozen helpers and stops
the timer in finally on terminal status. The first audit attempt during source
freezing preceded status.json creation; the subsequent audit succeeded. min-11
retains error evidence and must never be counted as a measurement result.


During min-12, read-only audits identified a reporting bug: monitor previously
called a preflight error healthy if there were no failed sample rows. The live
source monitor now treats error/failed/interrupted/unknown states as attention and
cross-checks terminal complete against durable summary and actual sample counts.
Read-only checks against real min-10 and min-11 evidence give health=ok (246 valid)
and health=attention (preflight error), respectively. Two focused fault tests were
added; run the full harness suite AFTER min-12 terminates, without competing with
measurements. The running job and timer retain their frozen earlier monitor;
no measured runtime or frozen helper has been changed. At 23:57 UTC all four
completed min-12 references pass; the service is live and heartbeat current.


While min-12 continues serially, cleanup.py adds a separate explicit, dry-run-first
maintenance stage for the fresh evaluation. It shares the nonblocking study lock,
plans both legacy and new runner artifacts, refuses retained recovery snapshots,
and preserves results/source archives, minimum inputs, model weights and jobs.
Optional historical input/download removal and explicitly named obsolete build
removal are recorded under results/maintenance with partial-failure evidence.
Two additional fault tests cover non-mutating plans, recovery refusal, evidence
preservation and symlink-parent escapes. All four newly added tests (two monitor,
two cleanup) remain pending until the measured ML service terminates. No cleanup
has been applied during min-12. At 00:00 UTC seven ML references had passed.


Min-12 was deliberately interrupted at 00:11 UTC after 23/30 valid samples:
all ten native references, all ten original versions, and the first three Observe
versions. Observe's third version still took 70.523 s rather than reusing SAM.
Live cache audits show ENOTDIR is fixed and entries are saved, but the shared
fixture/tmp directory changes between the independent PyTorch and TensorFlow
stages. This is additional interference, not evidence that the earlier isolated
SAM replay result was incorrect. Both service and timer were stopped before tests.

All 22 harness fault tests pass after the monitor/cleanup changes. The new
harness/temp_interference.py isolates imports without inference and keeps full
provenance. torch-temp-interference-01 passes 8/8 stages: ordinary SAM cold
12.378 s, after native TensorFlow import SAM repeats in 12.240 s; with an explicit
TORCHINDUCTOR_CACHE_DIR outside TMPDIR, cold 12.582 s and warm after TensorFlow
0.0151 s. Directory audit confirms the shared-temp mismatch only in the default
case. Protocol/dependency checks were not weakened.

The study now precreates fixture/config/torch and sets TORCHINDUCTOR_CACHE_DIR
there for ALL three DPT modes. It is disposable fixture state, reset between mode
sequences. The additional environment-layout unit test passes. cleanup.py was
manually planned and applied without an active measurement; evidence is
results/maintenance/cleanup-20261015T001434Z-1313394.json. Historical data/downloads
and all runner artifacts were selected; compact results, builds, source archives,
minimum fixtures and immutable model weights remain.

optimization-min-13 explicitly launches the complete minimum DPT sequence at
00:14 UTC, one repetition, all three modes and freshly created native references.
A five-minute incr-bench-optimization-audit.timer invokes its frozen monitor and
read-only cache audit, stopping on terminal state. Treat min-13 as active until
verified terminal; run no builds or other measurements concurrently. Full-size
evaluation remains unlaunched, and the all-benchmark speedup objective remains open.


optimization-min-13 completes at 00:34 UTC: 30/30 valid real-model DPT comparisons,
including exact native PNG validation. Totals: Bash 589.078 s, original 291.981 s,
Observe 273.992 s (1.066x overall). Later Observe versions take 15.8--18.4 s,
versus original 17.4--21.1 s. The compiler-cache namespace fix restores SAM reuse,
but classifier reexecution remains expensive; this is not significant all-family
success. A point-in-time selected-file metadata audit identifies the rewritten
working image as the classifier mismatch, with no SAM metadata mismatches. Keep
its metadata validation strict. Both the study service and self-stopping audit
timer are inactive before starting further probes.

OPTIMIZATION_VALIDATION.json records all 276 valid minimum comparisons from min-10
and min-13. Non-harness frozen binaries, helpers and benchmark source hashes are
identical across the two runs; DPT alone has the documented framework-cache
namespace environment fix. This ledger proves minimum correctness only, and
explicitly records performance_goal_achieved=false and no full evaluation launch.

framework-cpu-profile-01 is a sequential diagnostic CPU-sampling run of the real
framework-import probe, including traced TensorFlow via --trace-tensorflow.
perf samples user cycles with inherited stacks; these profiled timings must not
be used as headline measurements. Probe output/status and source provenance checks
remain enabled. Inspect its actual exec session/process before restarting it.


framework-cpu-profile-01 completes with 8/8 valid stages and unchanged provenance.
Its raw perf.data and observe-user-cycles.txt are retained in that result directory;
the disposable profiling workspace was removed. No lost samples were reported.
Among Observe user-cycle samples, Path hashing accounts for 16.23%, DefaultHasher
writes 13.80%, and repeated path-map insertion/component parsing/allocation are
additional visible costs. These are tracer-only proportions, not whole-workload
costs. Python/OpenBLAS worker spinning is also visible in the combined profile.

TracerState's parent walk now visits only new ancestors, stopping at already
visited nodes instead of cloning/hashing every full chain repeatedly. Existing
nodes already scheduled their ancestors and symlink targets, so first dependency
states remain intact. A focused unit test covers symlink target ancestors,
repeated sibling lookups, and upgrading traversal-only state after a direct stat.
All 7 Rust units and 414/414 integration assertions pass for this change.

Serial, unprofiled parent-walk-before-01 versus parent-walk-after-01 uses a copied
Observe binary from min-13 versus the new binary, with the same helper and explicit
framework-cache layout. All 8 stages pass with unchanged provenance. SAM cold
12.3004 -> 11.6647 s, TensorFlow import 13.2881 -> 12.8797 s; warm SAM 15.1 ->
14.5 ms. This is a preliminary single pair, not significance evidence. A separate
parent-walk-blas1-01 passes 4/4 stages: SAM cold 11.8066 s, TensorFlow 12.6876 s,
warm 13.7 ms. Explicit single-worker OpenBLAS shows no clear substantial benefit;
no OpenBLAS setting was added to the benchmark environment.

The all-family minimum ledger records the earlier frozen min-10/min-13 runtime,
not this newly optimized Observe binary. The next steps remain direct dependency
comparison / Incr regression checks, repeated small performance probes as needed,
and scaled poet/COVID/weather diagnosis before deciding to launch full evaluation.
The study service/audit timer are inactive; no full evaluation has been launched.


The new parent walk also passes all 70 Incr final-mode regressions. The separate
parent-walk-dependencies-01 differential check runs the frozen min-13 tracer and
new tracer on identical symlink traversal, missing ENOENT/ENOTDIR children,
repeated alias/canonical reads and a direct directory stat. Complete JSON reports
match exactly (77 dependencies), as do stdout/stderr/status. Raw reports and binary
hashes remain in that result directory. No dependency metadata was relaxed.

Next performance investigations should target scaled poet/COVID/weather rather
than extrapolate tiny startup-dominated timings. A concrete candidate is bounded
counted sorting for numeric/reverse GNU sort: count exact duplicate byte records,
let the real installed GNU sort order unique records with the original flags,
then expand multiplicities. This preserves GNU numeric/tie-break behavior for
strictly validated stdin-only, C/POSIX, non-stable/non-unique flags; reject -s/-u,
random/debug/check/merge/output-file/record-separator/compressor options and file
operands. Need rigorous binary, numeric edge, cold/warm, error, allocation/input
limit and fallback tests before adoption. No such numeric optimization exists yet.
The current 64 MiB / 8M-record byte-sort bound means larger poet/spell streams
fall back to GNU; investigate a justified higher bounded-memory threshold on this
64 GiB machine before assuming cold sorting gains extend to historical sizes.
Do not silently mark GNU sort pure or ignore image timestamp dependencies merely
to improve ratios. Preserve strict checks; direct full-size measurements remain
necessary after controlled scaling probes. All services/timers are currently
inactive, and the persistent speedup goal remains active and incomplete.


harness/scale.py is an explicit serial diagnostic stage, reusing the production
study's freeze, per-version Bash oracle, filesystem validators, statistics and
per-mode cleanup. It repeats complete minimum-fixture records (adding a missing
terminal newline) to a requested size, stores source/input hashes, and labels its
profile scaled. It cannot establish historical-size results or realistic text
vocabulary scaling. Original minimum inputs are never modified.
scaled-eight-01 completes 36/36 valid comparisons with unchanged provenance:
poet original 2.0869 s vs Observe 1.2077 s (1.728x); COVID 1.3712 vs 1.4311 s
(0.958x); weather 0.5933 vs 0.6247 s (0.950x). Thus poet's tiny slowdown is dominated
by setup, but COVID/weather still require work. scaled-thirtytwo-01 is currently
running in exec session 74121; inspect the handle before restarting. No other
measurement/build/test may overlap it. No full evaluation has been launched.

A second concrete runtime regression candidate is capture_stdin's correctness
poll before every read. Original v1 uses blocking read plus an unbounded mpsc
queue; new Incr uses poll plus a bounded spill queue to avoid hangs and excess
memory. Preserve the latter safeguards. Investigate reopening only FIFO/pipe
stdin via /proc/self/fd/FD with O_RDONLY|O_NONBLOCK|O_CLOEXEC, checking matching
fstat device/inode/type and preserving the original descriptor flags. Read queued
bytes directly; on EAGAIN poll with the existing child-exit/broken-pipe checks.
Do not set O_NONBLOCK on fd 0 itself (shared open-description flags). Check old
access flags first: O_WRONLY/O_PATH must retain their original read errors. If
reopen fails, keep the current poll path. A regular-file read does not need the
readiness poll; preserve the original StdinLock for it. Restrict a new independent
pipe reader to empty-prefix fresh-stdin entry, so prior StdinLock prefetch cannot
lose bytes when resuming a bounded sort fallback. Test original flags unchanged,
shared FIFO byte ordering, CLOEXEC, EAGAIN/EOF, regular/socket fallback, delayed/open
producer early-exit cases and byte-exact fallback before measuring. This is only
an investigation plan; no nonblocking-reader optimization is implemented yet.


scaled-thirtytwo-01 completes 36/36 comparisons with unchanged provenance.
Poet: original 5.9237 s vs Observe 3.2097 s (1.846x); COVID 2.7453 vs 2.8301 s
(0.970x); weather 1.2427 vs 1.2999 s (0.956x). Weather's Observe filesystem-output
counts are 47000/86104/124832 blocks versus original 3536/2832/2008: input-queue
spilling is significant even though it is not the whole timing deficit.

The bounded spool cap is raised from 8 to 64 MiB per stream, still allocated only
for actual backlog and spilling beyond the bound. Five spool tests pass (including
192 MiB forced spill/order validation), as do all 70 Incr final regressions.
scaled-thirtytwo-spool64-01 passes 24/24 comparisons with unchanged provenance.
Weather Observe output blocks fall to 3600/2904/1880 (near original 3536/2624/2256).
Observe elapsed falls to 1.1976 s, but the contemporaneous original is also faster
at 1.0714 s; COVID Observe 2.8962 vs original 2.5325 s. Do not claim an established
speedup from the reduced writes. The retained 64 MiB bound trades more possible
RAM backlog for much less transient disk traffic on this 64 GiB machine.

The independent nonblocking-pipe reader experiment passed two descriptor/FIFO
units and all 70 Incr final regressions. scaled-thirtytwo-nonblocking-01 passed
48/48 comparisons across two independent repetitions with mode order reversed.
COVID original/Observe mean totals 2.6750/2.8205 s; weather 1.1862/1.2665 s.
There was no consistent extra gain; the experiment is REVERTED, including its
reader code/tests. Its exact source/binaries remain archived in that result.
The restored stream_executor.rs came from the pre-experiment spool64 source
archive, preserving all earlier fixes. After rebuilding, the current Incr binary
is byte-identical to the tested scaled-thirtytwo-spool64-01 binary. The 64 MiB
spool change remains; Observe's ancestor optimization remains. No job/timer runs.

The scaling driver now checks raw minimum-source hashes while replicating and
scaled-input hashes before/after each mode. Any integrity failure leaves a failed
sequence marker so a later report cannot present all recorded rows as complete.
These guards were active during the valid 48-comparison nonblocking experiment.

A compiler import-time diagnostic (not a headline measurement) finds cumulative
site setup only 7.3 ms, logging 8.3 ms, argparse 11.4 ms and Shasta AST import 8.0 ms.
Avoid speculative -S/bootstrap changes for a small fraction of startup. A possible
next larger improvement is a native, byte-preserving transformation fast path
using a mature Bash CST parser (e.g. tree-sitter-bash), with fallback to the existing
Python transformer for ambiguous/source-sensitive/binding-changing syntax. Native
command-name insertion must preserve quotes/redirections/assignments, mirror the
existing ignore/executable rules, validate syntax and bound parse/output time.
Prefer an internal mode of the existing Incr binary (no persistent daemon or new
resource-accounting gap), an explicit source-version/capability handshake, and an
opt-in initial integration; do not treat untrusted/custom binaries' arbitrary
stdout as transformed code. Review CLI/source guards, use differential execution
and full shell regressions before any timed run. This frontend is NOT implemented.
Bounded numeric counted sorting and larger plain-sort thresholds also remain only
proposals. Full evaluation and all-family significant speedup are still unproven.


### Native compiler qualification (2026-10-15)

The proposed native frontend is now implemented, default off, enabled explicitly
with `--native-transform` in study/scale commands (`INCR_NATIVE_TRANSFORM=1` in
the wrapper). The restricted tree-sitter Bash CST pass preserves source bytes and
inserts command prefixes. Unsupported constructs fall back to the Python path.
It verifies embedded helper bytes, a capability marker, regular/size-bounded
source, syntax with bounded Bash validation, executable resolution and shell
configuration. An outer timeout covers a hanging custom control binary. This is
a frontend optimization as well as the existing runtime/tracer optimizations;
results must disclose that scope. Native mode is frozen in run configuration and
checked on resume, and appears in the report.

Current validation: 36 Rust tests pass (one ignored), 9 shell AST tests, 70 final
regressions, 6 execution/fallback tests (including a forced hanging control
binary), and 26 harness tests. Logs and current binary/source hashes are saved in
`../paper-size-benchmarks/results/native-transform-validation-01`.

`native-transform-min-01`: 36/36 exact comparisons for poet/COVID/weather,
original/Observe speedups 3.060x / 3.122x / 2.793x. The synthetic repeated-input
32 MiB probe `scaled-thirtytwo-native-01` passes 72/72 comparisons over two
independent repetitions with alternating original/Observe order; provenance is
valid. Speedups are 2.097x / 1.078x / 1.152x respectively. Synthetic scaling is
not the historical dataset and does not establish full-size performance.
`native-transform-min-02` is a newly launched explicit one-repetition check of
all 12 non-DPT minimum families. A five-minute read-only audit timer monitors it.
DPT needs separate current-binary qualification. No fresh full evaluation has
been launched. Significant speedups across all families remain unproven.

The harness now preserves saved status when a duplicate ID or incompatible
resume is rejected, and records preflight failures for automatically generated
IDs. Three regression tests cover ownership of the destination before writing
an error status. Existing raw evidence is preserved. Fresh full evaluation still
requires the separate explicit owned-artifact cleanup, historical preparation,
manual inspection and launch stages.


`native-transform-min-02` completed: 246/246 comparisons, no failed sequences,
all twelve non-DPT families faster in this single minimum-size repetition.
Original/Observe family-total ratios: file-mod 6.131x, word-freq 1.553x,
ngrams 8.175x, poet 3.362x, uppercase 4.015x, COVID 2.844x, nginx 1.690x,
spell 2.720x, bio 10.335x, weather 2.781x, beginner 4.140x, unixfun 4.746x.
The terminal read-only audit passed and stopped its timer. DPT and historical
sizes are not covered by this result. The next explicit diagnostic is
`scaled-128-native-bound64-01` (128 MiB repeated minimum records, one repetition),
which measures the existing 64 MiB sort bound before any change to that bound.


The 128 MiB probe `scaled-128-native-bound64-01` completed with 36/36 valid
comparisons and unchanged provenance. Original/Observe ratios were Poet 0.673x,
COVID 0.829x and weather 0.958x: all slower. This is synthetic scaling, not the
historical dataset. The subsequent checkpoint removes the sort-specific executor
and cut annotation rather than extending the command-specific optimization plan.
Fresh qualification must measure the general implementation.
