# Qualification findings (in progress)

Baseline: Incr observe 4f8723e, Incr main 4b8e5dd, Observe a95ca6b.

Ten focused regressions take about one second per executor. Both streaming and batch
fail append re-execution, read-modify-write, empty-directory replay, dangling-symlink
replay, file arguments incorrectly annotated pure, and /tmp input invalidation.
Observe's existing suite reports 371/371 assertions passing; the supervisor also
finds orphaned zombie descendants in signal tests. Full qualification is NOT complete.

Audit priorities:
- Live speculative writes can escape before cache decisions; no snapshot/control
  protocol is used by Incr. Rollback must not clobber concurrent consumers/writers.
- Post-execution hashing records the wrong dependency for read-modify-write.
- Cold Observe runs unnecessarily replay their own writes via try commit.
- Pure annotations currently ignore file arguments and writing flags.
- Main includes broken-pipe and cross-filesystem cleanup improvements missing here.
- Benchmark harness ignores command errors and validates stdout only; broad /tmp
  cleanup can delete unrelated files. Do not use it unmodified for qualification.

Progress update (qualification still in progress):
- Original Observe suite: 371/371 assertions, no remaining descendants. New
  dependency/gate tests add seven assertions and pass in focused runs.
- Focused Incr suite now covers append, read-modify-write, missing inputs,
  symlinks, hard links, rename, FIFO communication, cache corruption,
  concurrent cache users, inherited descriptors, early exit with open stdin,
  real warm hits, streams/status, and compression/full-tracing/annotation flags.
- Observe cold writes execute once. A shared atomic gate prevents cancellation
  after externally visible effects start. Replay barriers keep inode-sensitive
  operations and unsupported metadata effects live. Cache payloads are checked
  before replay, and cache writers use nonblocking locks with private entries
  on contention. These correctness restrictions must be included in the report;
  they are not evidence of universal operation-level replay support.
- First-access dependencies include negative opens, directories and symlinks;
  /tmp files are retained. Read/write keys preserve both metadata and pre-write
  hashes. Protocol v2 and cache key v7 prevent incompatible reuse.
- Unsafe read-only annotations/introspection no longer send writing awk/sed/find
  invocations through the try backend's read-only fast path. Full tracing now
  actually bypasses annotations. Both original branches have an empty stateless
  command list; chunk eligibility is unchanged, not newly qualified as enabled.
- Bash adapter tests exposed parser/wrapper bugs: option quoting, empty -c,
  combined/long options, altered HOME/PATH, non-UTF-8 argument corruption,
  incomplete here-documents, source/history/locale-sensitive pretty-printing.
  Source-sensitive forms execute unchanged. A native qualification launcher
  uses INCR_ARGV0 to preserve argv[0] across the script interpreter.
- All 11 previously failing/special Bash cases in bash-fixes-round2 match Bash.
  Some upstream cases intentionally leave background children; the supervisor
  records and cleans these. Candidate cleanup is accepted only when the Bash
  reference also requires cleanup, and remaining descendants always fail.
- Weather tuft variants and web-search now have real, documented minimum fixtures:
  one city-year (365 daily rows), one actual HTML article plus the existing stop
  sentinel. Their cold/warm Bash/Observe comparisons pass. DPT remains one real
  image using the supplied SAM/classifier models. Original larger --min weather
  and web attempts were interrupted to preserve iteration speed, not counted as
  passes. Image annotation is excluded at the user's explicit direction.
- Benchmark validation now checks failures and file manifests as well as output;
  bio-1's absent hard-coded sample and file-mod-7's missing gzip prerequisites
  were corrected. Random encryption salt is validated by decrypting payloads;
  DPT log timestamps/PIDs are normalized while preserving the actual messages.
- Long runs now freeze executables and shell helpers in content-addressed build
  snapshots. Diagnostic timings while other work runs are NOT final performance
  measurements. Final serial comparisons, report, and cleanup are outstanding.

Final pre-measurement update:
- Replaced in-place wrapper rewriting with private real-script execution. An eval
  prototype failed Bash arithmetic/error semantics and was discarded. Source files
  remain unchanged, including read-only files, spaces in paths and parallel calls.
- Native-copy Bash suite: all 83 cases match after narrowly normalizing temporary
  source locations (raw evidence and independent revalidation retained). Dedicated
  reruns of exportfunc/posix2 confirm the diagnostic normalization.
- Current cache key version is 11; Observe dependency protocol remains 3 and effect
  manifest version 2. Earlier version numbers above describe intermediate builds.
- Final focused suite has 33 cases; stream/full/annotation modes pass all 33, and
  batch/compressed-batch pass 31 with the two explicitly streaming-only cases omitted.
- Observe's complete test suite passed 378 assertions; eight existing Incr scripts
  returned success. The focused Python assertions are the stronger failure oracle.
- Non-UTF-8 internal paths prevent cache reuse. Uncapturable effects do not change
  the already-completed live command's exit status. stdout/stderr cache streams now
  carry integrity hashes; corrupt/truncated payloads become misses.
- DPT plot variants had a genuine input-format mismatch (raw classifier columns
  supplied to formatted-record readers). Move tee after formatting, and persist the
  final plot to PNG rather than opening an interactive window.
- The final measurement matrix uses three ordinary cold/warm pairs per mode and one
  DPT pair per variant/mode. The latter uses the real model with eight OpenMP threads
  on the 16-CPU machine; single samples have limited performance precision.

Executable-identity follow-up (before final timings):
- A custom PATH program named rev/tr could inherit a system tool's pure annotation.
  Added resolved executable identity (path, inode, ctime/mtime, size, mode) to command
  keys and restricted static annotations to the resolved system-tool locations.
- The batch key now incorporates that command hash instead of duplicating a subset
  of its fields. Cache version is 12. Tests cover a shadowed tool reading changing
  files and a system-tool symlink replaced by a custom executable.
- Interrupted v11 timings are retained in `timing-before-executable-identity`; they
  are not inputs to the final report. Focused suite now contains 35 cases.

Final v12 Bash qualification:
- 82 cases matched on the full pass. In printf, native Bash alone emitted two
  one-second clock-mismatch diagnostics from printf3.sub; no other output differed.
  A single fresh paired rerun matched. The initial failure and recheck are both kept.
  The combined summary contains 166 matched records for 83 cases, with this exception
  explicitly recorded rather than deleting the original evidence.
- All 35 focused tests pass in streaming/full/annotation modes; batch and compressed
  batch pass 33 and omit only the two stream-only input-lifetime cases.
- Inactive owned benchmark caches were removed with a mount check before restarting
  final timings. No active owned mergerfs process or mount remained at that point.
