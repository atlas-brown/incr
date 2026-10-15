# Incr Observe: Bash correctness study

This study compares **every standard Bash 5.2.37 test group** against native Bash, using the binary’s default **final** effect policy, first cold and then with the same cache retained. The test environment leaves `INCR_EFFECT_POLICY` unset. It uses verified, unmodified GNU test sources rather than the repository's edited `evaluation/bash-ts/tests` copy. It also runs Incr's focused correctness regressions under live and final effect policies.

Read [REPORT.md](REPORT.md) for findings, [CASE_ANALYSIS.md](CASE_ANALYSIS.md) for the per-group analysis, and [DESIGN_COMPARISON.md](DESIGN_COMPARISON.md) for Observe versus main. [PROGRESS.md](PROGRESS.md) preserves the investigation and corrections. Results are differential equivalence, not a count of independently numbered assertions.

## Run everything

From the Incr repository root:

```bash
./studies/bash-parity-audit-2026-10-08/run.sh
```

The default output is `results/latest/` under this directory. An existing nonempty output directory is rejected to protect evidence. For a repeat, choose a new destination:

```bash
./studies/bash-parity-audit-2026-10-08/run.sh --output /tmp/incr-bash-results-2
```

The script checks its own comparison/terminal helpers, builds current Incr and the sibling Observe repository with `cargo build --release --locked`, freezes their runtime files, verifies the Bash corpus, creates private locales and fixtures, runs 83 groups × 2 implementations × 2 phases, and then runs both regression policies. Each Observe warm run immediately follows its cold run without clearing its fixture or cache. Native cold/warm runs use the same arrangement. Groups have independent caches. Run the harness serially.

Expect roughly 10–15 minutes on this machine, largely because four `jobs` executions deliberately wait about a minute each. Ordinary commands have 45-second limits, `exportfunc` 60 seconds, `jobs` 120 seconds, and the full workflow an 1800-second budget checked between groups. Child cleanup is bounded by the repository supervisor. Temporary fixtures and locales are automatically removed after evidence capture. Host `/tmp` and host locales are never cleaned or modified.

Exit codes: **0** means all scheduled normalized comparisons and requested regressions passed; **1** means a substantive comparison failed; **2** means setup, coverage, or lifecycle failure. The runner prints each result and writes `progress.md` as it goes. A driver status of 1 alone is not a differential failure: upstream drivers use literal `diff`, which sees trivial source locations and native platform differences.

## Prerequisites

Linux with working `ptrace`/seccomp support; the Incr repository and sibling `../observe`; Rust/Cargo; `cc`, `make`, Python 3, GNU diff/coreutils, `localedef` and locale source data, `unshare`, `mount`, `setpriv`, and noninteractive `sudo` permitted for private mount namespaces. The `sudo` setup is used only to create private mounts; tests run as your normal UID/GID. No external service credentials are needed.

The existing qualification environment can be reused. To prepare missing Bash/parser dependencies:

```bash
python3 -B studies/bash-parity-audit-2026-10-08/harness/setup.py
```

This downloads GNU Bash 5.2.37 only if the build is absent, checks its pinned SHA256, builds Bash plus the four test helpers, and creates a parser venv only if absent (`libbash==0.1.14`, `libdash==0.5.2`, `shasta==0.5`). It does not install OS packages. Existing prerequisite directories are preserved. The runner verifies all 668 official test-tree files and stops on any modification. The initial download needs network access; subsequent runs use local prerequisites.

Override prerequisite paths with `--bash-build /path/to/bash-build --python /path/to/venv/bin/python`. Keep the venv interpreter path rather than resolving its symlink to system Python.

## Focused investigation

```bash
./studies/bash-parity-audit-2026-10-08/run.sh \
  --cases alias,execscript,read --skip-regressions \
  --output /tmp/incr-bash-focused
python3 -B -m unittest discover \
  -s studies/bash-parity-audit-2026-10-08/harness -p 'test_*.py' -v
```

`--cases` accepts exact names from `run-*`, without the prefix. `--timeout` overrides the ordinary per-case limit. Full results in `results/upstream/` are the clean final-policy execution. Earlier live-policy and exploratory results were removed; git commit `4a772a4` retains that history. Every cold run starts with an empty cache and private fixture; only its immediately following warm run retains that new cache.

## Evidence and interpretation

Each `records/CASE.MODE.PHASE.json.gz` contains command, raw stdout/stderr, actual and expected diff operands, exit status, timing, cleanup diagnostics, shell-launcher invocation coverage, and before/after cache file inventories. For example:

```bash
python3 - <<'PY'
import gzip, json
from pathlib import Path
path = Path('studies/bash-parity-audit-2026-10-08/results/upstream/records/execscript.observe.warm.json.gz')
record = json.loads(gzip.decompress(path.read_bytes()))
print(record['returncode'], record['cache_entries'], record['retained_metadata'])
print(record['captures'][0]['actual'])
PY
```

`case-results.json`/CSV and `summary.json` contain aggregate results; `diffs/` retains nonempty raw/normalized differences. `provenance.json` identifies source revisions and binary hashes; `setup/` holds compressed build and regression logs. The diff capture helper excludes capability checks comparing an expected file to itself, so those lines do not inflate the denominator.

Normalization is deliberately narrow: source-location paths, diagnostic line numbers, terminal process-group IDs, and PIDs in Bash signal-termination diagnostics. Signal labels and command text remain compared. Printed function bodies remain fully compared; compiler instrumentation is an observable difference and is never stripped. All raw text remains available. New unexpected differences fail; missing captures, changed expected operands, timeouts, and Observe-only leftover descendants cannot pass. Live process names/counts are checked separately so an adopted zombie in the native run cannot mask a live candidate leak. A controlling terminal is available to every test, with terminal stdin additionally provided for `read`.

Cache entries and unchanged metadata establish that warm runs retain cache state; they do not by themselves prove every command hit. Focused regression tests verify actual reuse separately. Shell syntax/source-sensitive constructs can execute natively by design. Launcher logs show shell entry points, not every individual Bash statement; direct shebang execution and builtins retain native shell semantics.

Regenerate the detailed ledger and independently recheck retained evidence without rerunning Bash:

```bash
python3 -B studies/bash-parity-audit-2026-10-08/harness/analyze.py \
  studies/bash-parity-audit-2026-10-08/results/upstream \
  --report studies/bash-parity-audit-2026-10-08/CASE_ANALYSIS.md
```

The analysis also writes `line-results.csv.gz`: one row for every compared transcript line, identified by group, phase, capture, and line number, with equality status and normalized hashes. Full unmodified text remains in the raw records. These are transcript-line IDs, not invented source-level test IDs.

The analysis command rejects missing records and recomputes all comparisons from raw captures. It writes `analysis.json` beside the results and exits nonzero if any group differs.

The runner accepts `--shell /bin/bash --native-transform --assume-directory-access`
to qualify the configuration used by the current benchmark study. A preparation
probe requires the native compiler to accept the selected target; this avoids
mislabeling a custom-Bash Python fallback as native-frontend qualification. The
verified custom Bash still drives the official test scripts, while reference and
Observe both execute the selected target shell. Omit `--shell` to test the custom
Bash build. Both runtime settings
and the disabled static-annotation policy are recorded in provenance. Omit these
options to qualify defaults; use distinct result directories for each run.

For the installed Bash 5.1 target, use its matching official corpus. Preparation
and execution both accept `--corpus-provenance`; setup derives the release
source directory from that pinned metadata. The runner rejects major/minor
version mismatches before building the candidate and archives the complete corpus
metadata with each new result. The installed-shell gate uses all 82 Bash 5.1.16
groups, while the custom-Bash default gate retains all 83 Bash 5.2.37 groups.

```bash
python3 -B studies/bash-parity-audit-2026-10-08/harness/setup.py \
  --bash-build qualification/.work/bash-5.1.16 \
  --corpus-provenance studies/bash-parity-audit-2026-10-08/corpus-provenance-5.1.16.json
studies/bash-parity-audit-2026-10-08/run.sh --shell /bin/bash \
  --bash-build qualification/.work/bash-5.1.16 \
  --corpus-provenance studies/bash-parity-audit-2026-10-08/corpus-provenance-5.1.16.json \
  --native-transform --assume-directory-access --output results-for-bash51
```

The failed `parser-fallback-system-bash-full-01` exploration used Bash 5.2 tests
on installed Bash 5.1. It completed 68 groups before native `read` timed out.
Independent partial analysis matches 66 groups in both phases; the remaining
`jobs` and `quotearray` groups also differ between the two native runs themselves.
Their variable values and diagnostic ordering are not normalized. That retained
cross-version run is diagnostic evidence, not a passing correctness gate.

`QUALIFICATION_HISTORY.json` records the scope and content-tree hashes of
superseded local trials. Their raw artifacts remain local diagnostics. The two
final version-matched suites retain complete raw evidence in the checkpoint.
