# Case-by-case Bash analysis

Effect policy: **final** (binary default; INCR_EFFECT_POLICY unset).

Generated from retained raw records. Counts are LF-delimited output lines, not separately numbered assertions. Each group has native cold/warm and Observe cold/warm evidence. Warm retains the same fixture/cache. Source locations, terminal process-group IDs, and the reviewed function executable prefixes are the only normalizations used here.

| Group | Native lines cold/warm | Cold match | Warm match | Cache entries cold/warm | Unchanged warm metadata |
|---|---:|:---:|:---:|---:|---:|
| alias | 45/45 | True | True | 1/1 | 1 |
| execscript | 172/172 | True | True | 5/6 | 5 |
| redir | 163/163 | True | True | 1/1 | 1 |
| read | 85/85 | True | True | 2/3 | 2 |
| procsub | 33/33 | True | True | 2/4 | 2 |
| set-e | 72/72 | True | True | 1/2 | 1 |

## alias

Alias definitions, chained/recursive expansion, unalias, and alias-driven grammar. Restores the original suite without excluding recursive cases.

- Native reference: 45 cold / 45 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 1/1; unchanged warm metadata files: 1. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 10/10; warm 10/10.
- Corpus files seen at shell-launcher entry points: `alias.tests`, `alias1.sub`, `alias2.sub`, `alias3.sub`, `alias4.sub`, `alias5.sub`, `alias6.sub`.
- Expected transcript(s): `alias.right`.
- Evidence: `records/alias.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/alias.*`.

## execscript

Invocation modes, missing commands, binary/directory execution, startup files, argv0, and restored empty/unset PATH tests.

- Native reference: 172 cold / 172 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 1/1; warm 1/1. Native matches literal expected operands: False.
- Cache entries cold/warm: 5/6; unchanged warm metadata files: 5. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 40/40; warm 40/40.
- Corpus files seen at shell-launcher entry points: `exec10.sub`, `exec11.sub`, `exec12.sub`, `exec13.sub`, `exec14.sub`, `exec2.sub`, `exec3.sub`, `exec4.sub`, `exec5.sub`, `exec6.sub`, `exec7.sub`, `exec9.sub`, `execscript`.
- Expected transcript(s): `exec.right`.
- Evidence: `records/execscript.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/execscript.*`.

Native versus expected-file differences (shared baseline context, not an Observe regression):

```diff
24d23
< trap -- 'echo USR1' SIGUSR1
25a25
> trap -- 'echo USR1' SIGUSR1
30d29
< trap -- 'echo USR1' SIGUSR1
31a31
> trap -- 'echo USR1' SIGUSR1
```

## redir

Descriptor redirection, file creation, invalid descriptors/paths, and error behavior.

- Native reference: 163 cold / 163 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: False / False.
- Driver status, native/Observe: cold 0/1; warm 0/1. Native matches literal expected operands: True.
- Cache entries cold/warm: 1/1; unchanged warm metadata files: 1. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 14/14; warm 14/14.
- Corpus files seen at shell-launcher entry points: `redir.tests`, `redir10.sub`, `redir11.sub`, `redir3.sub`, `redir4.sub`, `redir5.sub`, `redir6.sub`, `redir7.sub`, `redir8.sub`, `redir9.sub`.
- Expected transcript(s): `redir.right`.
- Evidence: `records/redir.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/redir.*`.

## read

Read options, timeouts, readline, pipes, and terminal input. A controlling terminal and terminal stdin are supplied to exercise original timeout paths.

- Native reference: 85 cold / 85 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: False / False.
- Driver status, native/Observe: cold 0/1; warm 0/1. Native matches literal expected operands: True.
- Cache entries cold/warm: 2/3; unchanged warm metadata files: 2. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 9/9; warm 9/9.
- Corpus files seen at shell-launcher entry points: `read.tests`, `read1.sub`, `read2.sub`, `read3.sub`, `read4.sub`, `read5.sub`, `read6.sub`, `read7.sub`, `read8.sub`.
- Expected transcript(s): `read.right`.
- Evidence: `records/read.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/read.*`.

## procsub

Process substitution, descriptors, process IDs/waits, and status interactions.

- Native reference: 33 cold / 33 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 2/4; unchanged warm metadata files: 2. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 4/4; warm 4/4.
- Corpus files seen at shell-launcher entry points: `procsub.tests`, `procsub1.sub`, `procsub2.sub`.
- Expected transcript(s): `procsub.right`.
- Evidence: `records/procsub.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/procsub.*`.

## set-e

Errexit behavior across control-flow and execution contexts.

- Native reference: 72 cold / 72 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 1/2; unchanged warm metadata files: 1. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 25/25; warm 25/25.
- Corpus files seen at shell-launcher entry points: `set-e.tests`, `set-e1.sub`, `set-e2.sub`, `set-e3.sub`.
- Expected transcript(s): `set-e.right`.
- Evidence: `records/set-e.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/set-e.*`.
