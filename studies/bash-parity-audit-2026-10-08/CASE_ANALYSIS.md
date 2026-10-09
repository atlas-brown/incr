# Case-by-case Bash analysis

Effect policy: **final** (binary default; INCR_EFFECT_POLICY unset).

Generated from retained raw records. Counts are LF-delimited output lines, not separately numbered assertions. Each group has native cold/warm and Observe cold/warm evidence. Warm retains the same fixture/cache. Source locations, terminal process-group IDs, and the reviewed function executable prefixes are the only normalizations used here.

| Group | Native lines cold/warm | Cold match | Warm match | Cache entries cold/warm | Unchanged warm metadata |
|---|---:|:---:|:---:|---:|---:|
| alias | 45/45 | True | True | 1/1 | 0 |
| appendop | 28/28 | True | True | 0/0 | 0 |
| arith | 263/263 | True | True | 0/0 | 0 |
| arith-for | 86/86 | True | True | 2/2 | 2 |
| array | 787/787 | True | True | 47/47 | 47 |
| array2 | 74/74 | True | True | 19/19 | 19 |
| assoc | 400/400 | True | True | 18/20 | 18 |
| attr | 37/37 | True | True | 0/0 | 0 |
| braces | 77/77 | True | True | 0/0 | 0 |
| builtins | 281/281 | True | True | 5/8 | 4 |
| case | 63/63 | True | True | 0/0 | 0 |
| casemod | 47/47 | True | True | 0/0 | 0 |
| complete | 63/63 | True | True | 0/0 | 0 |
| comsub | 79/79 | True | True | 9/9 | 9 |
| comsub-eof | 17/17 | True | True | 0/0 | 0 |
| comsub-posix | 100/100 | True | True | 4/4 | 4 |
| cond | 142/142 | True | True | 0/0 | 0 |
| coproc | 10/10 | True | True | 4/5 | 4 |
| cprint | 72/72 | True | True | 0/0 | 0 |
| dbg-support | 371/371 | True | True | 0/0 | 0 |
| dbg-support2 | 7/7 | True | True | 0/0 | 0 |
| dirstack | 79/79 | True | True | 0/0 | 0 |
| dollars | 744/744 | True | True | 33/33 | 33 |
| dynvar | 7/7 | True | True | 0/0 | 0 |
| errors | 208/208 | True | True | 0/0 | 0 |
| execscript | 172/172 | True | True | 5/6 | 3 |
| exp-tests | 419/419 | True | True | 23/23 | 23 |
| exportfunc | 14/14 | True | True | 5/5 | 4 |
| extglob | 184/184 | True | True | 2/4 | 2 |
| extglob2 | 70/70 | True | True | 0/0 | 0 |
| extglob3 | 27/27 | True | True | 0/0 | 0 |
| func | 169/169 | True | True | 2/4 | 2 |
| getopts | 68/68 | True | True | 0/0 | 0 |
| glob-test | 261/261 | True | True | 33/65 | 32 |
| globstar | 587/587 | True | True | 9/16 | 7 |
| heredoc | 133/133 | True | True | 6/10 | 6 |
| herestr | 38/38 | True | True | 0/0 | 0 |
| histexpand | 246/246 | True | True | 0/0 | 0 |
| history | 299/299 | True | True | 0/0 | 0 |
| ifs | 12/12 | True | True | 3/6 | 3 |
| ifs-posix | 1/1 | True | True | 0/0 | 0 |
| input-test | 3/3 | True | True | 0/0 | 0 |
| intl | 57/57 | True | True | 2/2 | 2 |
| invert | 10/10 | True | True | 1/1 | 1 |
| iquote | 92/92 | True | True | 0/0 | 0 |
| jobs | 120/120 | True | True | 2/3 | 2 |
| lastpipe | 22/22 | True | True | 1/1 | 0 |
| mapfile | 170/170 | True | True | 0/0 | 0 |
| more-exp | 214/214 | True | True | 59/59 | 59 |
| nameref | 560/560 | True | True | 6/6 | 6 |
| new-exp | 795/795 | True | True | 6/7 | 6 |
| nquote | 80/80 | True | True | 3/3 | 3 |
| nquote1 | 131/131 | True | True | 0/0 | 0 |
| nquote2 | 76/76 | True | True | 0/0 | 0 |
| nquote3 | 60/60 | True | True | 0/0 | 0 |
| nquote4 | 18/18 | True | True | 0/0 | 0 |
| nquote5 | 86/86 | True | True | 0/0 | 0 |
| parser | 16/16 | True | True | 0/0 | 0 |
| posix2 | 4/4 | True | True | 2/2 | 0 |
| posixexp | 308/308 | True | True | 13/14 | 13 |
| posixexp2 | 40/40 | True | True | 0/0 | 0 |
| posixpat | 42/42 | True | True | 0/0 | 0 |
| posixpipe | 41/41 | True | True | 0/0 | 0 |
| precedence | 28/28 | True | True | 0/0 | 0 |
| printf | 298/298 | True | True | 0/0 | 0 |
| procsub | 33/33 | True | True | 2/4 | 2 |
| quote | 182/182 | True | True | 14/14 | 14 |
| quotearray | 152/152 | True | True | 0/0 | 0 |
| read | 85/85 | True | True | 2/3 | 2 |
| redir | 163/163 | True | True | 1/1 | 0 |
| rhs-exp | 105/105 | True | True | 35/35 | 35 |
| rsh | 19/19 | True | True | 0/0 | 0 |
| set-e | 72/72 | True | True | 1/2 | 1 |
| set-x | 60/60 | True | True | 0/0 | 0 |
| shopt | 312/312 | True | True | 1/2 | 1 |
| strip | 12/12 | True | True | 0/0 | 0 |
| test | 297/297 | True | True | 13/13 | 1 |
| tilde | 28/28 | True | True | 0/0 | 0 |
| tilde2 | 28/28 | True | True | 1/1 | 1 |
| trap | 115/115 | True | True | 0/0 | 0 |
| type | 135/135 | True | True | 2/2 | 0 |
| varenv | 277/277 | True | True | 4/7 | 4 |
| vredir | 101/101 | True | True | 4/7 | 3 |

## alias

Alias definitions, chained/recursive expansion, unalias, and alias-driven grammar. Restores the original suite without excluding recursive cases.

- Native reference: 45 cold / 45 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 1/1; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 10/10; warm 10/10.
- Corpus files seen at shell-launcher entry points: `alias.tests`, `alias1.sub`, `alias2.sub`, `alias3.sub`, `alias4.sub`, `alias5.sub`, `alias6.sub`.
- Expected transcript(s): `alias.right`.
- Evidence: `records/alias.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/alias.*`.

## appendop

Scalar and array append-assignment behavior and expansion of appended values.

- Native reference: 28 cold / 28 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 3/3; warm 3/3.
- Corpus files seen at shell-launcher entry points: `appendop.tests`, `appendop1.sub`, `appendop2.sub`.
- Expected transcript(s): `appendop.right`.
- Evidence: `records/appendop.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/appendop.*`.

## arith

Arithmetic evaluation, operator precedence, bases, overflow/error diagnostics, and short-circuit side effects.

- Native reference: 263 cold / 263 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 9/9; warm 9/9.
- Corpus files seen at shell-launcher entry points: `arith.tests`, `arith1.sub`, `arith2.sub`, `arith3.sub`, `arith4.sub`, `arith5.sub`, `arith6.sub`, `arith7.sub`, `arith8.sub`.
- Expected transcript(s): `arith.right`.
- Evidence: `records/arith.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/arith.*`.

## arith-for

Arithmetic for-loop initialization, condition, update, and control flow.

- Native reference: 86 cold / 86 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 2/2; unchanged warm metadata files: 2. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 3/3; warm 3/3.
- Corpus files seen at shell-launcher entry points: `arith-for.tests`.
- Expected transcript(s): `arith-for.right`.
- Evidence: `records/arith-for.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/arith-for.*`.

## array

Indexed arrays, assignment, subscripting, and expansion. Restores malformed compound assignments removed from the vendored copy.

- Native reference: 787 cold / 787 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 47/47; unchanged warm metadata files: 47. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 31/31; warm 31/31.
- Corpus files seen at shell-launcher entry points: `array.tests`, `array1.sub`, `array10.sub`, `array11.sub`, `array12.sub`, `array13.sub`, `array14.sub`, `array15.sub`, `array16.sub`, `array17.sub`, `array18.sub`, `array19.sub`, `array2.sub`, `array20.sub`, `array21.sub`, `array22.sub`, `array23.sub`, `array24.sub`, `array25.sub`, `array26.sub`, `array27.sub`, `array28.sub`, `array29.sub`, `array3.sub`, `array30.sub`, `array4.sub`, `array5.sub`, `array6.sub`, `array7.sub`, `array8.sub`, `array9.sub`.
- Expected transcript(s): `array.right`.
- Evidence: `records/array.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/array.*`.

## array2

Array @/* expansion, quoting, and positional-argument interactions via array-at-star.

- Native reference: 74 cold / 74 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 19/19; unchanged warm metadata files: 19. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 1/1; warm 1/1.
- Corpus files seen at shell-launcher entry points: `array-at-star`.
- Expected transcript(s): `array2.right`.
- Evidence: `records/array2.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/array2.*`.

## assoc

Associative-array keys, updates, unset behavior, and expansion diagnostics.

- Native reference: 400 cold / 400 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: False / False.
- Driver status, native/Observe: cold 0/1; warm 0/1. Native matches literal expected operands: True.
- Cache entries cold/warm: 18/20; unchanged warm metadata files: 18. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 19/19; warm 19/19.
- Corpus files seen at shell-launcher entry points: `assoc.tests`, `assoc1.sub`, `assoc10.sub`, `assoc11.sub`, `assoc12.sub`, `assoc13.sub`, `assoc14.sub`, `assoc15.sub`, `assoc16.sub`, `assoc17.sub`, `assoc18.sub`, `assoc2.sub`, `assoc3.sub`, `assoc4.sub`, `assoc5.sub`, `assoc6.sub`, `assoc7.sub`, `assoc8.sub`, `assoc9.sub`.
- Expected transcript(s): `assoc.right`.
- Evidence: `records/assoc.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/assoc.*`.

## attr

Variable attributes and declaration semantics; the upstream driver filters explanatory expect lines.

- Native reference: 37 cold / 37 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 3/3; warm 3/3.
- Corpus files seen at shell-launcher entry points: `attr.tests`, `attr1.sub`, `attr2.sub`.
- Expected transcript(s): `attr.right`.
- Evidence: `records/attr.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/attr.*`.

## braces

Brace expansion, ranges, nesting, and quoting boundaries.

- Native reference: 77 cold / 77 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 1/1; warm 1/1.
- Corpus files seen at shell-launcher entry points: `braces.tests`.
- Expected transcript(s): `braces.right`.
- Evidence: `records/braces.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/braces.*`.

## builtins

Builtin semantics and error/status behavior. Check native differences independently; host limits can differ from expected files.

- Native reference: 281 cold / 281 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 1/1; warm 1/1. Native matches literal expected operands: False.
- Cache entries cold/warm: 5/8; unchanged warm metadata files: 4. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 22/22; warm 22/22.
- Corpus files seen at shell-launcher entry points: `builtins.tests`, `builtins1.sub`, `builtins2.sub`, `builtins3.sub`, `builtins4.sub`, `builtins5.sub`, `builtins6.sub`, `builtins7.sub`, `source5.sub`, `source6.sub`, `source7.sub`.
- Expected transcript(s): `builtins.right`.
- Evidence: `records/builtins.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/builtins.*`.

Native versus expected-file differences (shared baseline context, not an Observe regression):

```diff
1c1
< 0
---
> 1000
```

## case

Case patterns and terminators, including the restored esac-as-pattern grammar case.

- Native reference: 63 cold / 63 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 5/5; warm 5/5.
- Corpus files seen at shell-launcher entry points: `case.tests`, `case1.sub`, `case2.sub`, `case3.sub`, `case4.sub`.
- Expected transcript(s): `case.right`.
- Evidence: `records/case.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/case.*`.

## casemod

Case modification in parameter expansion and variable attributes.

- Native reference: 47 cold / 47 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 1/1; warm 1/1.
- Corpus files seen at shell-launcher entry points: `casemod.tests`.
- Expected transcript(s): `casemod.right`.
- Evidence: `records/casemod.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/casemod.*`.

## complete

Programmable completion definitions and generated candidates in noninteractive tests.

- Native reference: 63 cold / 63 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 1/1; warm 1/1.
- Corpus files seen at shell-launcher entry points: `complete.tests`.
- Expected transcript(s): `complete.right`.
- Evidence: `records/complete.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/complete.*`.

## comsub

Command substitutions, alias-created grammar, and subshell expansion. Restores comsub5/comsub6 cases removed from the vendored copy.

- Native reference: 79 cold / 79 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: False / False.
- Driver status, native/Observe: cold 0/1; warm 0/1. Native matches literal expected operands: True.
- Cache entries cold/warm: 9/9; unchanged warm metadata files: 9. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 7/7; warm 7/7.
- Corpus files seen at shell-launcher entry points: `comsub.tests`, `comsub1.sub`, `comsub2.sub`, `comsub3.sub`, `comsub4.sub`, `comsub5.sub`, `comsub6.sub`.
- Expected transcript(s): `comsub.right`.
- Evidence: `records/comsub.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/comsub.*`.

## comsub-eof

End-of-input handling inside command substitution, including restored malformed heredoc input.

- Native reference: 17 cold / 17 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 8/8; warm 8/8.
- Corpus files seen at shell-launcher entry points: `comsub-eof.tests`, `comsub-eof0.sub`, `comsub-eof1.sub`, `comsub-eof2.sub`, `comsub-eof3.sub`, `comsub-eof4.sub`, `comsub-eof5.sub`, `comsub-eof6.sub`.
- Expected transcript(s): `comsub-eof.right`.
- Evidence: `records/comsub-eof.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/comsub-eof.*`.

## comsub-posix

POSIX command substitution parsing and errors, including the restored incomplete conditional.

- Native reference: 100 cold / 100 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 4/4; unchanged warm metadata files: 4. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 15/15; warm 15/15.
- Corpus files seen at shell-launcher entry points: `comsub-posix.tests`, `comsub-posix1.sub`, `comsub-posix2.sub`, `comsub-posix3.sub`, `comsub-posix5.sub`, `comsub-posix6.sub`.
- Expected transcript(s): `comsub-posix.right`.
- Evidence: `records/comsub-posix.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/comsub-posix.*`.

## cond

Conditional commands, pattern matching, expression operators, and diagnostics.

- Native reference: 142 cold / 142 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 4/4; warm 4/4.
- Corpus files seen at shell-launcher entry points: `cond-regexp1.sub`, `cond-regexp2.sub`, `cond-regexp3.sub`, `cond.tests`.
- Expected transcript(s): `cond.right`.
- Evidence: `records/cond.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/cond.*`.

## coproc

Coprocess descriptors, process lifetime, and synchronization. Compare baseline background cleanup explicitly.

- Native reference: 10 cold / 10 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 4/5; unchanged warm metadata files: 4. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 1/1; warm 1/1.
- Corpus files seen at shell-launcher entry points: `coproc.tests`.
- Expected transcript(s): `coproc.right`.
- Evidence: `records/coproc.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/coproc.*`.

## cprint

Printing and quoting character values, including control-character representations.

- Native reference: 72 cold / 72 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 1/1; warm 1/1.
- Corpus files seen at shell-launcher entry points: `cprint.tests`.
- Expected transcript(s): `cprint.right`.
- Evidence: `records/cprint.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/cprint.*`.

## dbg-support

Debugger/source-stack behavior and tracing. Source-sensitive constructs may use native execution by design.

- Native reference: 371 cold / 371 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 2/2; warm 2/2.
- Corpus files seen at shell-launcher entry points: `dbg-support.tests`, `dbg-support3.sub`.
- Expected transcript(s): `dbg-support.right`.
- Evidence: `records/dbg-support.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/dbg-support.*`.

## dbg-support2

Debugger trap return values and control-flow effects; no blanket parser-error exclusions.

- Native reference: 7 cold / 7 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 1/1; warm 1/1.
- Corpus files seen at shell-launcher entry points: `dbg-support2.tests`.
- Expected transcript(s): `dbg-support2.right`.
- Evidence: `records/dbg-support2.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/dbg-support2.*`.

## dirstack

Directory-stack operations across both dstack and dstack2 transcripts; both captures must exist and match.

- Native reference: 79 cold / 79 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 2/2; warm 2/2.
- Corpus files seen at shell-launcher entry points: `dstack.tests`, `dstack2.tests`.
- Expected transcript(s): `dstack.right`, `dstack2.right`.
- Evidence: `records/dirstack.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/dirstack.*`.

## dollars

Dollar-at/star positional expansion and quoting through dollar-at-star and subsidiary cases.

- Native reference: 744 cold / 744 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 33/33; unchanged warm metadata files: 33. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 29/29; warm 29/29.
- Corpus files seen at shell-launcher entry points: `dollar-at-star`, `dollar-at-star1.sub`, `dollar-at-star10.sub`, `dollar-at-star11.sub`, `dollar-at-star2.sub`, `dollar-at-star3.sub`, `dollar-at-star4.sub`, `dollar-at-star5.sub`, `dollar-at-star6.sub`, `dollar-at-star7.sub`, `dollar-at-star8.sub`, `dollar-at-star9.sub`, `dollar-at1.sub`, `dollar-at2.sub`, `dollar-at3.sub`, `dollar-at4.sub`, `dollar-at5.sub`, `dollar-at6.sub`, `dollar-at7.sub`, `dollar-star1.sub`, `dollar-star10.sub`, `dollar-star2.sub`, `dollar-star3.sub`, `dollar-star4.sub`, `dollar-star5.sub`, `dollar-star6.sub`, `dollar-star7.sub`, `dollar-star8.sub`, `dollar-star9.sub`.
- Expected transcript(s): `dollar.right`.
- Evidence: `records/dollars.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/dollars.*`.

## dynvar

Dynamic shell variables and their observable behavior, including time-related checks written by the suite.

- Native reference: 7 cold / 7 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 2/2; warm 2/2.
- Corpus files seen at shell-launcher entry points: `dynvar.tests`.
- Expected transcript(s): `dynvar.right`.
- Evidence: `records/dynvar.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/dynvar.*`.

## errors

Shell error handling, invalid commands/arguments, and diagnostic/control-flow behavior.

- Native reference: 208 cold / 208 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 35/35; warm 35/35.
- Corpus files seen at shell-launcher entry points: `errors.tests`, `errors1.sub`, `errors2.sub`, `errors3.sub`, `errors4.sub`, `errors5.sub`, `errors6.sub`, `errors7.sub`, `errors8.sub`, `errors9.sub`.
- Expected transcript(s): `errors.right`.
- Evidence: `records/errors.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/errors.*`.

## execscript

Invocation modes, missing commands, binary/directory execution, startup files, argv0, and restored empty/unset PATH tests.

- Native reference: 172 cold / 172 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 1/1; warm 1/1. Native matches literal expected operands: False.
- Cache entries cold/warm: 5/6; unchanged warm metadata files: 3. These are retention evidence, not a per-command hit count.
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

## exp-tests

Parameter expansion and splitting; upstream expect-comment filtering is retained unchanged.

- Native reference: 419 cold / 419 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 23/23; unchanged warm metadata files: 23. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 15/15; warm 15/15.
- Corpus files seen at shell-launcher entry points: `exp.tests`, `exp1.sub`, `exp10.sub`, `exp11.sub`, `exp12.sub`, `exp13.sub`, `exp2.sub`, `exp3.sub`, `exp4.sub`, `exp5.sub`, `exp6.sub`, `exp7.sub`, `exp8.sub`, `exp9.sub`.
- Expected transcript(s): `exp.right`.
- Evidence: `records/exp-tests.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/exp-tests.*`.

## exportfunc

Exported functions and child-shell import behavior, with a 60-second per-run allowance.

- Native reference: 14 cold / 14 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: False / False.
- Driver status, native/Observe: cold 0/1; warm 0/1. Native matches literal expected operands: True.
- Cache entries cold/warm: 5/5; unchanged warm metadata files: 4. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 22/22; warm 22/22.
- Corpus files seen at shell-launcher entry points: `exportfunc.tests`, `exportfunc1.sub`, `exportfunc2.sub`, `exportfunc3.sub`.
- Expected transcript(s): `exportfunc.right`.
- Evidence: `records/exportfunc.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/exportfunc.*`.

## extglob

Extended glob patterns and matching; upstream explanatory-output filtering is preserved.

- Native reference: 184 cold / 184 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 2/4; unchanged warm metadata files: 2. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 8/8; warm 8/8.
- Corpus files seen at shell-launcher entry points: `extglob.tests`, `extglob1.sub`, `extglob1a.sub`, `extglob3.sub`, `extglob4.sub`, `extglob5.sub`, `extglob6.sub`, `extglob7.sub`.
- Expected transcript(s): `extglob.right`.
- Evidence: `records/extglob.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/extglob.*`.

## extglob2

Additional extended-pattern expansion and matching edge cases.

- Native reference: 70 cold / 70 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 1/1; warm 1/1.
- Corpus files seen at shell-launcher entry points: `extglob2.tests`.
- Expected transcript(s): `extglob2.right`.
- Evidence: `records/extglob2.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/extglob2.*`.

## extglob3

Extended-pattern regressions in the third upstream group.

- Native reference: 27 cold / 27 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 1/1; warm 1/1.
- Corpus files seen at shell-launcher entry points: `extglob3.tests`.
- Expected transcript(s): `extglob3.right`.
- Evidence: `records/extglob3.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/extglob3.*`.

## func

Function definition/invocation, argument scope, return behavior, and related diagnostics.

- Native reference: 169 cold / 169 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 2/4; unchanged warm metadata files: 2. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 11/11; warm 11/11.
- Corpus files seen at shell-launcher entry points: `func.tests`, `func1.sub`, `func2.sub`, `func3.sub`, `func4.sub`.
- Expected transcript(s): `func.right`.
- Evidence: `records/func.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/func.*`.

## getopts

Option parsing, OPTIND/OPTARG behavior, and invalid-option handling.

- Native reference: 68 cold / 68 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 19/19; warm 19/19.
- Corpus files seen at shell-launcher entry points: `getopts.tests`, `getopts1.sub`, `getopts10.sub`, `getopts2.sub`, `getopts3.sub`, `getopts4.sub`, `getopts5.sub`, `getopts6.sub`, `getopts7.sub`, `getopts8.sub`, `getopts9.sub`.
- Expected transcript(s): `getopts.right`.
- Evidence: `records/getopts.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/getopts.*`.

## glob-test

Filename expansion and locale-sensitive glob cases, using private generated locales.

- Native reference: 261 cold / 261 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 33/65; unchanged warm metadata files: 32. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 12/12; warm 12/12.
- Corpus files seen at shell-launcher entry points: `glob.tests`, `glob1.sub`, `glob10.sub`, `glob2.sub`, `glob3.sub`, `glob4.sub`, `glob5.sub`, `glob6.sub`, `glob7.sub`, `glob8.sub`, `glob9.sub`.
- Expected transcript(s): `glob.right`.
- Evidence: `records/glob-test.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/glob-test.*`.

## globstar

Recursive globbing, directory traversal, and matching corner cases.

- Native reference: 587 cold / 587 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 9/16; unchanged warm metadata files: 7. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 4/4; warm 4/4.
- Corpus files seen at shell-launcher entry points: `globstar.tests`, `globstar1.sub`, `globstar2.sub`, `globstar3.sub`.
- Expected transcript(s): `globstar.right`.
- Evidence: `records/globstar.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/globstar.*`.

## heredoc

Here-document expansion, quoting, nesting, and restored end-of-file syntax diagnostics.

- Native reference: 133 cold / 133 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 6/10; unchanged warm metadata files: 6. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 9/9; warm 9/9.
- Corpus files seen at shell-launcher entry points: `heredoc.tests`, `heredoc1.sub`, `heredoc2.sub`, `heredoc3.sub`, `heredoc4.sub`, `heredoc5.sub`, `heredoc6.sub`, `heredoc7.sub`.
- Expected transcript(s): `heredoc.right`.
- Evidence: `records/heredoc.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/heredoc.*`.

## herestr

Here-string input and expansion behavior.

- Native reference: 38 cold / 38 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 2/2; warm 2/2.
- Corpus files seen at shell-launcher entry points: `herestr.tests`, `herestr1.sub`.
- Expected transcript(s): `herestr.right`.
- Evidence: `records/herestr.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/herestr.*`.

## histexpand

History expansion and quoting; original-source/native handling is expected for history-sensitive scripts.

- Native reference: 246 cold / 246 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 8/8; warm 8/8.
- Corpus files seen at shell-launcher entry points: `histexp.tests`, `histexp1.sub`, `histexp2.sub`, `histexp3.sub`, `histexp4.sub`, `histexp5.sub`, `histexp6.sub`, `histexp7.sub`.
- Expected transcript(s): `histexp.right`.
- Evidence: `records/histexpand.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/histexpand.*`.

## history

History storage/manipulation and source-sensitive command text.

- Native reference: 299 cold / 299 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 11/11; warm 11/11.
- Corpus files seen at shell-launcher entry points: `history.tests`, `history1.sub`, `history2.sub`, `history3.sub`, `history4.sub`, `history5.sub`, `history6.sub`.
- Expected transcript(s): `history.right`.
- Evidence: `records/history.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/history.*`.

## ifs

IFS-driven word splitting with empty, whitespace, and non-whitespace separators.

- Native reference: 12 cold / 12 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 3/6; unchanged warm metadata files: 3. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 2/2; warm 2/2.
- Corpus files seen at shell-launcher entry points: `ifs.tests`, `ifs1.sub`.
- Expected transcript(s): `ifs.right`.
- Evidence: `records/ifs.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/ifs.*`.

## ifs-posix

POSIX field splitting, ordering, and the suite's own internal summary.

- Native reference: 1 cold / 1 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 1/1; warm 1/1.
- Corpus files seen at shell-launcher entry points: `ifs-posix.tests`.
- Expected transcript(s): `ifs-posix.right`.
- Evidence: `records/ifs-posix.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/ifs-posix.*`.

## input-test

Reading shell commands from stdin; this invocation mode deliberately executes natively.

- Native reference: 3 cold / 3 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 2/2; warm 2/2.
- Corpus files seen at shell-launcher entry points: `input-line.sub`.
- Expected transcript(s): `input.right`.
- Evidence: `records/input-test.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/input-test.*`.

## intl

Multibyte expansion, locale-dependent formatting, and Unicode conversion. Private French/Japanese/Chinese/German locales eliminate earlier skip warnings.

- Native reference: 57 cold / 57 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 2/2; unchanged warm metadata files: 2. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 7/7; warm 7/7.
- Corpus files seen at shell-launcher entry points: `intl.tests`, `intl1.sub`, `intl2.sub`, `intl3.sub`, `unicode1.sub`, `unicode2.sub`, `unicode3.sub`.
- Expected transcript(s): `intl.right`.
- Evidence: `records/intl.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/intl.*`.

## invert

Pipeline/command status inversion and control flow.

- Native reference: 10 cold / 10 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 1/1; unchanged warm metadata files: 1. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 1/1; warm 1/1.
- Corpus files seen at shell-launcher entry points: `invert.tests`.
- Expected transcript(s): `invert.right`.
- Evidence: `records/invert.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/invert.*`.

## iquote

Quoting and expansion regression cases from iquote.tests.

- Native reference: 92 cold / 92 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 2/2; warm 2/2.
- Corpus files seen at shell-launcher entry points: `iquote.tests`, `iquote1.sub`.
- Expected transcript(s): `iquote.right`.
- Evidence: `records/iquote.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/iquote.*`.

## jobs

Job control, waits, signals, and background processes. Each run deliberately waits roughly a minute; deadline is 120 seconds.

- Native reference: 120 cold / 120 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 2/3; unchanged warm metadata files: 2. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 9/9; warm 9/9.
- Corpus files seen at shell-launcher entry points: `jobs.tests`, `jobs1.sub`, `jobs2.sub`, `jobs3.sub`, `jobs4.sub`, `jobs5.sub`, `jobs6.sub`, `jobs7.sub`.
- Expected transcript(s): `jobs.right`.
- Evidence: `records/jobs.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/jobs.*`.

## lastpipe

Last pipeline element execution and variable/exit-status effects.

- Native reference: 22 cold / 22 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 1/1; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 4/4; warm 4/4.
- Corpus files seen at shell-launcher entry points: `lastpipe.tests`, `lastpipe1.sub`, `lastpipe2.sub`, `lastpipe3.sub`.
- Expected transcript(s): `lastpipe.right`.
- Evidence: `records/lastpipe.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/lastpipe.*`.

## mapfile

Line-array input, delimiters/options, callbacks, and array update behavior.

- Native reference: 170 cold / 170 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 3/3; warm 3/3.
- Corpus files seen at shell-launcher entry points: `mapfile.tests`, `mapfile1.sub`, `mapfile2.sub`.
- Expected transcript(s): `mapfile.right`.
- Evidence: `records/mapfile.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/mapfile.*`.

## more-exp

Additional expansion edge cases; native diagnostic locations are normalized without suppressing results.

- Native reference: 214 cold / 214 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: False / False.
- Driver status, native/Observe: cold 0/1; warm 0/1. Native matches literal expected operands: True.
- Cache entries cold/warm: 59/59; unchanged warm metadata files: 59. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 1/1; warm 1/1.
- Corpus files seen at shell-launcher entry points: `more-exp.tests`.
- Expected transcript(s): `more-exp.right`.
- Evidence: `records/more-exp.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/more-exp.*`.

## nameref

Name references, indirect updates, scope, invalid references, and error diagnostics.

- Native reference: 560 cold / 560 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: False / False.
- Driver status, native/Observe: cold 0/1; warm 0/1. Native matches literal expected operands: True.
- Cache entries cold/warm: 6/6; unchanged warm metadata files: 6. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 25/25; warm 25/25.
- Corpus files seen at shell-launcher entry points: `nameref.tests`, `nameref1.sub`, `nameref10.sub`, `nameref11.sub`, `nameref12.sub`, `nameref13.sub`, `nameref14.sub`, `nameref15.sub`, `nameref16.sub`, `nameref17.sub`, `nameref18.sub`, `nameref19.sub`, `nameref2.sub`, `nameref20.sub`, `nameref21.sub`, `nameref22.sub`, `nameref23.sub`, `nameref3.sub`, `nameref4.sub`, `nameref5.sub`, `nameref6.sub`, `nameref7.sub`, `nameref8.sub`, `nameref9.sub`.
- Expected transcript(s): `nameref.right`.
- Evidence: `records/nameref.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/nameref.*`.

## new-exp

Expansion regressions including large unbroken outputs and process substitution; comparison avoids quadratic path matching.

- Native reference: 795 cold / 795 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: False / False.
- Driver status, native/Observe: cold 0/1; warm 0/1. Native matches literal expected operands: True.
- Cache entries cold/warm: 6/7; unchanged warm metadata files: 6. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 28/28; warm 28/28.
- Corpus files seen at shell-launcher entry points: `new-exp.tests`, `new-exp1.sub`, `new-exp10.sub`, `new-exp11.sub`, `new-exp12.sub`, `new-exp13.sub`, `new-exp14.sub`, `new-exp15.sub`, `new-exp16.sub`, `new-exp2.sub`, `new-exp3.sub`, `new-exp4.sub`, `new-exp5.sub`, `new-exp6.sub`, `new-exp7.sub`, `new-exp8.sub`, `new-exp9.sub`.
- Expected transcript(s): `new-exp.right`.
- Evidence: `records/new-exp.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/new-exp.*`.

## nquote

Quoting/expansion regression group nquote, with upstream expect-line filtering.

- Native reference: 80 cold / 80 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 3/3; unchanged warm metadata files: 3. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 6/6; warm 6/6.
- Corpus files seen at shell-launcher entry points: `nquote.tests`, `nquote1.sub`, `nquote2.sub`, `nquote3.sub`, `nquote4.sub`, `nquote5.sub`.
- Expected transcript(s): `nquote.right`.
- Evidence: `records/nquote.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/nquote.*`.

## nquote1

Quoting/expansion regression group nquote1.

- Native reference: 131 cold / 131 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 1/1; warm 1/1.
- Corpus files seen at shell-launcher entry points: `nquote1.tests`.
- Expected transcript(s): `nquote1.right`.
- Evidence: `records/nquote1.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/nquote1.*`.

## nquote2

Quoting/expansion regression group nquote2.

- Native reference: 76 cold / 76 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 1/1; warm 1/1.
- Corpus files seen at shell-launcher entry points: `nquote2.tests`.
- Expected transcript(s): `nquote2.right`.
- Evidence: `records/nquote2.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/nquote2.*`.

## nquote3

Quoting/expansion regression group nquote3.

- Native reference: 60 cold / 60 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 1/1; warm 1/1.
- Corpus files seen at shell-launcher entry points: `nquote3.tests`.
- Expected transcript(s): `nquote3.right`.
- Evidence: `records/nquote3.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/nquote3.*`.

## nquote4

Quoting/expansion regression group nquote4, including its binary-safe diff capability check (excluded from scoring).

- Native reference: 18 cold / 18 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 1/1; warm 1/1.
- Corpus files seen at shell-launcher entry points: `nquote4.tests`.
- Expected transcript(s): `nquote4.right`.
- Evidence: `records/nquote4.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/nquote4.*`.

## nquote5

Quoting/expansion regression group nquote5.

- Native reference: 86 cold / 86 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 1/1; warm 1/1.
- Corpus files seen at shell-launcher entry points: `nquote5.tests`.
- Expected transcript(s): `nquote5.right`.
- Evidence: `records/nquote5.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/nquote5.*`.

## parser

Shell grammar, tokenization, and parser regression cases, retained without source edits.

- Native reference: 16 cold / 16 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 12/12; warm 12/12.
- Corpus files seen at shell-launcher entry points: `parser.tests`, `parser1.sub`, `posix2syntax.sub`.
- Expected transcript(s): `parser.right`.
- Evidence: `records/parser.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/parser.*`.

## posix2

POSIX behavior and diagnostic checks using the original driver's filtering.

- Native reference: 4 cold / 4 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: False / False.
- Driver status, native/Observe: cold 0/1; warm 0/1. Native matches literal expected operands: True.
- Cache entries cold/warm: 2/2; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 9/9; warm 9/9.
- Corpus files seen at shell-launcher entry points: `posix2.tests`.
- Expected transcript(s): `posix2.right`.
- Evidence: `records/posix2.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/posix2.*`.

## posixexp

POSIX expansion, including the restored unterminated parameter-expansion diagnostic.

- Native reference: 308 cold / 308 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 13/14; unchanged warm metadata files: 13. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 82/82; warm 82/82.
- Corpus files seen at shell-launcher entry points: `posixexp.tests`, `posixexp1.sub`, `posixexp2.sub`, `posixexp3.sub`, `posixexp4.sub`, `posixexp5.sub`, `posixexp6.sub`, `posixexp7.sub`, `posixexp8.sub`.
- Expected transcript(s): `posixexp.right`.
- Evidence: `records/posixexp.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/posixexp.*`.

## posixexp2

Additional POSIX quoting/parameter expansions; restores two previously commented-out cases.

- Native reference: 40 cold / 40 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 1/1; warm 1/1.
- Corpus files seen at shell-launcher entry points: `posixexp2.tests`.
- Expected transcript(s): `posixexp2.right`.
- Evidence: `records/posixexp2.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/posixexp2.*`.

## posixpat

POSIX pattern matching and bracket-pattern behavior.

- Native reference: 42 cold / 42 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 1/1; warm 1/1.
- Corpus files seen at shell-launcher entry points: `posixpat.tests`.
- Expected transcript(s): `posixpat.right`.
- Evidence: `records/posixpat.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/posixpat.*`.

## posixpipe

POSIX pipeline behavior and status propagation.

- Native reference: 41 cold / 41 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 1/1; warm 1/1.
- Corpus files seen at shell-launcher entry points: `posixpipe.tests`.
- Expected transcript(s): `posixpipe.right`.
- Evidence: `records/posixpipe.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/posixpipe.*`.

## precedence

Shell operator precedence and control-flow grouping.

- Native reference: 28 cold / 28 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 1/1; warm 1/1.
- Corpus files seen at shell-launcher entry points: `precedence.tests`.
- Expected transcript(s): `prec.right`.
- Evidence: `records/precedence.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/precedence.*`.

## printf

Formatting, escapes, assignment output, and restored extglob/printf interactions; upstream cat -v output conversion remains active.

- Native reference: 298 cold / 298 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 5/5; warm 5/5.
- Corpus files seen at shell-launcher entry points: `printf.tests`, `printf1.sub`, `printf2.sub`, `printf3.sub`, `printf4.sub`.
- Expected transcript(s): `printf.right`.
- Evidence: `records/printf.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/printf.*`.

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

## quote

Quoting/expansion behavior, including restored POSIX quote handling in quote1.sub.

- Native reference: 182 cold / 182 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 14/14; unchanged warm metadata files: 14. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 5/5; warm 5/5.
- Corpus files seen at shell-launcher entry points: `quote.tests`, `quote1.sub`, `quote2.sub`, `quote3.sub`, `quote4.sub`.
- Expected transcript(s): `quote.right`.
- Evidence: `records/quote.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/quote.*`.

## quotearray

Quoting of indexed/associative arrays and expanded array words.

- Native reference: 152 cold / 152 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 6/6; warm 6/6.
- Corpus files seen at shell-launcher entry points: `quotearray.tests`, `quotearray1.sub`, `quotearray2.sub`, `quotearray3.sub`, `quotearray4.sub`, `quotearray5.sub`.
- Expected transcript(s): `quotearray.right`.
- Evidence: `records/quotearray.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/quotearray.*`.

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

## redir

Descriptor redirection, file creation, invalid descriptors/paths, and error behavior.

- Native reference: 163 cold / 163 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: False / False.
- Driver status, native/Observe: cold 0/1; warm 0/1. Native matches literal expected operands: True.
- Cache entries cold/warm: 1/1; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 14/14; warm 14/14.
- Corpus files seen at shell-launcher entry points: `redir.tests`, `redir10.sub`, `redir11.sub`, `redir3.sub`, `redir4.sub`, `redir5.sub`, `redir6.sub`, `redir7.sub`, `redir8.sub`, `redir9.sub`.
- Expected transcript(s): `redir.right`.
- Evidence: `records/redir.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/redir.*`.

## rhs-exp

Right-hand-side assignment expansion and its original driver's redirection ordering.

- Native reference: 105 cold / 105 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 35/35; unchanged warm metadata files: 35. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 2/2; warm 2/2.
- Corpus files seen at shell-launcher entry points: `rhs-exp.tests`, `rhs-exp1.sub`.
- Expected transcript(s): `rhs-exp.right`.
- Evidence: `records/rhs-exp.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/rhs-exp.*`.

## rsh

Restricted-shell behavior; restricted invocation/source modes can use native execution.

- Native reference: 19 cold / 19 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 3/3; warm 3/3.
- Corpus files seen at shell-launcher entry points: `rsh.tests`, `rsh1.sub`, `rsh2.sub`.
- Expected transcript(s): `rsh.right`.
- Evidence: `records/rsh.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/rsh.*`.

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

## set-x

Execution tracing and source-text display; xtrace is deliberately kept native where required.

- Native reference: 60 cold / 60 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 2/2; warm 2/2.
- Corpus files seen at shell-launcher entry points: `set-x.tests`, `set-x1.sub`.
- Expected transcript(s): `set-x.right`.
- Evidence: `records/set-x.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/set-x.*`.

## shopt

Shell-option state, enable/disable behavior, and effects on execution.

- Native reference: 312 cold / 312 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 1/2; unchanged warm metadata files: 1. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 5/5; warm 5/5.
- Corpus files seen at shell-launcher entry points: `shopt.tests`, `shopt1.sub`.
- Expected transcript(s): `shopt.right`.
- Evidence: `records/shopt.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/shopt.*`.

## strip

Parameter prefix/suffix removal and pattern handling.

- Native reference: 12 cold / 12 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 1/1; warm 1/1.
- Corpus files seen at shell-launcher entry points: `strip.tests`.
- Expected transcript(s): `strip.right`.
- Evidence: `records/strip.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/strip.*`.

## test

Test builtin predicates/operators, including terminal-dependent checks enabled by the controlling terminal.

- Native reference: 297 cold / 297 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: False / False.
- Driver status, native/Observe: cold 0/1; warm 0/1. Native matches literal expected operands: True.
- Cache entries cold/warm: 13/13; unchanged warm metadata files: 1. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 2/2; warm 2/2.
- Corpus files seen at shell-launcher entry points: `test.tests`, `test1.sub`.
- Expected transcript(s): `test.right`.
- Evidence: `records/test.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/test.*`.

## tilde

Tilde expansion in words and assignments.

- Native reference: 28 cold / 28 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 1/1; warm 1/1.
- Corpus files seen at shell-launcher entry points: `tilde.tests`.
- Expected transcript(s): `tilde.right`.
- Evidence: `records/tilde.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/tilde.*`.

## tilde2

Additional tilde-expansion and assignment-context regressions.

- Native reference: 28 cold / 28 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 1/1; unchanged warm metadata files: 1. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 2/2; warm 2/2.
- Corpus files seen at shell-launcher entry points: `tilde2.tests`, `tilde3.sub`.
- Expected transcript(s): `tilde2.right`.
- Evidence: `records/tilde2.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/tilde2.*`.

## trap

Signal, ERR/EXIT traps, subshells, and direct script execution. Original direct invocations are preserved rather than rewritten by the harness.

- Native reference: 115 cold / 115 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: True / True.
- Driver status, native/Observe: cold 0/0; warm 0/0. Native matches literal expected operands: True.
- Cache entries cold/warm: 0/0; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 4/4; warm 4/4.
- Corpus files seen at shell-launcher entry points: `trap.tests`, `trap3.sub`, `trap4.sub`, `trap6.sub`.
- Expected transcript(s): `trap.right`.
- Evidence: `records/trap.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/trap.*`.

## type

Command classification and function display. Only the two reviewed Incr executable prefixes in the displayed function are normalized.

- Native reference: 135 cold / 135 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: False / False.
- Driver status, native/Observe: cold 0/1; warm 0/1. Native matches literal expected operands: True.
- Cache entries cold/warm: 2/2; unchanged warm metadata files: 0. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 5/5; warm 5/5.
- Corpus files seen at shell-launcher entry points: `type.tests`, `type1.sub`, `type2.sub`, `type3.sub`, `type4.sub`.
- Expected transcript(s): `type.right`.
- Evidence: `records/type.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/type.*`.

## varenv

Variable scope, temporary assignments, export/environment propagation, and declaration behavior.

- Native reference: 277 cold / 277 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: False / False.
- Driver status, native/Observe: cold 0/1; warm 0/1. Native matches literal expected operands: True.
- Cache entries cold/warm: 4/7; unchanged warm metadata files: 4. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 27/27; warm 27/27.
- Corpus files seen at shell-launcher entry points: `varenv.tests`, `varenv1.sub`, `varenv10.sub`, `varenv11.sub`, `varenv12.sub`, `varenv13.sub`, `varenv14.sub`, `varenv15.sub`, `varenv16.sub`, `varenv17.sub`, `varenv18.sub`, `varenv19.sub`, `varenv2.sub`, `varenv20.sub`, `varenv21.sub`, `varenv22.sub`, `varenv3.sub`, `varenv4.sub`, `varenv5.sub`, `varenv6.sub`, `varenv7.sub`, `varenv8.sub`, `varenv9.sub`.
- Expected transcript(s): `varenv.right`.
- Evidence: `records/varenv.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/varenv.*`.

## vredir

Variable-allocated file descriptors, readonly variables, and terminal-dependent redirections.

- Native reference: 101 cold / 101 warm lines; normalized Observe matches: True / True. Byte-exact including stderr: False / False.
- Driver status, native/Observe: cold 0/1; warm 0/1. Native matches literal expected operands: True.
- Cache entries cold/warm: 4/7; unchanged warm metadata files: 3. These are retention evidence, not a per-command hit count.
- Native/Observe cleanup required: cold True/True; warm True/True. Cold/warm output variation: none.
- Shell-launcher calls, native/Observe: cold 9/9; warm 9/9.
- Corpus files seen at shell-launcher entry points: `vredir.tests`, `vredir1.sub`, `vredir2.sub`, `vredir3.sub`, `vredir4.sub`, `vredir5.sub`, `vredir6.sub`, `vredir7.sub`, `vredir8.sub`.
- Expected transcript(s): `vredir.right`.
- Evidence: `records/vredir.{bash,observe}.{cold,warm}.json.gz`; nonempty differences are under `diffs/vredir.*`.
