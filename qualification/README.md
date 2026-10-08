# Minimum-size qualification

Start with [PLAN.md](PLAN.md), [AUDIT.md](AUDIT.md), and the dated
`results/2026-10-07/MEASUREMENTS.md`. Raw failed attempts are retained as diagnostic
evidence; only `final-ordinary` and `final-dpt` feed the final measurements.

## Fast checks

From the Incr repository, with the sibling Observe repository built:

```bash
cargo build --release
(cd ../observe && cargo build --release)
python3 qualification/regressions.py
python3 qualification/regressions.py --batch --compress
python3 qualification/regressions.py --full
python3 qualification/benchmark_tests.py
```

The focused suite uses 5-second command deadlines and owned temporary directories.
Batch mode omits only the two tests requiring an unbounded/held-open input stream.
The annotation, compression and full-tracing configurations have separate results.

Use the supervisor for arbitrary validation commands:

```bash
python3 qualification/bounded.py --timeout 120 --result /path/to/result.json -- command args
```

It records status, byte hashes, elapsed completion time, deadline failures and
process-tree cleanup. Run it serially in a dedicated Python process: it becomes a
child subreaper and rejects preexisting children. Privileged sandbox helpers require
noninteractive `sudo -n`. No unbounded wait on inherited stdout pipes is used.

## Benchmark environment

The measurement host is Linux x86-64 with Bash, strace, mergerfs/FUSE, Rust, Python
3.10, noninteractive sudo and the tools listed in the saved setup records. Bio uses
minimap2/samtools; file modification uses ffmpeg/ImageMagick/OpenSSL; weather uses
gnuplot; spelling uses `/usr/share/dict/words`. Python parser dependencies are
libdash 0.5.2, libbash 0.1.14 and shasta 0.5. The dedicated `qualification/.venv`
contains the parser dependencies plus CPU PyTorch, TensorFlow, segment-anything,
OpenCV and plotting libraries. Exact installed versions are saved in
`results/2026-10-07/python-dependencies.txt`.

Web search uses Node 22.20.0 under `.work/node-v22.20.0-linux-x64` and dependencies
installed from its existing package.json with `npm install --ignore-scripts`.
The Node archive was verified against official SHA256 sums. DPT uses the actual
SAM vit_h checkpoint, classifier and label dictionary; it never substitutes a model
stub. Input-fetch commands and their results are saved with the setup evidence.
Do not run benchmark `install.sh` or `fetch.sh` blindly: inspect their paths and use
a bounded wrapper around downloads. They may fetch substantially more than the
minimum image actually selected by the runner.

The driver expects minimum inputs in each benchmark's existing `inputs` directory.
It prepares one fixed Matplotlib font cache per plotting family outside timings,
so process-dependent font-list order cannot create false filesystem mismatches.
Plot images are still compared exactly. It copies fixtures into `.work`, gives every invocation a private TMPDIR, restores
warm fixtures in place, and keeps separate caches by mode/script/repetition.
Weather plotting is reduced to one city-year, and web search to one real article.
DPT selects the provided one-image minimum. Image annotation is excluded by the
user; no API credential is needed for the remaining matrix.

## Reproduction

Build the candidate and the pinned main revision recorded in `final-build.json`.
The driver expects main in the sibling detached worktree `incr-main-qualification`.
`build_snapshot.py` freezes binaries and helpers before each matrix so rebuilding
source during diagnostic work cannot alter an in-flight invocation.

```bash
python3 qualification/benchmarks.py \
  --only beginner,bio,covid,file-mod,nginx-analysis,nlp-ngrams,nlp-uppercase,poet,spell,unixfun,weather,word-freq,web-search \
  --repetitions 3 --results qualification/results/DATE/final-ordinary
python3 qualification/benchmarks.py --only dpt --repetitions 1 \
  --results qualification/results/DATE/final-dpt
python3 qualification/report.py qualification/results/DATE
```

Copy the benchmark inventory into a new result directory before generating its
report. Keep the two matrices serial, with no concurrent tests or builds. A result
exit code of 1 is intentional if any baseline or candidate case fails; inspect raw
records, do not silently ignore it. Main failures are preserved but excluded from
valid speed comparisons. Every candidate and Bash reference must pass, and every
scheduled case/sample must exist, before the aggregate report says complete.

For the Bash suite, the pinned built Bash and helpers live in `.work/bash-src`;
setup/build commands and its revision are in the dated setup records. The harness
uses a private mount namespace and private `/tmp` to isolate upstream test cleanup.

```bash
python3 qualification/bash_suite.py --all --modes bash,observe \
  --results qualification/results/DATE/bash
```

## Cleanup

Retain source changes and `results/`. Remove only owned benchmark caches, run
fixtures, temporary transformed scripts, test directories and frozen build copies
when no driver is active. Check for owned live processes and mounts before deleting
sandbox trees; never recursively remove a live mount. Root-owned sandbox leftovers
may need noninteractive sudo. Do not clean global `/tmp` or unrelated user files.
Reusable model/input downloads and installed dependencies are distinct from run
artifacts; retain them for subsequent full-size qualification unless explicitly
removing the dedicated environment.
