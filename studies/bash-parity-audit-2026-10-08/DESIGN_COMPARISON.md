# Incr main versus Incr Observe

Reviewed local main 4b8e5dd, Incr observe bd11f3a (runtime changes at 8f3c769), and Observe b5ad47a. The detached baseline worktree matches local main. No remote fetch was needed to compare these local branches.

## Execution path

Both transform shell ASTs to prefix selected external commands with Incr. Both start commands while hashing stdin, capture and forward stdout/stderr, and on a cache hit replay the unforwarded output suffix. Batch waits for finite stdin before lookup.

| Area | Main | Current Observe branch |
|---|---|---|
| Write tracing | try mergerfs sandbox plus strace text; commit upperdir effects | ptrace/seccomp on the live filesystem; typed JSON report; retain try fallback |
| Shell wrapper | src/incr.sh rewrites the caller script with sentinel backup | incr.sh uses a private transformed script, preserves argv and source-sensitive native execution |
| Command identity | name, arguments, filtered environment; a single argument is shell-split | literal argv, cwd bytes, executable identity, environment/PWD; cache key also includes umask/backend/policy |
| Dependencies | post-run regular-file mtime (microseconds), hashes for read/write files; limited absent-path records | first-access state, failed lookups, ctime/mtime/size/mode, symlink targets, directories and parent access; pre-write hashes |
| Annotations | broad name-based pure/read-only tables, including file-reading grep/sort and potentially writing awk/sed | restricted argument forms and resolved system tools; unknown effects traced |
| Streaming memory | unbounded channel | 1 MiB memory queue plus anonymous disk spill |
| Live interactions | sandbox visibility and unconditional streaming cache cancellation | shared effect gate; live policy cannot cancel after first effect; FIFO dependencies block reuse |
| Final-output policy | absent | optional prevalidated candidates; full stdin selects entry; stop writers, restore unexpected effects, install cached outputs |
| Cached effects | try upperdir copy/commit | versioned file/dir/link/deletion manifest, validated payloads, overwrite versus inode replacement distinction |
| Integrity/concurrency | older cache without current checks/leases | stdout/stderr and effect checksums; nonblocking locks and private contention entries |
| Process lifecycle | older kill/join behavior | subreaper, managed children, bounded shutdown, stdin polling for early consumers |
| Chunk executor | stateless rule table empty, effectively dormant | restricted cat/tr and explicitly assumed ASCII rev; ordered workers share cache/replay |
| Unsupported inputs | older string/descriptor/terminal handling | terminals, inherited descriptors and byte argv/env pass through; byte filesystem paths traced/restored but not persisted |

Current protocol boundaries: cache key 22, effect manifest 3, Observe dependencies 7. The Bash suite uses the default live streaming policy through the Bash parser (`incr.sh -b`); this wrapper flag is distinct from the Rust binary's batch flag.

## What the historical logs explain

The original Observe integration replaced sandbox startup but initially reused the old post-run dependency and commit assumptions. Later tiny reproductions exposed stale append/read-modify-write caching, duplicated cold effects, incomplete directory/link replay, bad pure annotations, races and orphaned descendants. The qualification log documents successive fixes rather than one unchanged implementation.

Live correctness came first: initial-state dependencies, a cancellation gate, conservative replay barriers and ownership of descendants. Final-output optimization was added explicitly afterward because late validation sees already-mutated inputs. Up to eight recent candidates are validated before launch, one is chosen by complete stdin hash, and snapshots cover paths outside the intersection of candidate outputs. Restoration failure preserves a recovery snapshot and returns an error.

The shell wrapper moved away from both in-place rewriting and an unsuccessful eval prototype. Real private scripts retain Bash error/control-flow semantics; source/history introspection, sensitive modes, builtins, functions/aliases and live-interaction commands can use native execution. Thus shell parity is not proof of acceleration for every test.

The latest audit further fixed Unix-byte paths, parent symlink/permission dependencies, read-only and group-writable replay, low-fd restoration and parser prefixes. It reran only 23 curated Bash groups; the earlier complete 83-group run predates those changes. This audit independently reruns all 83 on current sources.

## Documentation discrepancies

The early agents/docs integration review says no bugs were found and describes replaying cold Observe writes through try. Later reproducible failures and current code supersede that assessment. The old architecture pages list grep/sort as pure and chunking as dormant; both have changed.

Observe DESIGN.md and CONTEXT.md still describe a descriptor cache, lexical pathname normalization, percent-encoded snapshot names, reverse-order best-effort restoration, and older SIGTERM handling. Current source removes the descriptor cache, preserves path components and bytes, uses numeric payload names, preflights restoration with ordered phases, and kills/reaps tracees before writing reports. These documents explain design history but cannot be treated as current specifications.

Earlier benchmark notes also describe in-place script sentinels, filtering ordinary /tmp dependencies, unsafe global temporary cleanup and weak output checks. The newer qualification harness and runtime supersede those practices. This audit uses owned fixtures/private /tmp and retains raw comparison evidence.

## Limits

Filesystem memoization assumes deterministic behavior and stable external state. Network, clocks, randomness, concurrent external mutation and general filesystem transactions are not covered. Final policy deliberately does not preserve intermediate observations. Many unsupported effects run live; source-sensitive shell scripts can pass by native execution. Native Bash is the semantic reference, not main's potentially incorrect behavior.
