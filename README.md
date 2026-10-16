# incr

Bolt-on incremental execution for the shell. Caches command outputs and reuses them when inputs haven't changed.

## Quick Start

```bash
# Build incr and the optional Observe tracing backend
cargo build --release
cd ../observe && cargo build --release && cd ../incr

# Run a script with incremental execution
./incr.sh my_script.sh [/path/to/cache]
```

When **observe** is built as a sibling project (`../observe/target/release/observe`), incr.sh automatically uses it to trace commands on the live filesystem. Without Observe, the default backend uses try + strace. Static tool annotations are off by default in both cases.

---

## Usage

### Script mode (recommended)

Transform and run a bash script so each command is executed incrementally:

```bash
./incr.sh <script> [cache_dir]
```

- **script**: Path to your bash script
- **cache_dir**: Optional; defaults to `/tmp/incr_cache` (or set `INCR_CACHE_DIR`)
- **observe**: Auto-enabled when `../observe/target/release/observe` exists

incr.sh uses `insert.py` to wrap each command with incr, then runs the transformed script. Re-run the script; unchanged commands replay from cache.

### Direct command mode

Run a single command through incr:

```bash
./target/release/incr --try ./src/scripts/try.sh --cache /tmp/my_cache [--observe ../observe/target/release/observe] -- <command> [args...]
```

Arguments are passed literally, including a lone executable name with spaces. To
run shell source, pass `bash -c '...'` explicitly.

Example:

```bash
# Read-only command (traced by Observe)
echo "" | ./target/release/incr -t ./src/scripts/try.sh -c /tmp/cache --observe ../observe/target/release/observe -- cat input.txt

# Write (uses Observe when --observe is passed)
echo "" | ./target/release/incr -t ./src/scripts/try.sh -c /tmp/cache --observe ../observe/target/release/observe -- bash -c "echo hello > output.txt"
```

---

## Using observe

**observe** is a ptrace/seccomp tracer that records file reads, writes and their dependencies. Incr uses it instead of strace + the try filesystem sandbox when `--observe` is selected.

### Why use observe?

Observe traces commands on the live filesystem, avoiding the fallback's per-command
mergerfs sandbox setup. The explicit live effect policy supports shared-file and
FIFO interactions that require intermediate effects.
Actual speedups depend on the workload and whether its effects can safely replay;
see the [consolidated evaluation results](studies/evaluation-checkpoint-2026-10-16/README.md).

### Enabling observe

1. **Build observe** (sibling to incr):
   ```bash
   cd ../observe && cargo build --release
   ```

2. **Script mode**: incr.sh auto-detects `../observe/target/release/observe` and passes it to insert.py. No extra flags.

3. **Direct mode**: Pass `--observe ../observe/target/release/observe` (or the full path) to the incr binary.

### Backend selection

With annotations disabled, commands use Observe to trace filesystem accesses and
coordinate effects. Valid cache candidates can replay after dependency and
complete-stdin validation. Read-only witness files are no longer needed; the
legacy `-o` / `--skip_introspection` option is accepted as a no-op.

Static tool annotations are opt-in with `-a`. They can select read-only tracing
or omit tracing for guarded stream-only system-tool forms. They are disabled in
the initial benchmark comparison for both original Incr and Incr+Observe.

### Fallback: try + strace

Without Observe, the default backend runs commands through try and strace.
The command executes in a mergerfs/unionfs overlay; strace records file access,
and try commit applies changes to the real filesystem. With `-a`, guarded
read-only forms can use strace without an overlay and guarded pure forms can
omit tracing. This backend requires `try.sh` and its filesystem dependencies.

This fallback works without the observe project. It adds sandbox setup and commit overhead. Use it when Observe is unavailable; its overlay is not a security boundary.

---

## Cache correctness and execution limits

The cache directory is trusted private state, as in original Incr. Cached stdout,
stderr and filesystem payloads are not checksummed on capture or replay. Missing
or nonregular payloads invalidate an entry, but externally modified bytes are
outside this contract. Application inputs and replay preconditions are still
validated independently. Cache format 34 and effect manifest 5 separate this
representation from earlier checksum-bearing entries.

Incr reuses deterministic command output when its arguments, environment, working
directory, executable identity, umask, stdin and recorded filesystem dependencies match. Observe reports
first-access state, including failed opens, symlinks, directories and write targets.
File state includes ctime as well as mtime, size and mode. Observe-backed execution
assumes `/tmp`, `/var/tmp`, and an absolute, non-root `$TMPDIR` contain disposable
scratch state rather than persistent inputs or application outputs. Those paths
are excluded from dependency/effect replay by default, alongside virtual
`/proc`, `/dev`, and `/sys` state. Use `--track-temporaries` or
`INCR_TRACK_TEMPORARIES=true` when temporary paths are meaningful inputs/outputs.
The policy is part of the cache key; commands and byte streams still execute normally.

`--assume-directory-access` (or `INCR_ASSUME_DIRECTORY_ACCESS=true`) additionally
assumes directory stat/access results are used for existence and access checks,
not directory timestamps or inode identities. Observe still tracks directory
opens/listings, permissions, ownership and symlink resolution. This option is off
by default, recorded in protocol 10/11 reports, and separated in the cache key.
`--content-validated-inputs` (or `INCR_CONTENT_VALIDATED_INPUTS=true`) additionally
allows read-only regular workspace files opened for content to retain cached
results after inode/ctime changes. Modification time, size, content, permissions,
ownership, link count and effective access still have to match. Unchanged
identity/ctime is the fast path; drift requires rehashing. Paths queried only through stat/access or O_PATH, files outside the workspace,
and written files retain strict checks. A successful read-only regular-file open
identifies a content input, including programs that also fstat that descriptor. This opt-in
assumes the content input's inode/ctime are not application data, and is useful
when archive extraction recreates identical inputs. It requires Observe protocol
11 (12 with guarded inherited files) and has a separate cache key; strict defaults are unchanged.

Static performance annotations are disabled by default. Enable them with
`-a` / `--enable_annotations`; this also enables supported chunk optimizations.
When enabled, tool annotations apply only to resolved system tools, so custom PATH programs
with the same names are traced. With Observe, inherited read-only regular files
have their descriptor numbers, identities, offsets, flags and fdinfo included in
the cache key. Protocol 12 guards their use before speculative execution can
consume shared state; commands that access them execute live and are not cached.
Unused descriptors can therefore remain open in shell loops without disabling
every command's cache. Writable descriptors, pipes, sockets, unsupported descriptor
sets and non-UTF-8 arguments/environment execute directly. The try backend also
retains its inherited-descriptor bypass. Terminal-connected invocations execute directly to preserve
terminal reads and ioctl behavior. Observe reports and snapshots preserve arbitrary
Unix path bytes; dependency paths that the current binary cache cannot encode
prevent reuse. Executable and working-directory identities use their exact bytes.

Streaming execution starts the command while consuming stdin. The default
`--effect-policy final` validates cache candidates before execution, selects one by
the complete stdin hash, stops all writers, and installs cached final outputs.
This policy targets final-output equivalence; it does not preserve intermediate
file observations or concurrent external writes. Use `--effect-policy live`, or
`INCR_EFFECT_POLICY=live` with the wrapper, for shared-file handshakes and programs
that require intermediate effects. Live permits cache cancellation only before the
first live effect. FIFO dependencies prevent cache reuse under either policy.

The full upstream Bash correctness evaluation and its exact scope are maintained
in [the Bash correctness runner](studies/bash-parity-audit-2026-10-08/README.md). Shell-level
fallbacks preserve Bash parsing, alias expansion, command lookup and source-sensitive
behavior; passing those cases does not imply that every command is accelerated.

Both policies validate saved payloads before replay. File replay distinguishes
in-place writes from pathname replacement so existing hard-link aliases receive the
correct final contents. Replayed regular files retain their saved modification
times so replay alone does not invalidate downstream content dependencies. Setting
a historical timestamp can require ownership; when access permits writing but not
timestamp restoration, downstream validation conservatively misses. Final policy
also supports rename/unlink outputs; ownership, timestamp and special-file operations
still require live execution. Cache key version 33, effect manifest version 4 and
Observe dependency protocols 9/10/11/12 reject incompatible
entries. External network state, clocks and randomness are not general memoization inputs.

With `-a`, plain `cat` and simple alphanumeric `tr` translations can reuse independent
chunks. `--assume-text` (or `INCR_ASSUME_TEXT=true`) additionally enables line-wise
`rev` in the C/POSIX locale, assuming NUL-free ASCII input. Do not enable that
assumption for arbitrary binary input. Chunk caches preserve output order, compression and command status.

Streaming stdin uses an in-memory queue, as in original Incr, so hashing can
finish ahead of a slow child and cancel its execution on a cache hit. This
assumes enough RAM for the queued input; large backlogs can consume substantial
memory. Ordered speculative output retains a 64 MiB memory queue with an unlinked
temporary file for overflow.

Batch mode requires finite stdin and checks the cache before execution. Cache writers
use nonblocking entry locks; contending commands execute with private temporary entries.

The wrapper creates an owned transformed copy and never rewrites the input script.
Use `INCR_CACHE_DIR=/path/to/cache ./incr.sh -b script.sh args...` for the Bash parser
and unambiguous script arguments. Source/history introspection and interpreter modes
that cannot preserve semantics through transformation execute natively. Those paths
are correct passthroughs, not accelerated cases. Parser source locations can refer
to the private transformed copy. Set `INCR_OBSERVE=0` to force try/strace, or `1` to
require Observe; `INCR_OBSERVE_PATH` selects its executable.

The optional `INCR_NATIVE_TRANSFORM=1` frontend inserts wrappers into a conservative
Bash syntax subset while preserving source bytes. Unsupported constructs use the
Python transformer. It is off by default. Commands execute through the general
tracing/cache backends; no sort or cut implementation is substituted.

See [the benchmark harness](studies/paper-size-benchmarks/README.md) for methodology and explicit reproduction commands, and [the consolidated study](studies/evaluation-checkpoint-2026-10-16/README.md) for all saved measurements. All active and pending evaluations were cancelled; no background work is scheduled.

## Development Setup

1. **Rust**: Install Rust (e.g. `rustup`).
2. **OverlayFS**: `sudo apt install mergerfs` (for try.sh sandbox when observe is not used).
3. **Python**: For `insert.py` (script transformation):
   ```bash
   pip3 install -r requirements.txt
   ```
4. **Build**:
   ```bash
   cargo build --release
   ```

Toggle `DEBUG` and `DEBUG_LOGS` in `src/config.rs` for cache debug info and logs.

### Docker

```bash
docker build -t incr .
docker run -it --rm -v $(pwd):/app --privileged incr
```

---

## Testing and benchmarks

```bash
bash agents/test_incr_observe.sh
python3 qualification/regressions.py
```

[Qualification](qualification/README.md) documents maintained component tests; [studies](studies/README.md) lists the full Bash runner, single benchmark harness and consolidated detailed statistics. Workload programs and minimum seeds remain in `evaluation/benchmarks/`. Old duplicate launchers, result trees and caches were removed. Runtime and dependency setup is explicit; no benchmark runs automatically.

When final-output streaming selects a prevalidated candidate, unexpected speculative
paths are restored from selective pre-write snapshots before cached outputs are
installed. Paths written by every candidate are excluded from backups. All writers
must stop first. Failed restoration returns an error and retains a `.recovery`
snapshot for inspection; it never silently discards the backup. Temporary paths
with non-UTF-8 names can also be restored during speculation even though those
paths cannot be persisted in the binary cache. The policy still
assumes deterministic final outputs and no concurrent external mutations.
