# Incr + Observe qualification work log

This is the running log for the user-authorized minimum-size qualification goal.
It will be updated as work proceeds. Detailed historical diagnostics are preserved
in [FINDINGS.md](qualification/results/2026-10-07/FINDINGS.md); this file provides
one readable account of the work, decisions, current status and outstanding tasks.

## Goal and scope

Deliver working Incr with Observe on all minimum-size benchmark entrypoints, with
Bash correctness checks and comparison against pinned Incr main. Audit both codebases,
fix defects on the Observe-side branches, preserve useful incremental execution,
measure cold/warm behavior with and without Observe, and clean owned run artifacts.
Full-size inputs are deferred. The user explicitly excluded image annotation, so
its missing API credential is not a blocker.

- Incr branch: `observe`, starting at `4f8723e60f1cbb5b1b7c614dec162ad43dbaf795`.
- Observe branch: `qualify-incr-observe`, starting at `a95ca6b6cce9c8e7a24e58048d29ffc1a4557d88`.
- Pinned main: `4b8e5ddf8e275d947518c7cc0f5d2713fe992307`, built in the owned sibling worktree
  `incr-main-qualification`. Main remains unchanged.
- Source fixes were committed and pushed on user request: Observe `main` at `b993d58`, Incr `observe` at `7990ee6`. Measurement publication follows the final run.
- No sub-agents were used in this execution.

## How execution is kept bounded

Created `qualification/bounded.py`: a Linux child-subreaper supervisor with explicit
per-command deadlines, 30-second progress heartbeats, TERM/KILL escalation, adopted
child reaping, and saved stdout/stderr hashes, statuses and cleanup diagnostics.
It avoids waiting forever on pipes inherited by descendants. Focused invocations
usually have 5-second deadlines; Bash cases have 120 seconds; ordinary benchmarks
have 300 seconds; real-model DPT runs have 900 seconds. All timing modes run serially.

Created isolated fixture restoration, independent backend caches, immutable runtime
snapshots and raw per-invocation results. Warm restoration preserves unchanged input
inode/ctime. Created inventory, aggregate-report and source/input fingerprint tools.
No timeout, missing case, identical error or unclean process exit counts as a pass.

## Code audit and fixes completed

### Dependencies and cache correctness

- Observe now records first-access filesystem state, including failed opens,
  missing paths, symlink entries and targets, directory state, and write destinations.
- File dependency state includes ctime, mtime, size and mode. This catches content
  changes even when mtime is restored.
- Fixed repeated-creation collisions (`mkdir`, symlink creation and noclobber),
  append/read-modify-write invalidation, and partial writes retaining stale suffixes.
- Added typed effect capture/replay for files, modes, empty directories, symlinks
  and hardlink groups. Validate all saved effect payloads before replaying mutations.
- Added stdout/stderr checksums; missing, truncated or corrupt streams become cache misses.
- Added conservative replay barriers for operations needing inode/metadata history:
  rename, unlink, hard-link creation, ownership/timestamp changes and special files.
  These commands execute live instead of pretending final bytes reproduce the operation.
- Unsupported effect capture prevents reuse without changing a completed live
  command's exit status.
- Added nonblocking per-entry cache locks. Contending invocations use owned transient
  entries rather than waiting on peers that may communicate with them.
- Added umask and executable identity to cache keys. Static annotations apply only
  to resolved system tools; custom PATH programs cannot inherit a pure tool's rules.
- Added direct execution for inherited extra descriptors and non-UTF-8 arguments or
  environment. Lossy filesystem dependency paths are uncacheable.
- Current versions: cache key 12, Observe dependency protocol 3, effect manifest 2.

### Live execution, tracing and process ownership

- Cold Observe execution no longer replays its writes a second time.
- Added a versioned shared effect gate: streaming cache cancellation/replay can win
  only before the first live write; once effects begin the command finishes live.
- Gate termination kills and drains tracees instead of leaving a parked process.
- Added child ownership/reaping and cancellation cleanup; incorporated main's broken
  pipe and sandbox extraction/commit fixes where applicable.
- Poll stdin alongside child completion so an early-exiting consumer does not wait
  forever for a producer to close stdin. Batch remains intentionally finite-input.
- Narrowed unsafe pure/read-only annotations, including file-argument sort and
  general awk/sed behavior. Full tracing and skip-introspection options are honored.
- Moved try's internal ignore file into the owned sandbox runtime path to avoid
  leaking helper files when cancellation happens early.

### Wrapper and Bash semantics

- Replaced in-place source rewriting with an owned real transformed script. The
  caller's script remains byte-for-byte unchanged, including under parallel calls.
- An eval-based prototype was tested, found to change Bash arithmetic/error semantics,
  and discarded. The current implementation executes a real script and preserves $0.
- Preserved script arguments, read-only scripts and paths containing spaces.
- Added native passthrough for source/history introspection, locale-sensitive escapes,
  problematic interpreter modes, invalid syntax and unresolved external commands.
- Preserved arbitrary Unix bytes instead of lossy parser decoding; fixed no-change
  serialization and option handling, including empty/combined -c forms.
- ShellCheck, shell syntax, Python syntax and strict Rust Clippy checks pass.

## Benchmark inventory, setup and repairs

Inventoried 96 benchmark entrypoints: 86 ordinary cases and 10 DPT variants.
Seven image-annotation cases are explicitly excluded by the user. Classified helper
scripts separately so they are neither silently missed nor double-counted.

Installed and verified the actual tools needed by the minimum workloads, including
mergerfs/strace, bio/media/weather utilities, a dedicated Python environment, Node
22.20.0 and web-search dependencies. Node's archive checksum was verified. DPT uses
the real SAM vit_h checkpoint, classifier, label dictionary and one real image;
no model stub substitutes for the real benchmark. Exact versions and fingerprints
are recorded in `qualification/results/2026-10-07/`.

Repairs found in the benchmark code itself:

- Beginner 13: corrected `head 10` to `head -n 10`.
- Bio 1: select a supplied minimum sample instead of a nonexistent hardcoded sample.
- File-mod 7: archive the actual WAV inputs instead of another script's nonexistent gzip outputs.
- Spell 6/7: normalize and sort the dictionary before `comm`; clean the temporary file.
- Web search: initialize output/index state, avoid same-file read/truncate, handle an
  absent global index, reject incomplete padded n-grams, and import only Natural's
  stemmer. Its aggregate import had emitted random dotenv messages into index data.
- DPT 5c/5d/5e: feed formatted classifications to plot readers; save the final plot
  as PNG instead of waiting for an interactive window.
- Raised the minimum shasta dependency to the tested compatible version, 0.5.

Minimum profiles: supplied --min inputs generally; weather plotting is one city-year;
web search processes one real page; DPT uses one real image and the unchanged real models.

## Validation completed before the current timing run

- 35 focused regression cases. Streaming, full-tracing and annotation configurations
  pass all 35; batch and compressed batch pass 33 and omit only the two explicitly
  stream-only infinite/held-open-input cases.
- Observe's complete integration suite: 378 assertions passed.
- Eight existing Incr test scripts passed. The new assertion-based suite gives
  stronger failure detection than scripts that do not consistently use errexit.
- All 83 Bash differential cases matched across the full run plus one documented
  clock-sensitive recheck. Native Bash's printf test alone reported a one-second
  date/builtin-clock mismatch at a second boundary; a single fresh paired rerun
  matched. Both the original evidence and recheck remain saved.
- Independent benchmark component checks verify exactly six complete n-grams from
  three tokens and correct DPT plot-record parsing/PNG production.
- Earlier ordinary validation completed all 86 cases and exposed the benchmark bugs
  above; subsequent focused reruns passed their fixes.
- A real DPT-1 smoke run matched Bash on cold/warm Observe runs. Remaining variants
  still need the final matrix; that smoke run is not full DPT qualification.

## Measurement policy and current run

Compare Bash, pinned main, updated Incr with try/strace, and updated Incr with Observe.
Ordinary cases use three cold/warm pairs in rotated mode order. DPT uses one pair per
variant/mode because even one real image requires substantial inference time; those
results will be labeled single samples. DPT uses eight OpenMP threads on the 16-CPU
host and two TensorFlow threads. Cold means an empty Incr cache, not a flushed OS cache.

An initial timing pass was stopped when the executable-identity audit found another
cache-key issue. Its results remain in `timing-before-executable-identity` and will
not feed final comparisons. The current frozen v12 snapshot is
`bad83b650932aabad3a9`. No concurrent tests or builds run during the timing matrix.

The report will show medians/ranges, matched-case geometric means and summed times.
Invalid main runs are saved and excluded from valid speed comparisons. Several main
warm runs leave strace descendants; the supervisor cleans them and records failure.
The updated backends have not shown that defect in the completed matrix portion.

## Cleanup performed so far

Focused test directories and temporary scripts clean themselves up. Interrupted
process trees have been drained. Before restarting the final matrix, verified that
no owned benchmark mounts or mergerfs processes remained, then removed inactive owned
benchmark caches (including root-owned sandbox leftovers). No global /tmp cleanup
or unrelated user-file deletion was used. Final run fixtures/caches and the owned
main worktree still need cleanup after measurement. Reusable dependencies and model
inputs are separate from temporary execution artifacts.

## Remaining work

- Finish the current 2,064 ordinary measurements and diagnose any candidate mismatch.
- Run all 10 real DPT variants across the four modes, cold/warm: 80 measurements.
- Generate and verify aggregate statistics and the final qualification report.
- Record any limitations, especially conservative replay reducing reuse and the
  lack of full-size memory/performance qualification.
- Clean owned execution artifacts and verify no owned live processes/mounts remain.
- Mark the persistent goal complete only after the agreed minimum qualification is met.

## Ongoing updates

### 2026-10-08 02:53 UTC

Created this consolidated log at the user’s request. The v12 ordinary matrix has
completed 756/2,064 measurements; latest case: `file-mod/file-mod-6.sh`.
Candidate/Bash mismatches recorded so far: 0. Work continues; qualification
is not yet complete.

### 2026-10-08 02:55 UTC

Ordinary matrix: 874/2,064 measurements complete; current family `nginx-analysis`. Bash/updated-backend mismatches: 0; pinned-main invalid measurements: 66. No candidate fix or timing-build change has been needed during this pass. Raw invocation evidence continues to be saved.

### 2026-10-08 02:58 UTC

Ordinary timings: 1065/2,064 complete. Current case: `nginx-analysis/nginx-2.sh`. Bash/updated-backend mismatches: 0; main invalid measurements: 81. The frozen build is unchanged.

### 2026-10-08 03:01 UTC

final-ordinary: 1331/2064 measurements complete. Latest: `nlp-ngrams/ngrams-1.sh`, try cold. Invalid measurements by mode: `{'main': 91}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:04 UTC

final-ordinary: 1659/2064 measurements complete. Latest: `spell/spell-6.sh`, main cold. Invalid measurements by mode: `{'main': 107}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:05 UTC

final-ordinary: 1779/2064 measurements complete. Latest: `unixfun/7.sh`, main cold. Invalid measurements by mode: `{'main': 113}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:06 UTC

final-ordinary: 1928/2064 measurements complete. Latest: `weather/tuft-weather-1.sh`, observe warm. Invalid measurements by mode: `{'main': 129}`. Bash/updated-backend failures: 0.

### Weather font-cache nondeterminism diagnosed

Native Bash cold/warm differed only in `tmp/matplotlib/fontlist-v390.json`; actual benchmark outputs matched. Two bounded independent font-cache generations confirmed identical semantic contents after sorting their font lists. Matplotlib’s discovery order varies between processes. This is fixture nondeterminism, not a candidate output pass.

Archived the affected weather measurements in `weather-font-cache-diagnostic`. The harness now builds one owned font cache during fixture setup and copies the same cache into every mode’s starting state. Plot images remain compared exactly. All six weather cases will be rerun with this fixed setup; the already completed pre-weather measurements remain valid. Added an append mode that refuses overlapping cases so the remaining weather, word-frequency and web-search cases can complete the existing matrix without repeating unrelated work. The Incr/Observe timing binaries remain unchanged.

### 2026-10-08 03:12 UTC

final-ordinary: 1975/2064 measurements complete. Latest: `weather/tuft-weather-3.sh`, observe cold. Invalid measurements by mode: `{'main': 130}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:13 UTC

final-ordinary: 1981/2064 measurements complete. Latest: `weather/tuft-weather-3.sh`, observe cold. Invalid measurements by mode: `{'main': 131}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:14 UTC

final-ordinary: 1987/2064 measurements complete. Latest: `weather/tuft-weather-3.sh`, observe cold. Invalid measurements by mode: `{'main': 131}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:15 UTC

final-ordinary: 2008/2064 measurements complete. Latest: `word-freq/top-n.sh`, bash warm. Invalid measurements by mode: `{'main': 134}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:17 UTC

final-ordinary: 2064/2064 measurements complete. Latest: `web-search/engine.sh`, main warm. Invalid measurements by mode: `{'main': 141}`. Bash/updated-backend failures: 0.

### Ordinary matrix complete

All 2,064 scheduled ordinary measurements are saved. Bash, updated try/strace and Observe each passed all 516 measurements across 86 scripts. Pinned main has 141 invalid measurements; they are excluded from valid timing comparisons.

Observe vs updated try/strace, cold: 6.211x geometric-mean speedup across 86 cases; 5.217x speedup for summed per-case medians.

Observe vs updated try/strace, warm: 1.941x geometric-mean speedup across 86 cases; 2.515x speedup for summed per-case medians.

These are ordinary-only results; DPT is still outstanding. The report correctly remains incomplete until all 10 DPT cases are covered. Starting the serial 80-invocation real-model DPT matrix next.

### 2026-10-08 03:19 UTC

final-dpt: 2/80 measurements complete. Latest: `dpt/dpt_1.sh`, bash warm. Invalid measurements by mode: `{}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:22 UTC

final-dpt: 5/80 measurements complete. Latest: `dpt/dpt_1.sh`, try cold. Invalid measurements by mode: `{'main': 1}`. Bash/updated-backend failures: 0.

### 2026-10-08T03:23:14+00:00 — DPT first baseline diagnostic

Pinned main’s first warm DPT run reproduced stdout and filesystem outputs but left adopted descendants requiring supervisor cleanup (including date/stat zombies). Its 0.424-second timing is therefore invalid and excluded from valid performance comparisons. The bounded supervisor cleaned the descendants; the matrix continues serially. Bash cold/warm and updated try cold passed.

### 2026-10-08 03:24 UTC

final-dpt: 7/80 measurements complete. Latest: `dpt/dpt_1.sh`, observe cold. Invalid measurements by mode: `{'main': 1}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:25 UTC

final-dpt: 8/80 measurements complete. Latest: `dpt/dpt_1.sh`, observe warm. Invalid measurements by mode: `{'main': 1}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:26 UTC

final-dpt: 9/80 measurements complete. Latest: `dpt/dpt_2.sh`, bash cold. Invalid measurements by mode: `{'main': 1}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:28 UTC

final-dpt: 10/80 measurements complete. Latest: `dpt/dpt_2.sh`, bash warm. Invalid measurements by mode: `{'main': 1}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:29 UTC

final-dpt: 12/80 measurements complete. Latest: `dpt/dpt_2.sh`, main warm. Invalid measurements by mode: `{'main': 2}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:30 UTC

final-dpt: 13/80 measurements complete. Latest: `dpt/dpt_2.sh`, try cold. Invalid measurements by mode: `{'main': 2}`. Bash/updated-backend failures: 0.

DPT variant 2: pinned main cold passed; warm matched stdout/filesystem state but required cleanup of two adopted descendants, with none surviving cleanup. Updated try cold passed. These invalid baseline timings remain excluded.

### 2026-10-08 03:31 UTC

final-dpt: 14/80 measurements complete. Latest: `dpt/dpt_2.sh`, try warm. Invalid measurements by mode: `{'main': 2}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:33 UTC

final-dpt: 15/80 measurements complete. Latest: `dpt/dpt_2.sh`, observe cold. Invalid measurements by mode: `{'main': 2}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:34 UTC

final-dpt: 16/80 measurements complete. Latest: `dpt/dpt_2.sh`, observe warm. Invalid measurements by mode: `{'main': 2}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:35 UTC

final-dpt: 18/80 measurements complete. Latest: `dpt/dpt_3a.sh`, bash warm. Invalid measurements by mode: `{'main': 2}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:37 UTC

final-dpt: 20/80 measurements complete. Latest: `dpt/dpt_3a.sh`, main warm. Invalid measurements by mode: `{'main': 3}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:38 UTC

final-dpt: 21/80 measurements complete. Latest: `dpt/dpt_3a.sh`, try cold. Invalid measurements by mode: `{'main': 3}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:39 UTC

final-dpt: 22/80 measurements complete. Latest: `dpt/dpt_3a.sh`, try warm. Invalid measurements by mode: `{'main': 3}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:40 UTC

final-dpt: 23/80 measurements complete. Latest: `dpt/dpt_3a.sh`, observe cold. Invalid measurements by mode: `{'main': 3}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:41 UTC

final-dpt: 24/80 measurements complete. Latest: `dpt/dpt_3a.sh`, observe warm. Invalid measurements by mode: `{'main': 3}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:42 UTC

final-dpt: 25/80 measurements complete. Latest: `dpt/dpt_3b.sh`, bash cold. Invalid measurements by mode: `{'main': 3}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:43 UTC

final-dpt: 26/80 measurements complete. Latest: `dpt/dpt_3b.sh`, bash warm. Invalid measurements by mode: `{'main': 3}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:45 UTC

final-dpt: 28/80 measurements complete. Latest: `dpt/dpt_3b.sh`, main warm. Invalid measurements by mode: `{'main': 4}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:46 UTC

final-dpt: 29/80 measurements complete. Latest: `dpt/dpt_3b.sh`, try cold. Invalid measurements by mode: `{'main': 4}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:48 UTC

final-dpt: 30/80 measurements complete. Latest: `dpt/dpt_3b.sh`, try warm. Invalid measurements by mode: `{'main': 4}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:49 UTC

final-dpt: 31/80 measurements complete. Latest: `dpt/dpt_3b.sh`, observe cold. Invalid measurements by mode: `{'main': 4}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:50 UTC

final-dpt: 32/80 measurements complete. Latest: `dpt/dpt_3b.sh`, observe warm. Invalid measurements by mode: `{'main': 4}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:51 UTC

final-dpt: 33/80 measurements complete. Latest: `dpt/dpt_4.sh`, bash cold. Invalid measurements by mode: `{'main': 4}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:52 UTC

final-dpt: 34/80 measurements complete. Latest: `dpt/dpt_4.sh`, bash warm. Invalid measurements by mode: `{'main': 4}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:53 UTC

final-dpt: 36/80 measurements complete. Latest: `dpt/dpt_4.sh`, main warm. Invalid measurements by mode: `{'main': 5}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:54 UTC

final-dpt: 37/80 measurements complete. Latest: `dpt/dpt_4.sh`, try cold. Invalid measurements by mode: `{'main': 5}`. Bash/updated-backend failures: 0.

Midpoint baseline diagnostic: all five completed main warm DPT variants (1, 2, 3a, 3b, 4) matched stdout and filesystem effects but required descendant cleanup. No descendants survived the bounded supervisor. All completed Bash/updated try/Observe measurements remain valid.

### 2026-10-08 03:55 UTC

final-dpt: 38/80 measurements complete. Latest: `dpt/dpt_4.sh`, try warm. Invalid measurements by mode: `{'main': 5}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:56 UTC

final-dpt: 39/80 measurements complete. Latest: `dpt/dpt_4.sh`, observe cold. Invalid measurements by mode: `{'main': 5}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:57 UTC

final-dpt: 40/80 measurements complete. Latest: `dpt/dpt_4.sh`, observe warm. Invalid measurements by mode: `{'main': 5}`. Bash/updated-backend failures: 0.

### 2026-10-08 03:59 UTC

final-dpt: 41/80 measurements complete. Latest: `dpt/dpt_5a.sh`, bash cold. Invalid measurements by mode: `{'main': 5}`. Bash/updated-backend failures: 0.

### 2026-10-08 04:00 UTC

final-dpt: 42/80 measurements complete. Latest: `dpt/dpt_5a.sh`, bash warm. Invalid measurements by mode: `{'main': 5}`. Bash/updated-backend failures: 0.

### 2026-10-08 04:01 UTC

final-dpt: 44/80 measurements complete. Latest: `dpt/dpt_5a.sh`, main warm. Invalid measurements by mode: `{'main': 6}`. Bash/updated-backend failures: 0.

### 2026-10-08 04:03 UTC

final-dpt: 45/80 measurements complete. Latest: `dpt/dpt_5a.sh`, try cold. Invalid measurements by mode: `{'main': 6}`. Bash/updated-backend failures: 0.

### 2026-10-08 04:04 UTC

final-dpt: 46/80 measurements complete. Latest: `dpt/dpt_5a.sh`, try warm. Invalid measurements by mode: `{'main': 6}`. Bash/updated-backend failures: 0.

### 2026-10-08 04:05 UTC

final-dpt: 47/80 measurements complete. Latest: `dpt/dpt_5a.sh`, observe cold. Invalid measurements by mode: `{'main': 6}`. Bash/updated-backend failures: 0.

### 2026-10-08 04:06 UTC

final-dpt: 48/80 measurements complete. Latest: `dpt/dpt_5a.sh`, observe warm. Invalid measurements by mode: `{'main': 6}`. Bash/updated-backend failures: 0.

### 2026-10-08 04:07 UTC

final-dpt: 49/80 measurements complete. Latest: `dpt/dpt_5b.sh`, bash cold. Invalid measurements by mode: `{'main': 6}`. Bash/updated-backend failures: 0.

### 2026-10-08 04:08 UTC

final-dpt: 50/80 measurements complete. Latest: `dpt/dpt_5b.sh`, bash warm. Invalid measurements by mode: `{'main': 6}`. Bash/updated-backend failures: 0.

### 2026-10-08 04:09 UTC

final-dpt: 52/80 measurements complete. Latest: `dpt/dpt_5b.sh`, main warm. Invalid measurements by mode: `{'main': 7}`. Bash/updated-backend failures: 0.

### 2026-10-08 04:10 UTC

final-dpt: 53/80 measurements complete. Latest: `dpt/dpt_5b.sh`, try cold. Invalid measurements by mode: `{'main': 7}`. Bash/updated-backend failures: 0.

### 2026-10-08 04:11 UTC

final-dpt: 54/80 measurements complete. Latest: `dpt/dpt_5b.sh`, try warm. Invalid measurements by mode: `{'main': 7}`. Bash/updated-backend failures: 0.

### 2026-10-08 04:12 UTC

final-dpt: 55/80 measurements complete. Latest: `dpt/dpt_5b.sh`, observe cold. Invalid measurements by mode: `{'main': 7}`. Bash/updated-backend failures: 0.

### 2026-10-08 04:13 UTC

final-dpt: 56/80 measurements complete. Latest: `dpt/dpt_5b.sh`, observe warm. Invalid measurements by mode: `{'main': 7}`. Bash/updated-backend failures: 0.

## Source publication

User requested brief subject-only commits and pushes, excluding junk files. Fetched both remotes; no concurrent remote changes were present. Pushed Observe `b993d58` to `origin/main` and Incr `7990ee6` to `origin/observe`. Commits contain source, regressions, harnesses and relevant documentation; generated results, models, binaries, caches and Python bytecode were excluded. The real-model final evaluation continues using its frozen runtime snapshot. Source hashes were compared with the measured build and recorded in `published-code.json`. Final curated evidence and this log will be committed after measurement/cleanup.

### 2026-10-08 04:18 UTC

final-dpt: 60/80 measurements complete. Latest: `dpt/dpt_5c.sh`, main warm. Invalid measurements by mode: `{'main': 8}`. Bash/updated-backend failures: 0.

### 2026-10-08 04:19 UTC

final-dpt: 61/80 measurements complete. Latest: `dpt/dpt_5c.sh`, try cold. Invalid measurements by mode: `{'main': 8}`. Bash/updated-backend failures: 0.

### 2026-10-08 04:20 UTC

final-dpt: 62/80 measurements complete. Latest: `dpt/dpt_5c.sh`, try warm. Invalid measurements by mode: `{'main': 8}`. Bash/updated-backend failures: 0.

### 2026-10-08 04:21 UTC

final-dpt: 63/80 measurements complete. Latest: `dpt/dpt_5c.sh`, observe cold. Invalid measurements by mode: `{'main': 8}`. Bash/updated-backend failures: 0.

### 2026-10-08 04:22 UTC

final-dpt: 64/80 measurements complete. Latest: `dpt/dpt_5c.sh`, observe warm. Invalid measurements by mode: `{'main': 8}`. Bash/updated-backend failures: 0.

### 2026-10-08 04:23 UTC

final-dpt: 65/80 measurements complete. Latest: `dpt/dpt_5d.sh`, bash cold. Invalid measurements by mode: `{'main': 8}`. Bash/updated-backend failures: 0.

### 2026-10-08 04:24 UTC

final-dpt: 66/80 measurements complete. Latest: `dpt/dpt_5d.sh`, bash warm. Invalid measurements by mode: `{'main': 8}`. Bash/updated-backend failures: 0.

DPT warm-reuse diagnosis: inspected completed Observe cache metadata for variant 1 without modifying the live run. Three of five entries contain explicit unlink and/or rename replay barriers. Saved `dpt-replay-barriers.json`. This confirms conservative operation-replay restrictions are active in this workload; timing evidence does not show meaningful DPT acceleration. No runtime behavior was changed during final measurements.

### 2026-10-08 04:27 UTC

final-dpt: 69/80 measurements complete. Latest: `dpt/dpt_5d.sh`, try cold. Invalid measurements by mode: `{'main': 9}`. Bash/updated-backend failures: 0.

### 2026-10-08 04:28 UTC

final-dpt: 70/80 measurements complete. Latest: `dpt/dpt_5d.sh`, try warm. Invalid measurements by mode: `{'main': 9}`. Bash/updated-backend failures: 0.

## Expanded optimization goal

The user cleared the original persistent goal and requested robust effectful streaming reuse, investigation of replay after live writes, a full module-by-module code quality audit, stronger optimization coverage, new measurements, and commits/pushes. Created the replacement persistent goal and expanded qualification/PLAN.md. The original frozen-build matrix continues as baseline evidence; finishing it alone will not complete the expanded goal. Fast deterministic experiments precede any further real-model evaluation.

User explicitly authorized assuming only final outputs matter when needed to install cached contents. The optimization investigation will include an explicit final-output policy, alongside a tested live-interaction policy. This changes the permitted replay contract, not the requirement to validate original inputs or stop surviving writers before installation.

### 2026-10-08 04:32 UTC

final-dpt: 74/80 measurements complete. Latest: `dpt/dpt_5e.sh`, bash warm. Invalid measurements by mode: `{'main': 9}`. Bash/updated-backend failures: 0.

### 2026-10-08 04:34 UTC

final-dpt: 76/80 measurements complete. Latest: `dpt/dpt_5e.sh`, main warm. Invalid measurements by mode: `{'main': 10}`. Bash/updated-backend failures: 0.

### 2026-10-08 04:36 UTC

final-dpt: 78/80 measurements complete. Latest: `dpt/dpt_5e.sh`, try warm. Invalid measurements by mode: `{'main': 10}`. Bash/updated-backend failures: 0.

### 2026-10-08 04:38 UTC

final-dpt: 79/80 measurements complete. Latest: `dpt/dpt_5e.sh`, observe cold. Invalid measurements by mode: `{'main': 10}`. Bash/updated-backend failures: 0.

### 2026-10-08 04:39 UTC

final-dpt: 80/80 measurements complete. Latest: `dpt/dpt_5e.sh`, observe warm. Invalid measurements by mode: `{'main': 10}`. Bash/updated-backend failures: 0.

## Frozen baseline qualification complete

All 2,144 scheduled measurements finished across 96 minimum-size entrypoints.
Bash, updated try and Observe each passed 536/536 measurements. Pinned main had
151 invalid measurements: 144 required descendant cleanup and 28 had filesystem
mismatches (overlapping reasons). All ten main warm DPT runs matched final
filesystem outputs but required cleanup; no descendants survived the supervisor.
The driver returned status 1 because these baseline failures remain recorded.

The aggregate report independently checks case coverage and expected sample counts;
additional verification found 2,144 unique case/mode/repetition/phase keys and all
536 valid records for each candidate and Bash. No missing benchmark entrypoints.

Across all 96 cases Observe versus updated try has geometric-mean speedups of
5.140x cold and 1.813x warm; sums of per-case medians improve 1.243x and 1.079x.
Ordinary-only geometric means remain 6.211x cold and 1.941x warm. DPT is essentially
tied: 1.011x cold, 1.009x warm, using one pair per case. Plain Bash remains faster
at these minimum sizes. Main comparisons exclude invalid runs.

Cleaned about 2.3 GB of owned benchmark fixtures/caches plus Bash-suite workspaces,
obsolete frozen snapshots and Python bytecode. Verified no owned mounts or benchmark
processes remained before removal. Kept the pinned main worktree and measured frozen
snapshot for the expanded comparison, plus reusable dependencies/models and saved
evidence. Cleanup details are in results/2026-10-07/cleanup.json.

This completes the original minimum-size baseline, not the expanded optimization
goal. Next: implement and test aggressive final-output replay, preserve a live policy,
complete the module audit, and obtain new measurements on stabilized code.

## Baseline publication and fast effectful-streaming probes

Published curated baseline evidence and the expanded plan in Incr commit 84a95e5
(`Save minimum-size qualification baseline`), pushed to origin/observe. No runtime
source changed after the measured source commits. CSV generation now emits LF
line endings; the final commit passes whitespace checks. Models, binaries, caches,
install/download logs and intermediate attempts are excluded from the commit.

Added effect_replay_probe.py. It runs a real Incr/Observe writer and a producer that
waits until the writer exposes a partial regular-file output before sending the
rest of stdin. This makes early live effects deterministic rather than timing a
sleep and assuming the effect happened. Both overwrite and rename/unlink scenarios
pass cold/warm output checks, but neither retains the cached metadata on warm runs:
overwrite 0.421s/0.484s, rename 0.465s/0.428s. The four probes complete in under two
seconds and clean their temporary directories. Raw evidence is saved in
qualification/results/effect-replay/baseline.json. This is a regression target for
real cache reuse under the authorized final-output policy, not an optimization yet.

Source inspection identified the next implementation boundary: cache candidates
must be validated before speculative writes, then selected by complete stdin hash;
the cancellation path must stop/reap every writer before cached installation and
account for temporary paths created only by the speculative execution. Existing
post-execution validation and kill-only cancellation are insufficient by themselves.

Implemented the first final-output replay prototype: pre-execution candidate validation, separate policy/cache keys, bounded graceful Observe cancellation after effects, and cleanup of speculative newly created paths. Tiny overwrite and rename/unlink streaming probes now retain cached metadata and run warm in ~0.13s versus ~0.43–0.46s cold. Live policy remains unchanged. Initial final-policy regressions exposed a tracer-startup/report race; added handshake-aware cancellation and reran. The user reiterated comprehensive code cleanup, including names, consolidation, dead paths and concise comments; added those explicit review requirements to PLAN.md. Prototype is not yet committed or fully qualified.

The startup handshake fix passes all 35 focused regressions under both policies. Final-policy batch (33 + 2 intentional streaming skips), compressed streaming, compressed batch, full tracing and annotation variants also pass. Strict Clippy passes. Extended the streaming probe to change stdin and then revisit an older candidate, verifying selection by the complete input hash. Remaining work includes transient-path and alias identity coverage, bounded indexing, wrapper policy integration, full module cleanup/audit, and fresh benchmark measurements; no new runtime changes have been pushed yet.

Consolidated batch and stream dependency/effect capture into execution/record.rs; live, final, final-batch and final-compressed regressions pass afterward. Started CODE_REVIEW.md with every source module enumerated and explicit incomplete coverage. Reviewed dormant chunk paths: the stateless table is empty in both baseline and current code, and the dormant implementation ignores child exit status, lacks compression metadata, and has weaker cache validation/concurrency handling. Annotation tests do not constitute chunk-engine coverage. Restoring/qualifying that optimization remains required rather than claiming it already works.


## File identity and directory replay coverage

Observe dependency protocol 4 records original regular-file device/inode identities.
Incr effect manifest 3 distinguishes overwriting an inode from replacing its pathname;
a native-operation comparison test verifies final content of external hard-link aliases
in both cases. Cache namespace is now version 14. All 35 final-policy regressions pass.
Observe's full suite passed 379 assertions before the subsequent directory enhancement.

Directory rename tracking now records source/destination subtree dependencies and
written descendants in dependency mode, without following symlinks. Enumeration
failures block reuse. Added focused Observe assertions for nested dependency/output
coverage; these pass. Expanded the streaming probe with nested directory rename and
symlink outputs; all 12 cold/warm/changed-input/older-input runs pass, with warm cache
metadata retained (~0.17–0.18s versus ~0.46s cold in this probe).

Added INCR_EFFECT_POLICY environment selection for wrapper invocations, keeping the
live default during qualification. Updated current protocol/policy documentation.
Continued naming cleanup in changed code. These are development probes; they are not
new whole-suite performance claims. Source changes remain local until broader review
and testing closes remaining replay cases and optimization gaps.

Environment-selected final policy passes all 35 focused regressions, including wrapper cases. Strict Clippy checks pass in both repositories after the identity/subtree changes. All probes clean their owned temporary directories; no model reruns were needed in this iteration. Remaining review explicitly includes symlink metadata, speculative-path rollback limits, index lifetime, chunk optimization and the full source checklist.

### Chunk optimization and cleanup follow-up

Replaced the dormant chunk-specific cache with the shared validated, locked cache.
Enabled conservative chunk rules for plain cat and simple tr translations. Added an
explicit NUL-free ASCII assumption for rev: native probes showed invalid bytes can
fail and NUL bytes have special behavior, so unrestricted rev is not parallelized.
The assumption is included in cache key version 15. Removed unused annotation
matching machinery, the old chunk cache and its bytes dependency; replaced the
legacy line reader and improved chunk/hash/signal names.

Eight bounded behavioral tests now pass, covering cold/warm reuse, corruption repair,
compressed caches, ordering, empty/unterminated input, text reversal and an infinite
producer with an early-exiting consumer. The latter found a real output-capture bug:
a broken downstream pipe was forgotten after draining. Capture now reports it,
allowing chunk workers to terminate. The failed diagnostic is retained separately.
Three Rust tests pass, including nonzero child status on cold and cached execution.
Broader regression verification and the full source audit remain underway; these
changes are not yet committed or represented as final benchmark results.

### Stable chunking, bounded hints and symlink metadata

Found that the chunk executor rounded content boundaries to OS read boundaries,
which made reuse depend on producer timing. Replaced the approximate chunker and
its duplicate reference implementation with exact incremental content boundaries;
line mode extends through the next newline. Tests now prove identical boundaries
for read sizes 1, 7, 64, 8192 and 65536, with byte-mode size limits and line alignment.
A process-level test changes producer writes to 7777-byte fragments and verifies
identical cache entries, unchanged metadata and exact output. All nine chunk tests
pass in about 13 seconds.

Candidate hints retain at most 64 numeric regular files per command and validate
at most eight. Index failures affect hit rate rather than command success; unrelated
files/directories are left alone. Added a retention regression. Five Rust tests pass.

Found and fixed missing symlink metadata dependencies: changing a symlink timestamp
without changing its target could reuse stale stat output. Observe protocol 5 now
records symlink mtime/ctime/mode; Incr cache key 16 validates them alongside the
target. A focused stat regression passes under both live and final policies; both
36-test regression runs pass, as do Observe's focused dependency checks.

Continued style cleanup: renamed Runtime.typ to kind, executable dev/ino fields to
device/inode, single-letter metadata and error variables, and consolidated duplicate
trace path filtering. Strict Clippy passes in both repositories. Final measurement
runs remain deferred until the wider lifecycle/effect audit is complete.

Observe full suite now passes all 382 assertions across 34 files in 31 seconds.
The bounded supervisor reports no timeout or surviving/leaked descendants.

### Shared replay, child ownership and Observe report/lifecycle review

Consolidated all three executors onto one cached-stream/effect replay function.
Capture now distinguishes a fully drained broken output pipe from an early
short-circuit: completed effects are retained without -s, while cold and warm
executions both return 141 for a broken destination. Added a regression checking
file contents, cold/warm status and a proven batch cache hit. The first fixture
changed the command's working-directory metadata and therefore missed correctly;
placing outputs in their own directory isolates the replay behavior. Failed and
passing evidence is retained. Oversized speculative output now returns an explicit
error instead of asserting, including compressed streams; flush-time broken pipes
are handled consistently.

Added bounded ManagedChild cleanup on error exits. A test starts a 30-second child,
drops its owner and verifies it was killed and reaped immediately. Six Rust tests
pass. Shared replay passes nine chunk tests; the expanded streaming regression
suite passes 38 tests, and compressed batch passes 36 plus its two intentional
finite-stdin skips. Both strict Clippy checks pass.

Observe report generation now borrows dependency/path data, uses a typed write
representation and buffers file output. The 200-file report probe produced the
same read/write sets while reducing tracer write syscalls from 22,057 to 2
(95,354 baseline report bytes versus 108,817 with richer current dependencies).
Strace-observed elapsed times were 1.764s and 0.574s; tracing overhead makes these
diagnostic figures, not a whole-benchmark speedup claim. Raw evidence and the
reproducible probe are saved.

Observe now preserves arbitrary Unix argument bytes using args_os rather than
panicking on non-UTF-8 arguments. Its full suite passed 383 assertions after the
report/argument changes. The subsequent lifecycle review reproduced worker-thread
exec failing with ECHILD after successfully producing output: Linux changes the
executing thread's TID to the process leader's PID, leaving a stale live-thread
entry. The exec event now retires that old TID. All nine focused multiprocess
assertions pass, including the new case; Incr also covers cold/warm execution and
input invalidation for this case. Signal-handler installation errors are now checked.

Remaining next review targets include the legacy strace parser (currently suppresses
all warnings and duplicates an unused Python parser), shared shell AST helpers,
Observe syscall/state/snapshot code, and final-output speculative-path edge cases.
No new model or broad benchmark reruns were started in this development iteration.

### Legacy parser and shell helper cleanup

Removed the unused 423-line Python strace parser after checking repository references.
The Rust parser no longer suppresses compiler/Clippy warnings. Removed duplicated
read/write wrapper types and parent traversal, unused exit-code parsing, opaque
single-letter variables and implementation-history comments. The parser now returns
Trace directly, preserving reasons that prevent reuse instead of silently dropping
unrecognized/incomplete records. Cache key version is 17.

Fixed escaped quotes and nested argument splitting, octal/hex UTF-8 decoding, escaped
file-descriptor paths, syscall delimiters inside filenames, AT_FDCWD resolution,
copy-versus-share semantics for fork/CLONE_FS working directories, failed rename
classification, both hard-link paths and O_RDONLY|O_CREAT writes. Parent components
are preserved because simplifying symlink/.. lexically can select another file.
Strace captures complete pathname strings (4096 bytes) and clone3/vfork events.
Seven parser tests pass; total Rust tests are 13. Two real strace tests verify native
output/status equality, proven warm hits and input invalidation for long negative
paths and names containing UTF-8, quotes, commas and syscall delimiters. The first
real special-path check exposed descriptor annotations using C escapes too; that
was fixed rather than weakening the cache-hit assertion.

Consolidated duplicate libdash initialization and the Shasta compatibility shim in
shell_ast.py. Replaced repeated Dash AST reconstruction with explicit child-field
traversal; retained its transformation scope. Simplified incremental script generation
and improved names/imports in insert.py. Removed unused line-number rewriting and
its residual strip_no_op_lines call: the latter could delete legitimate source lines
containing incr__no_op. Added a wrapper regression for that literal. Dash --identity
now actually avoids inserting Incr. Three bounded shell-AST tests verify generated
pipeline/loop prefixes, transformed execution and identity mode. All 39 focused
regressions and strict Clippy pass. These are development checks, not the final
Bash/benchmark matrix.

### Descriptor tracking, snapshots, and initial write dependencies

Reproduced incorrect descriptor attribution after another thread called dup2:
Observe reported fchmod on the old file while the kernel modified the replacement.
Removed the descriptor-path cache and resolve descriptors through /proc at each
use. This also removes close/dup bookkeeping and their seccomp stops. Literal
filenames ending in ` (deleted)` are distinguished from unlinked descriptors by
inode identity. Path resolution uses O_PATH; parent components remain intact across
symlinks. Tracee string reads now use a stack buffer on the fast path. The full
Observe suite passed 386 assertions after these changes, with no leaked processes.

Consolidated snapshot/manifest entry types and duplicate copy logic. Snapshot
payload names use bounded numeric indices, avoiding NAME_MAX failures. Restoration
removes a replacement symlink before copying original contents, creates missing
parents, and returns failure when an entry cannot be restored. Added long-name,
replacement-symlink, and unreadable-manifest regressions. All 107 snapshot assertions
pass. Directory-tree rename restoration and inode identity remain review items.

Reproduced a separate cache corruption: chmod-only execution could replay an old
file's contents after input bytes changed. Observe now captures dependencies before
metadata, truncate, unlink and rename effects. Incr requires initial dependencies
for writes as well as reads; missing evidence prevents reuse. Descendants of an
initially absent directory inherit that absence. Cache key version is now 18.
Added chmod, truncate and symlink/parent-component invalidation regressions: all 42
focused tests pass in final streaming mode; batch passes with its two intentional
stream-only skips. Rust tests remain 13/13. A streaming rename probe exposed a
trailing-slash dependency introduced by mapping the root path; corrected that mapping
and am rerunning the actual-hit probe. These are focused development results, not
new final benchmark measurements. Source changes remain uncommitted pending review.

Follow-up: all 42 live-policy regressions pass too. The isolated 12-case streaming
probe passes output/filesystem checks and actual-hit assertions for overwrite,
rename/unlink and nested-tree rename, including older candidates. Warm times were
73–114 ms versus 378–450 ms cold in this tiny fixture. Probe runs overlapping other
fixture activity had rename cache misses (correct outputs); isolated runs passed.
Directory-metadata sensitivity remains an investigation item, not a reason to weaken
correctness or the hit assertion. Removed the retained debug fixture. Strict Observe
Clippy passes after the final mapping/comment cleanup.

### Syscall coverage and helper review

Optimized the effect gate: standalone Observe no longer performs gate-only path
checks, and a gate already in live state skips repeated effect classification.
Consolidated metadata-write handling, covering fd/path forms, AT_EMPTY_PATH,
no-follow flags, fchmodat2 and legacy timestamp calls. Missing chmod/truncate targets
now produce negative dependencies; added a failed-chmod-then-create regression.
Extended attribute reads capture path/target metadata dependencies; writes and
asynchronous I/O carry replay barriers because their effects are not represented by
cached file contents. Native execution remains allowed. Added attribute invalidation
and Observe timestamp/attribute tests. An initial full-suite check found the new
attribute handler reporting a FIFO in ordinary non-dependency mode; restored that
mode's existing regular-node filter and reran the full suite successfully.

Renames now share one snapshot-tree implementation, including nested source paths
and destination entries. The nested-directory rename restoration test passes.
Snapshot type-replacement/exchange edges remain under review. Tracee path reads are
bounded by PATH_MAX and reject partial unreadable strings rather than reporting them
as real paths. The initial ptrace-stop wait now retries EINTR and handles requested
termination. Removed syscall section dividers, improved local names and corrected
stale README claims about close/dup stops, termination and universal restoration.

Reviewed Incr's annotation, cache data types, execution dispatch, skip execution,
entry point, byte/data helpers, logging and Observe report decoder. Removed heap
allocation around hashers, capped bincode decode allocation accounting at 64 MiB,
and made debug logging tolerate unavailable paths/writes. Independent CLI default
resolution fixes a relative --cache argument being placed under the home directory
when --try was omitted; its regression passes. Updated CODE_REVIEW.md coverage and
EFFECT_REPLAY.md to distinguish implemented behavior from remaining work.

Validation: strict Clippy passes in both repositories; Incr Rust tests 13/13; Observe
full suite 396/396 assertions across 34 files; Incr final-policy focused regressions
45/45. All runtime runs were bounded with no leaked descendants. These source changes
are still under qualification, with no new final benchmark claims or publication yet.

The post-review 12-case effect-replay probe also passes all correctness and actual-hit
assertions after the gate/syscall changes (syscall-review-probe.json); no descendants
remained. Larger measurements remain deferred until the remaining lifecycle audit.

### Bounded streaming stdin and runtime ownership

Replaced the stream executor's unbounded heap queue with a shared stdin spool.
The queue holds at most 1 MiB, then spills to a private, immediately unlinked file
inside the cache filesystem. The child reads concurrently while hashing continues;
this preserves early cache lookup for slow readers instead of imposing child-speed
backpressure on hashing. EOF and receiver closure have explicit ownership. Added
order/cleanup and closed-receiver Rust tests, plus a roughly 6 MiB slow-reader
regression that verifies both output hash and retained warm-cache metadata. Spill
space is released when the descriptors close; large slow-reader inputs can use disk
space proportional to the buffered input.

Streaming runtimes now have cleanup on error paths. Output capture files are opened
before launching the child, eliminating a race where a delayed capture thread could
create an artifact after cleanup. A missing-tracer regression verifies no owned
runtime files remain. Consolidated duplicate Observe launch arguments, preserved
signal exit codes in every executor, and fixed the receiver-closure race so partial
stdin is not treated as complete. Cache version is 19 to invalidate entries created
before the newly covered syscall dependencies. Updated README and review tracker.

Validation: strict Clippy passes; Rust tests 15/15; final-policy regression suite
47/47; nine chunk tests pass after the capture-file ownership change. Bounded runs
report no leaked descendants. No expensive model reruns were started. Remaining
work includes speculative preexisting-path effects, remaining module reviews, the
full policy/optimization matrix, final benchmarks, curated commits and pushes.
The isolated post-spool effect probe passes all 12 correctness and actual-hit cases
(spool-effect-probe.json), with no remaining descendants.

### Shell, dependency, snapshot and lifecycle audit

Consolidated repetitive Bash AST reconstruction into explicit child-field traversal,
added until-loop traversal, removed fixture-specific ignore names and reset the
modified flag between declaration discovery and transformation. The first check
caught libbash's unhashable enum values; traversal now keys on their integer values.
Four shell AST tests pass, including nested conditionals/loops/cases/functions. All
eight selected Bash differential cases (dollars, func, getopts, ifs, invert, quote,
read, comsub-posix) match native Bash. Removed the wrapper's unused argument array
and installed cleanup before temporary setup.

Reviewed all of try.sh. Fixed commit failures lost inside a pipeline subshell,
standalone commit/summary ignoring the sandbox's saved exclusion list, temporary
ignore files leaked by help/error exits, and mount/path quoting. Removed decorative
separators and obsolete case comments. Five bounded try tests pass: exclusions,
failed commit status, spaced paths, help cleanup and a real Incr streaming sandbox
execution/commit with no leftover runtime sandbox. Shared result capture now extracts
that sandbox directly rather than first renaming a possible mount across filesystems.

Unified legacy try dependency keys with Observe's nanosecond/ctime/mode/size states,
removed three obsolete serialized key variants, and made unreadable captures
uncacheable instead of silently dropping them. Three real strace cases pass, including
content changes with restored mtime. Cache key version is 20. Incr Rust tests 15/15,
strict Clippy and all 47 final-policy regressions pass.

Observe's seccomp filter tags unsupported i386/x32 syscall ABIs; these commands run
live with a replay barrier instead of an incomplete reusable report. A real ELF32
assembly program produces native output and the expected barrier. Condensed the
filter implementation and verbose commentary. Snapshot restoration now removes
new entries deepest-first, restores directories before contents, then metadata;
file/tree rename-exchange regression passes. Fixed failed O_CREAT against a directory
being snapshotted as nonexistent, and failed rmdir creating a directory during revert.
The full Observe suite passes 403 assertions across 34 files. Subsequent lifecycle
cleanup gives TracerState bounded ownership of surviving tracees on error paths;
focused errors/signals/multiprocess tests pass with no leaked descendants. Both
repositories pass strict Clippy.

Updated review coverage: remaining source concerns are command pending-output
buffering/failure paths and speculative writes to unexpected preexisting paths in
final-output streaming. No final benchmark reruns or new publication yet. Earlier
benchmark evidence remains immutable; new evidence is under results/effect-replay.

Completed the pending-output review: chunk stdin and ordered stdout/stderr now share
the bounded-memory spool rather than allocating unbounded queues for unusually long
lines or delayed earlier chunks. Capture streams are written as data arrives; only
forwarding waits for output order. Removed the obsolete channel-only forwarder and
renamed its result type to ForwardResult to cover input and output use. All nine
chunk tests and 47 final-policy regressions pass after the change; strict Clippy and
15 Rust tests pass. Recorded the concrete selective-snapshot design for unexpected
preexisting speculative writes in EFFECT_REPLAY.md; that is the remaining source
review item before the full qualification matrix and final measurements.

### Selective restoration and final fast matrix

Implemented the remaining final-output cancellation case. When validated candidates
exist, Observe snapshots paths outside the intersection of their write sets. Exact
exclusions avoid copying known outputs and do not exclude unexpected descendants.
Snapshot content capture now also saves original metadata. Incr stops/reaps writers,
checks partial-report replay barriers, restores snapshots with a bounded Observe
revert subprocess, cleans remaining new paths and installs selected cached output.
Snapshot restoration failures retain a .recovery directory with an explicit error.
The live policy is unchanged.

The new timing-dependent probe delivers all stdin on the cold run, but delays warm
stdin until the command temporarily modifies a preexisting file. It verifies original
contents, mode and mtime after cancellation, exact final stdout/output, cache metadata
retention on two warm runs and absence of runtime artifacts. Both warm runs reused
the cache at roughly 75–91 ms versus roughly 0.4s cold. The ordinary 12-case early-write
probe still passes. Updated a snapshot dedup assertion to require exactly one content
entry and one metadata entry; added an exact-exclusion restoration test.

Final fast matrix: all 24 groups pass, covering 16 live/final optimization configurations,
nine chunk tests, four shell-AST tests, three real strace tests, five try tests,
benchmark component checks, 405 Observe assertions and both replay probes. The full
83-case Bash differential run is now active. Strict Clippy and 15 Rust tests pass.
Source review coverage is complete; final measurements/publication remain required.
The benchmark driver now records the Observe effect policy explicitly. Final timing
comparisons will use --effect-policy final, retaining the earlier live-policy baseline.

Source commits are pushed: Observe main 1817725972558eb8e67495bb4eeffe5e10314810;
Incr observe 119e668fdcb0 (full revision in final-build.json). Both messages contain
only brief subjects. No execution caches, bytecode or result-directory artifacts
were included in these source commits.

The complete Bash differential suite passes all 83 cases (166 native/candidate
records). Job-control and trap tests contain intentional waits and completed within
their individual deadlines. Build/source/dependency/input fingerprints were recorded
for frozen snapshot b21d57dc13686230ee36. The final ordinary benchmark matrix has
started serially with three pairs per case and explicit Observe final-output policy.
Real-model DPT follows only after ordinary validation. Results are being saved in
qualification/results/2026-10-08; final report and evidence commit remain pending.

### Final measurement monitoring

The ordinary matrix has passed 480 completed records with no Bash, updated try or
Observe validation failures. Pinned main reproduces warm bio mismatches; its invalid
runs will be excluded from speed comparisons. Runtime sources and measured binaries
remain fixed. Updated the progress reader to accept an explicit results directory
instead of silently reading the previous evaluation date, and corrected the source
review tracker to the final 405 Observe assertions. These are harness/documentation
changes only.

The ordinary matrix passed its halfway point (1,120/2,064 records) with zero
Bash/updated-try/Observe failures. File-modification cases show working final-output
replay: completed warm Observe samples are about 0.2–0.3s versus 2–5s for updated
try in these cases. These are preliminary case-level timings, not an aggregate.
Added OPTIMIZATIONS.md to map assumptions, implementation and behavioral coverage.
The later real-model matrix is expected to take roughly 80 minutes based on the
previous frozen baseline; it will run once, serially, after ordinary validation.

### Ordinary final matrix complete

All 2,064 scheduled measurements across 86 entrypoints completed. Bash, updated
try and Observe each pass all 516 measurements. Pinned main has 374 valid and 142
invalid measurements; the driver exits 1 because those baseline failures remain
visible. Every candidate raw record passes status, timeout and descendant checks;
record identities are unique and complete. Observe uses the final-output policy.
The real-model DPT matrix now starts serially, one cold/warm pair per mode and
variant. No source changes or competing tests/builds will run during it.

DPT variant 1 completed all eight measurements. Bash, updated try and Observe
pass cold/warm validation; pinned main warm is invalid. Observe takes 66.28s cold
and 66.43s warm versus updated try 69.50s/66.42s: no meaningful warm-model speedup.
The final report will separate model and ordinary results rather than imply that
the ordinary speedups apply to model inference. Remaining variants continue
serially under the existing deadlines.

DPT midpoint: 40/80 measurements, five complete variants. Bash, updated try and
Observe each pass 10/10; pinned main has five valid cold and five invalid warm
runs. No candidate timeouts or cleanup failures. Model timings remain close
between Observe and updated try. The report now separates all/ordinary/DPT
aggregates and uses descriptive loop variables; measured runtime sources and
binaries are unchanged.

### Final qualification complete

All 2,144 measurements across 96 benchmark entrypoints are present and unique.
Bash, updated try and Observe each pass 536/536. Pinned main has 384 valid and
152 invalid runs: 146 require descendant cleanup and 29 have filesystem mismatches,
with overlap. Both benchmark drivers exit 1 solely because baseline failures remain
visible; the candidate qualification report is true. Independently rechecked all
1,608 reference/candidate raw records against native output/effects/status and
cleanup evidence. Published source and binary hashes exactly match the frozen build.

Observe versus updated try: all-case geometric means 5.787x cold / 2.148x warm;
sum-of-medians speedups 1.278x / 1.112x. Ordinary-only geometric means are
7.073x / 2.343x, with 15.705x warm file-modification and 8.739x warm word-frequency
speedups. DPT is 1.031x / 1.019x on single samples, without meaningful model-cache
acceleration. Two cold and six warm case medians are slower than updated try; worst
warm ratio 0.951x. Plain Bash remains faster overall at minimum size, and the
27 fully valid main warm ordinary cases favor main by about 7% geometrically.
The final evaluation documents these regressions and remaining assumptions.

Cleanup removed 2.3 GB of disposable benchmark fixtures/caches, Bash execution
fixtures, obsolete build 8bcf3a4ad33c026f3990, Python bytecode, old progress state and
the redundant Node download archive. No owned benchmark processes, mounts or
recovery snapshots remained. Kept the frozen baseline/final builds, pinned main
checkout, reusable dependencies/models and saved evidence for reproduction.
Completed the expanded plan and final evaluation documentation. Curated evidence
and documentation are being published together with a brief subject-only commit.
