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
