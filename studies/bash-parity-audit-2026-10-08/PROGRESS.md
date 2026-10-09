# Bash parity audit — 2026-10-08

## Scope and plan

Compare the active Incr Observe implementation with local main, read historical design and qualification logs, and independently rerun the vendored Bash suite against native Bash. Work incrementally with per-process-tree deadlines, private mount namespaces and private /tmp. Preserve raw records and audit normalization rather than accepting historical pass labels. No runtime edits are planned unless a concrete failure warrants a separately documented fix.

## Initial inspection

- Incr observe: bd11f3a; local main and origin/main: 4b8e5dd. Main has a detached worktree at ../incr-main-qualification.
- Observe main: b5ad47a. Both repositories started clean.
- Existing qualification harness captures actual diff operands, freezes runtime files, and uses a subreaper with bounded TERM/KILL cleanup.
- Existing harness has broad normalization and can disregard driver exit status when diff captures exist; these require independent auditing.
- Existing Bash build, parser environment, and release binaries are present. Will rebuild current sources under deadlines before freezing.
- Stages: design/log review and setup; small native/Observe/main probe; full native/Observe suite; individual mismatch review and targeted reruns; final evidence report.

## Setup
Both current release builds passed within one second under 180-second process-tree deadlines. Initial harness-copy command used an incorrect relative path and exited before testing; corrected immediately. Audit runner uses its own fixture directory and saves expected diff operands and cache entry counts.

- `smoke/dollars/bash`: historical comparator=MATCH, status=0, 0.705s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `smoke/dollars/observe`: historical comparator=MATCH, status=0, 5.540s, timeout=False, captures=1, cache entries=33, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `smoke/dollars/main`: historical comparator=DIFF, status=-15, 15.000s, timeout=True, captures=0, cache entries=29, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `smoke/quote/bash`: historical comparator=MATCH, status=1, 0.243s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `smoke/quote/observe`: historical comparator=MATCH, status=1, 1.245s, timeout=False, captures=1, cache entries=14, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `smoke/quote/main`: historical comparator=MATCH, status=1, 7.989s, timeout=False, captures=1, cache entries=15, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `smoke/execscript/bash`: historical comparator=MATCH, status=1, 0.534s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `smoke/execscript/observe`: historical comparator=MATCH, status=1, 3.662s, timeout=False, captures=1, cache entries=1, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `smoke/execscript/main`: historical comparator=DIFF, status=1, 9.523s, timeout=False, captures=1, cache entries=11, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

## Full-suite launch
Smoke: Observe matches native Bash for dollars, quote and execscript. Main dollars hit the 15-second smoke budget; main quote matched and execscript differed. No survivors in smoke records. Full native/Observe run: 83 cases, 45-second ordinary deadlines, 60 seconds for exportfunc, 120 seconds for jobs (historically 62 seconds of intentional waits), 900-second outer deadline. Cache policy is default live.

- `full/alias/bash`: historical comparator=MATCH, status=0, 0.119s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/alias/observe`: historical comparator=MATCH, status=0, 1.208s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/appendop/bash`: historical comparator=MATCH, status=0, 0.072s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/appendop/observe`: historical comparator=MATCH, status=0, 0.475s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/arith/bash`: historical comparator=MATCH, status=0, 0.186s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/arith/observe`: historical comparator=MATCH, status=0, 1.501s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/arith-for/bash`: historical comparator=MATCH, status=0, 0.243s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/arith-for/observe`: historical comparator=MATCH, status=0, 0.440s, timeout=False, captures=1, cache entries=2, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/array/bash`: historical comparator=MATCH, status=1, 0.508s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/array/observe`: historical comparator=MATCH, status=1, 5.591s, timeout=False, captures=1, cache entries=47, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/array2/bash`: historical comparator=MATCH, status=0, 0.157s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/array2/observe`: historical comparator=MATCH, status=0, 0.594s, timeout=False, captures=1, cache entries=19, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/assoc/bash`: historical comparator=MATCH, status=0, 2.247s, timeout=False, captures=1, cache entries=0, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `full/assoc/observe`: historical comparator=MATCH, status=1, 5.269s, timeout=False, captures=1, cache entries=18, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `full/attr/bash`: historical comparator=MATCH, status=0, 0.074s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/attr/observe`: historical comparator=MATCH, status=0, 0.513s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/braces/bash`: historical comparator=MATCH, status=0, 0.076s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/braces/observe`: historical comparator=MATCH, status=0, 0.214s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/builtins/bash`: historical comparator=MATCH, status=1, 1.203s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/builtins/observe`: historical comparator=MATCH, status=1, 3.471s, timeout=False, captures=1, cache entries=1, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/case/bash`: historical comparator=MATCH, status=1, 0.097s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/case/observe`: historical comparator=MATCH, status=1, 0.929s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/casemod/bash`: historical comparator=MATCH, status=0, 0.072s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/casemod/observe`: historical comparator=MATCH, status=0, 0.239s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/complete/bash`: historical comparator=MATCH, status=0, 0.067s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/complete/observe`: historical comparator=MATCH, status=0, 0.383s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/comsub/bash`: historical comparator=MATCH, status=1, 0.174s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/comsub/observe`: historical comparator=MATCH, status=1, 1.180s, timeout=False, captures=1, cache entries=9, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/comsub-eof/bash`: historical comparator=MATCH, status=1, 0.112s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/comsub-eof/observe`: historical comparator=MATCH, status=1, 1.188s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/comsub-posix/bash`: historical comparator=MATCH, status=1, 0.236s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/comsub-posix/observe`: historical comparator=MATCH, status=1, 1.148s, timeout=False, captures=1, cache entries=4, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/cond/bash`: historical comparator=MATCH, status=0, 0.085s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/cond/observe`: historical comparator=MATCH, status=0, 0.738s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/coproc/bash`: historical comparator=MATCH, status=0, 3.089s, timeout=False, captures=1, cache entries=0, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `full/coproc/observe`: historical comparator=MATCH, status=0, 3.261s, timeout=False, captures=1, cache entries=3, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `full/cprint/bash`: historical comparator=MATCH, status=0, 0.073s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/cprint/observe`: historical comparator=MATCH, status=0, 0.320s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/dbg-support/bash`: historical comparator=MATCH, status=0, 0.101s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/dbg-support/observe`: historical comparator=MATCH, status=0, 0.385s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/dbg-support2/bash`: historical comparator=MATCH, status=0, 0.075s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/dbg-support2/observe`: historical comparator=MATCH, status=0, 0.186s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/dirstack/bash`: historical comparator=MATCH, status=0, 0.107s, timeout=False, captures=2, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/dirstack/observe`: historical comparator=MATCH, status=0, 0.467s, timeout=False, captures=2, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/dollars/bash`: historical comparator=MATCH, status=0, 0.769s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/dollars/observe`: historical comparator=MATCH, status=0, 5.987s, timeout=False, captures=1, cache entries=33, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/dynvar/bash`: historical comparator=MATCH, status=0, 2.088s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/dynvar/observe`: historical comparator=MATCH, status=0, 2.230s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/errors/bash`: historical comparator=MATCH, status=0, 0.167s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/errors/observe`: historical comparator=MATCH, status=0, 1.942s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/execscript/bash`: historical comparator=MATCH, status=1, 0.474s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/execscript/observe`: historical comparator=MATCH, status=1, 3.443s, timeout=False, captures=1, cache entries=1, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/exp-tests/bash`: historical comparator=MATCH, status=0, 0.425s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/exp-tests/observe`: historical comparator=MATCH, status=0, 2.935s, timeout=False, captures=1, cache entries=23, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/exportfunc/bash`: historical comparator=MATCH, status=0, 0.148s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/exportfunc/observe`: historical comparator=MATCH, status=1, 11.308s, timeout=False, captures=1, cache entries=1, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/extglob/bash`: historical comparator=MATCH, status=0, 0.166s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/extglob/observe`: historical comparator=MATCH, status=0, 1.216s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/extglob2/bash`: historical comparator=MATCH, status=0, 0.091s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/extglob2/observe`: historical comparator=MATCH, status=0, 0.217s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/extglob3/bash`: historical comparator=MATCH, status=0, 0.083s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/extglob3/observe`: historical comparator=MATCH, status=0, 0.293s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/func/bash`: historical comparator=MATCH, status=0, 5.161s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/func/observe`: historical comparator=MATCH, status=0, 5.948s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/getopts/bash`: historical comparator=MATCH, status=0, 0.144s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/getopts/observe`: historical comparator=MATCH, status=0, 2.881s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/glob-test/bash`: historical comparator=MATCH, status=1, 0.355s, timeout=False, captures=2, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/glob-test/observe`: historical comparator=MATCH, status=1, 2.399s, timeout=False, captures=2, cache entries=13, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/globstar/bash`: historical comparator=MATCH, status=0, 0.157s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/globstar/observe`: historical comparator=MATCH, status=0, 0.838s, timeout=False, captures=1, cache entries=3, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/heredoc/bash`: historical comparator=MATCH, status=1, 0.225s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/heredoc/observe`: historical comparator=MATCH, status=1, 1.393s, timeout=False, captures=1, cache entries=5, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/herestr/bash`: historical comparator=MATCH, status=0, 0.093s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/herestr/observe`: historical comparator=MATCH, status=0, 0.412s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/histexpand/bash`: historical comparator=MATCH, status=0, 0.133s, timeout=False, captures=1, cache entries=0, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `full/histexpand/observe`: historical comparator=MATCH, status=0, 1.175s, timeout=False, captures=1, cache entries=0, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `full/history/bash`: historical comparator=MATCH, status=0, 0.126s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/history/observe`: historical comparator=MATCH, status=0, 1.039s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/ifs/bash`: historical comparator=MATCH, status=0, 0.090s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/ifs/observe`: historical comparator=MATCH, status=0, 0.444s, timeout=False, captures=1, cache entries=2, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

## Design/log review checkpoint
Read the consolidated 1,283-line work log, early agent design/benchmark notes, Observe design/context, audit plans, effect-replay investigation and dated final reports. Saved document hashes and a main-versus-Observe design comparison. Several early documents are stale; current code and latest evidence take precedence. Strict comparison of the first 24 completed full-suite pairs needs only source-location/PID normalization; assoc driver status differs solely because its expected-output diff reports a transformed source location.

- `full/ifs-posix/bash`: historical comparator=MATCH, status=0, 10.645s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/ifs-posix/observe`: historical comparator=MATCH, status=0, 10.887s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/input-test/bash`: historical comparator=MATCH, status=0, 0.072s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/input-test/observe`: historical comparator=MATCH, status=0, 0.206s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/intl/bash`: historical comparator=MATCH, status=1, 0.393s, timeout=False, captures=2, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/intl/observe`: historical comparator=MATCH, status=1, 1.336s, timeout=False, captures=2, cache entries=2, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/invert/bash`: historical comparator=MATCH, status=0, 0.078s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/invert/observe`: historical comparator=MATCH, status=0, 0.234s, timeout=False, captures=1, cache entries=1, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/iquote/bash`: historical comparator=MATCH, status=0, 0.219s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/iquote/observe`: historical comparator=MATCH, status=0, 0.426s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/jobs/bash`: historical comparator=MATCH, status=0, 62.178s, timeout=False, captures=1, cache entries=0, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- Private locale `zh_HK.big5hkscs` generation: status 0, generated=True, timeout=False; no host locale changes.

## Coverage improvement
Full suite has reached job-control without timeouts. Raw glob-test has one extra wrapper startup locale warning; intl skips French ISO-8859-1 and Japanese Shift-JIS subtests in the host environment. Preparing four private locales and an isolated /usr/lib/locale bind mount for a supplemental paired run. Full-suite records retain original host-locale behavior.

- Private locale `fr_FR.ISO8859-1` generation: status 0, generated=True, timeout=False; no host locale changes.

- Private locale `ja_JP.SJIS` generation: status 1, generated=True, timeout=False; no host locale changes.

- Private locale `zh_TW.BIG5` generation: status 0, generated=True, timeout=False; no host locale changes.

Private locale verification: locale -a lists all four new locales and each charmap query succeeds in the private mount namespace. Shift-JIS localedef returned its documented ASCII-compatibility warning (status 1) but generated a functioning locale. A quick result-display script initially encountered the summary list rather than a single record; no test was affected.

- `full/jobs/observe`: historical comparator=MATCH, status=0, 63.395s, timeout=False, captures=1, cache entries=1, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `full/lastpipe/bash`: historical comparator=MATCH, status=0, 0.098s, timeout=False, captures=1, cache entries=0, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `full/lastpipe/observe`: historical comparator=MATCH, status=0, 0.705s, timeout=False, captures=1, cache entries=0, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `full/mapfile/bash`: historical comparator=MATCH, status=0, 0.083s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/mapfile/observe`: historical comparator=MATCH, status=0, 0.462s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/more-exp/bash`: historical comparator=MATCH, status=0, 0.402s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/more-exp/observe`: historical comparator=MATCH, status=1, 1.491s, timeout=False, captures=1, cache entries=59, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/nameref/bash`: historical comparator=MATCH, status=0, 0.225s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/nameref/observe`: historical comparator=MATCH, status=1, 4.145s, timeout=False, captures=1, cache entries=6, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/new-exp/bash`: historical comparator=MATCH, status=0, 0.646s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/new-exp/observe`: historical comparator=MATCH, status=1, 3.266s, timeout=False, captures=1, cache entries=5, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/nquote/bash`: historical comparator=MATCH, status=0, 0.142s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/nquote/observe`: historical comparator=MATCH, status=0, 1.050s, timeout=False, captures=1, cache entries=3, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/nquote1/bash`: historical comparator=MATCH, status=0, 0.171s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/nquote1/observe`: historical comparator=MATCH, status=0, 0.254s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/nquote2/bash`: historical comparator=MATCH, status=0, 0.145s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/nquote2/observe`: historical comparator=MATCH, status=0, 0.257s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/nquote3/bash`: historical comparator=MATCH, status=0, 0.109s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/nquote3/observe`: historical comparator=MATCH, status=0, 0.249s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/nquote4/bash`: historical comparator=MATCH, status=0, 0.140s, timeout=False, captures=2, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/nquote4/observe`: historical comparator=MATCH, status=0, 0.245s, timeout=False, captures=2, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/nquote5/bash`: historical comparator=MATCH, status=0, 0.113s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/nquote5/observe`: historical comparator=MATCH, status=0, 0.261s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/parser/bash`: historical comparator=MATCH, status=0, 0.086s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/parser/observe`: historical comparator=MATCH, status=0, 0.496s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/posix2/bash`: historical comparator=MATCH, status=0, 0.117s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/posix2/observe`: historical comparator=MATCH, status=1, 0.451s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/posixexp/bash`: historical comparator=MATCH, status=1, 0.738s, timeout=False, captures=1, cache entries=0, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `full/posixexp/observe`: historical comparator=MATCH, status=1, 2.741s, timeout=False, captures=1, cache entries=26, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `full/posixexp2/bash`: historical comparator=MATCH, status=1, 0.099s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/posixexp2/observe`: historical comparator=MATCH, status=1, 0.338s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/posixpat/bash`: historical comparator=MATCH, status=0, 0.060s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/posixpat/observe`: historical comparator=MATCH, status=0, 0.166s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/posixpipe/bash`: historical comparator=MATCH, status=0, 0.062s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/posixpipe/observe`: historical comparator=MATCH, status=0, 0.188s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/precedence/bash`: historical comparator=MATCH, status=0, 0.144s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/precedence/observe`: historical comparator=MATCH, status=0, 0.262s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/printf/bash`: historical comparator=MATCH, status=1, 0.098s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/printf/observe`: historical comparator=MATCH, status=1, 0.728s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/procsub/bash`: historical comparator=MATCH, status=0, 2.418s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/procsub/observe`: historical comparator=MATCH, status=0, 2.900s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/quote/bash`: historical comparator=MATCH, status=1, 0.183s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/quote/observe`: historical comparator=MATCH, status=1, 1.211s, timeout=False, captures=1, cache entries=14, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/quotearray/bash`: historical comparator=MATCH, status=0, 0.108s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/quotearray/observe`: historical comparator=MATCH, status=0, 1.118s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/read/bash`: historical comparator=MATCH, status=1, 5.581s, timeout=False, captures=1, cache entries=0, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `full/read/observe`: historical comparator=MATCH, status=1, 7.474s, timeout=False, captures=1, cache entries=5, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `full/redir/bash`: historical comparator=MATCH, status=0, 0.395s, timeout=False, captures=1, cache entries=0, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `full/redir/observe`: historical comparator=MATCH, status=1, 1.902s, timeout=False, captures=1, cache entries=0, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `full/rhs-exp/bash`: historical comparator=MATCH, status=0, 0.158s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/rhs-exp/observe`: historical comparator=MATCH, status=0, 0.882s, timeout=False, captures=1, cache entries=35, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/rsh/bash`: historical comparator=MATCH, status=0, 0.081s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/rsh/observe`: historical comparator=MATCH, status=0, 0.458s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/set-e/bash`: historical comparator=MATCH, status=0, 0.227s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/set-e/observe`: historical comparator=MATCH, status=0, 0.812s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/set-x/bash`: historical comparator=MATCH, status=0, 0.073s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/set-x/observe`: historical comparator=MATCH, status=0, 0.326s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/shopt/bash`: historical comparator=MATCH, status=0, 0.174s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/shopt/observe`: historical comparator=MATCH, status=0, 0.638s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/strip/bash`: historical comparator=MATCH, status=0, 0.086s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/strip/observe`: historical comparator=MATCH, status=0, 0.239s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/test/bash`: historical comparator=MATCH, status=1, 3.143s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/test/observe`: historical comparator=MATCH, status=1, 3.576s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/tilde/bash`: historical comparator=MATCH, status=0, 0.070s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/tilde/observe`: historical comparator=MATCH, status=0, 0.208s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/tilde2/bash`: historical comparator=MATCH, status=0, 0.084s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/tilde2/observe`: historical comparator=MATCH, status=0, 0.362s, timeout=False, captures=1, cache entries=1, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

## Comparator performance
The new-exp fixture contains very long whitespace-free output. The historical normalization regex retried its path pattern at every character, adding tens of seconds of CPU time outside command deadlines. Anchored the audit-local patterns to token starts; this preserves their intended matches while avoiding quadratic scanning. Runtime and existing qualification scripts are unchanged. The running full sweep retains its initially loaded comparator; its outer 900-second deadline remains active.

- `full/trap/bash`: historical comparator=MATCH, status=0, 15.121s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/trap/observe`: historical comparator=MATCH, status=0, 16.070s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/type/bash`: historical comparator=MATCH, status=0, 0.112s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/type/observe`: historical comparator=MATCH, status=1, 0.873s, timeout=False, captures=1, cache entries=1, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/varenv/bash`: historical comparator=MATCH, status=0, 0.236s, timeout=False, captures=1, cache entries=0, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `full/varenv/observe`: historical comparator=MATCH, status=1, 3.476s, timeout=False, captures=1, cache entries=3, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `full/vredir/bash`: historical comparator=MATCH, status=1, 0.108s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `full/vredir/observe`: historical comparator=MATCH, status=1, 1.416s, timeout=False, captures=1, cache entries=3, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `with-locales/glob-test/bash`: historical comparator=MATCH, status=0, 0.359s, timeout=False, captures=2, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

## Full sweep completed
166/166 planned records across all 83 groups exist with unique case/mode keys. Historical comparator matches all 83 Observe groups; independent raw normalization audit follows. Outer supervisor completed in 402.16 seconds with no timeout or surviving descendants. Locale-complete glob/intl follow-up is now running.

- `with-locales/glob-test/observe`: historical comparator=MATCH, status=0, 2.446s, timeout=False, captures=2, cache entries=13, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `with-locales/intl/bash`: historical comparator=MATCH, status=1, 0.430s, timeout=False, captures=2, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `with-locales/intl/observe`: historical comparator=MATCH, status=1, 1.443s, timeout=False, captures=2, cache entries=2, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

## Follow-up: main-recheck
Started with 140-second outer deadline.

- `main-recheck/dollars/bash`: historical comparator=MATCH, status=0, 0.791s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `main-recheck/dollars/main`: historical comparator=MATCH, status=0, 25.324s, timeout=False, captures=1, cache entries=44, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `main-recheck/quote/bash`: historical comparator=MATCH, status=1, 0.218s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `main-recheck/quote/main`: historical comparator=MATCH, status=1, 7.623s, timeout=False, captures=1, cache entries=15, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `main-recheck/execscript/bash`: historical comparator=MATCH, status=1, 0.540s, timeout=False, captures=1, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

## Raw differences and locale follow-up
Full audit: 68 exact output matches, 13 additional location/PID-only matches, glob-test has a duplicate missing-locale startup warning, and type exposes the instrumented function body. The historical comparator strips Incr prefixes globally and hides the type discrepancy. Treat function-body introspection as an observable compatibility limitation, not merely a line-number change. No runtime patch is being applied in this evaluation. First private-locale rerun gives exact native/Observe output for glob-test and intl, but intl exposes a further missing German locale. Generated de_DE.UTF-8 successfully for a final locale-complete recheck.

- `main-recheck/execscript/main`: historical comparator=DIFF, status=1, 9.015s, timeout=False, captures=1, cache entries=11, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

Completed main-recheck: status=1, elapsed=45.088s, timeout=False, cleanup=False, remaining=[].

## Follow-up: regressions-live
Started with 45-second outer deadline.

Completed regressions-live: status=0, elapsed=8.614s, timeout=False, cleanup=False, remaining=[].

## Follow-up: regressions-final
Started with 45-second outer deadline.

Completed regressions-final: status=0, elapsed=8.975s, timeout=False, cleanup=False, remaining=[].

- Minimal type/bash: status 0, 0.003s, timeout=False, remaining=[].

- Minimal type/observe: status 0, 0.141s, timeout=False, remaining=[].

- Minimal type/main: status 0, 0.142s, timeout=False, remaining=[].

- Minimal declare/bash: status 0, 0.003s, timeout=False, remaining=[].

- Minimal declare/observe: status 0, 0.141s, timeout=False, remaining=[].

- Minimal declare/main: status 0, 0.120s, timeout=False, remaining=[].

- `locales-complete/glob-test/bash`: historical comparator=MATCH, status=0, 0.409s, timeout=False, captures=2, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

## User clarification: trivial differences
The user explicitly requested ignoring trivial executable differences, PIDs and similar presentation changes. Accordingly, the type function-body diff is classified as an executable/wrapper-prefix presentation difference for this evaluation, not a failed Bash group. Its raw diff and tiny reproductions remain available; behavior that actually depends on exact printed function source is outside this normalization contract. Only verified diagnostic/function-display prefixes are ignored, not arbitrary changed command results.

Main recheck completed: dollars matches in 25.32 seconds (the earlier 15-second smoke cutoff was too short, not proof of a hang); quote matches; execscript retains real missing-command status/BASH_ENV/argv0 differences. Both live and final streaming regression suites passed all 57 tests in 8.61 and 8.97 seconds respectively, without timeouts, cleanup needs or survivors.

- `locales-complete/glob-test/observe`: historical comparator=MATCH, status=0, 2.430s, timeout=False, captures=2, cache entries=13, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `locales-complete/intl/bash`: historical comparator=MATCH, status=0, 0.437s, timeout=False, captures=2, cache entries=0, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

- `locales-complete/intl/observe`: historical comparator=MATCH, status=0, 1.427s, timeout=False, captures=2, cache entries=2, cleanup needed=False, remaining=[]. Raw output retained for stricter audit.

## Final assessment
Persistent goal created at the user’s explicit request. The locale-complete rerun finished in 5.74 seconds: glob-test and intl are byte-exact, all four statuses zero, no timeout or survivors. Independent finalization checks all 83 case names, all capture counts, unchanged expected operands, matching cleanup requirements, narrow trivia normalization, and both 57-test regression results. Result: 83/83 normalized matches, 68 byte-exact, 81 location/PID-normalized, no substantive Observe mismatch. There are 87 captures per mode and 349 cache entries across 31 Observe groups. All nine differing driver statuses are literal diff results for reviewed trivial changes. REPORT.md, final-results.json, and case-results.csv preserve the complete conclusion and limits. No further runtime testing is needed for the stated evaluation; final provenance and owned-artifact cleanup remain.

## Completed
Final provenance checks pass: all three repository revisions and all four recorded binary hashes are unchanged; frozen Incr and Observe snapshot binaries match the recorded release binaries. Incr has only this untracked audit directory; Observe and the main worktree are clean. Final cleanup found no active owned processes or parent-namespace mounts. Removed owned test fixtures, private generated locales, audit bytecode, and one generated shell_ast bytecode file discovered by the cleanliness check. All raw evidence and reproduction scripts are retained. The persistent goal is complete: full Bash suite, focused correctness evaluation, main comparison, design/log review, progress log, and final report are delivered.

## Follow-up: scope of “all tests”
Rechecked the run-all enumeration against saved records: all 83 runnable groups are present, with no omitted group. The corpus contains 84 expected .right files totaling 12,234 lines; the initial captured native transcripts total 12,548 lines including diff capability probes. Neither figure is an assertion count: scripts contain loops, silent checks, multiline results, and conditionals. No reliable “10,000 individual tests passed” count is supplied by this harness. After substituting the locale-complete reruns, 15 native drivers still differ from literal expected files. Some differences are environment/terminal diagnostics; others are missing expected output or parser diagnostic differences shared by native and Observe. In particular read/test/vredir encountered /dev/tty errors without a controlling terminal, so those terminal-specific paths are not established by the full sweep. The focused Incr terminal regression is separate and does not establish those Bash cases. Thus the supported conclusion remains complete group-level differential parity, not unconditional passage of every upstream assertion. See coverage-check.json.

## Paper-aligned follow-up
Moved the complete audit directory into incr/studies at user request. Historical JSON commands/hashes are preserved as evidence of original execution paths; Python harness roots are adjusted to the new location. Starting case-by-case review against the OSDI 2026 paper correctness methodology, including group coverage, individual-case accounting, terminal gaps, and cold/warm behavior.

- Private locale `zh_HK.big5hkscs` generation: status 0, generated=True, timeout=False; no host locale changes.

- Private locale `fr_FR.ISO8859-1` generation: status 0, generated=True, timeout=False; no host locale changes.

- Private locale `ja_JP.SJIS` generation: status 1, generated=True, timeout=False; no host locale changes.

- Private locale `zh_TW.BIG5` generation: status 0, generated=True, timeout=False; no host locale changes.

- Private locale `de_DE.UTF-8` generation: status 0, generated=True, timeout=False; no host locale changes.

- `upstream-smoke/alias/bash/cold`: historical comparator=MATCH, status=0, 0.133s, timeout=False, captures=1, cache entries=0, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `upstream-smoke/alias/bash/warm`: historical comparator=MATCH, status=0, 0.155s, timeout=False, captures=1, cache entries=0, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `upstream-smoke/alias/observe/cold`: historical comparator=MATCH, status=0, 1.137s, timeout=False, captures=1, cache entries=0, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `upstream-smoke/alias/observe/warm`: historical comparator=MATCH, status=0, 1.262s, timeout=False, captures=1, cache entries=0, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `upstream-smoke/execscript/bash/cold`: historical comparator=MATCH, status=1, 0.514s, timeout=False, captures=1, cache entries=0, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `upstream-smoke/execscript/bash/warm`: historical comparator=MATCH, status=1, 0.529s, timeout=False, captures=1, cache entries=0, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `upstream-smoke/execscript/observe/cold`: historical comparator=MATCH, status=1, 3.463s, timeout=False, captures=1, cache entries=1, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `upstream-smoke/execscript/observe/warm`: historical comparator=MATCH, status=1, 3.141s, timeout=False, captures=1, cache entries=1, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `upstream-smoke/read/bash/cold`: historical comparator=MATCH, status=0, 8.422s, timeout=False, captures=1, cache entries=0, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `upstream-smoke/read/bash/warm`: historical comparator=MATCH, status=0, 8.409s, timeout=False, captures=1, cache entries=0, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `upstream-smoke/read/observe/cold`: historical comparator=MATCH, status=1, 9.677s, timeout=False, captures=1, cache entries=1, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `upstream-smoke/read/observe/warm`: historical comparator=MATCH, status=1, 9.854s, timeout=False, captures=1, cache entries=1, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `upstream-smoke/test/bash/cold`: historical comparator=MATCH, status=0, 3.196s, timeout=False, captures=1, cache entries=0, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `upstream-smoke/test/bash/warm`: historical comparator=MATCH, status=0, 3.166s, timeout=False, captures=1, cache entries=0, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `upstream-smoke/test/observe/cold`: historical comparator=MATCH, status=1, 3.628s, timeout=False, captures=1, cache entries=0, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `upstream-smoke/test/observe/warm`: historical comparator=MATCH, status=1, 3.778s, timeout=False, captures=1, cache entries=0, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `upstream-smoke/vredir/bash/cold`: historical comparator=MATCH, status=0, 0.130s, timeout=False, captures=1, cache entries=0, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `upstream-smoke/vredir/bash/warm`: historical comparator=MATCH, status=0, 0.131s, timeout=False, captures=1, cache entries=0, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `upstream-smoke/vredir/observe/cold`: historical comparator=MATCH, status=1, 1.531s, timeout=False, captures=1, cache entries=3, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

- `upstream-smoke/vredir/observe/warm`: historical comparator=MATCH, status=1, 1.632s, timeout=False, captures=1, cache entries=6, cleanup needed=True, remaining=[]. Raw output retained for stricter audit.

## Upstream verification and final runner
Downloaded official GNU bash-5.2.37.tar.gz over HTTPS and verified every one of its 668 test-tree files against the existing build source: zero differences. Saved release SHA256 and per-file hashes in corpus-provenance.json. Vendored top-level tests differ in 16 files, including disabled PATH and parser cases; vendored-changes.diff records the changes. Upstream smoke covers alias, execscript, read, test, and vredir with native/Observe cold/warm runs and a controlling terminal: all normalized outputs match. Native read now passes its expected transcript. The maintained runner is being verified separately, with invocation logging, excluded diff self-probes, untouched official sources, narrow normalization, retained caches, private locales, and automatic scratch cleanup.

## Study cleanup
Consolidated the initial vendored-suite/main/locale/regression JSON evidence into results/prior-evaluation.json.gz. Removed exploratory scripts, duplicate diffs/logs, intermediate smoke result directories, private locale copies, and disposable fixtures. Maintained harness files now live only in harness/, with run.sh as the entry point. Current upstream run and its temporary directory are untouched.

## Corrected terminal-helper signal inheritance
The first maintained-runner sweep reached 45 groups; detailed audit found variable histexpand broken-pipe diagnostics and extra SIGPIPE/SIGXFSZ traps in execscript. Python ignores these signals and os.execvp preserves that state, unlike subprocess.Popen's default restore_signals behavior. Corrected terminal.py to restore SIGPIPE/SIGXFZ/SIGXFSZ defaults before exec. Interrupted the owned runner with SIGINT so bounded.run performs its normal child cleanup before temporary fixture removal. Restarting the full sweep from scratch; partial pre-fix results cannot support the final score. The earlier progress message claiming 45 matches was premature: 44 of the completed groups matched and histexpand differed due to this harness issue.

## Published denominator reproduced
Inspected the paper's Zenodo artifact (71 MB streamed under a 60-second deadline; finished in 30.14 seconds). categories.py constructs <category>.right and skips nonexistent names. Eight groups use different actual expected filenames, accounting for nine omitted files and 1,952 lines. The script's category totals exactly reproduce the published 10,282 denominator (12,234 complete lines minus 1,952 omitted). Saved mapping/counts and the script SHA256 in paper-accounting.json. No artifact code was executed. Archived expected-file line counts match the official source, though rsh.right differs in bytes. Final evaluation continues to use the checksum-verified official suite, including all omitted transcripts. This resolves the previously stated denominator limitation.

## Final upstream result
Maintained runner exited 0 after 783.25 seconds. All 83 groups match both cold and warm, with 12,234/12,234 transcript lines per phase. The artifact-counted subset independently reproduces 10,282/10,282 matching lines per phase and all ten category denominators. There are 70 byte-exact groups and 13 presentation-only groups in each phase; no cold/warm variation. All 24,468 ledger rows have equal normalized hashes. Captures are complete (84 per phase per implementation). Cache entries: 332 cold, 361 warm; 331 cold metadata files remain unchanged across 30 warm groups. No timeouts, surviving descendants, locale-skip warnings, or /dev/tty availability errors. Both 57-test regression suites pass, and all 14 harness checks pass. Only native core-limit output and signal-trap ordering differ from literal expected files. CASE_ANALYSIS.md documents all 83 groups. Final cleanup, repository review, commit and push remain.

## Final review and cleanup
Added two fail-closed comparator guards: identical abnormal driver exits cannot pass, and unexplained extra driver stdout cannot be ignored. All 16 harness checks pass; reanalysis of every full-run record under these guards still gives 83/83 and 12,234/12,234 in both phases. Execution behavior did not change, so the complete raw run remains valid. Removed all study scratch directories, exploratory signal-check output, duplicate console files, temporary formatter installs, and generated bytecode. Final process/mount check finds no active study process or mount. Saved final verification/harness hashes. Runtime source diff is empty. Ready for staged review and the explicitly requested commit/push.

Final lifecycle review distinguishes cleanup flags from survivors: all runs had terminal/sudo adopted descendants; retained diagnostics show 8,408 zombies and 24 sleeping processes. Live background processes occurred only in assoc/redir, with identical native/Observe state/name counts. All were cleaned. Added lifecycle-analysis.json and report explanation. Staged whitespace review identified CSV CRLF endings; normalized generated CSV to LF and updated the writer, preserving all data. Raw upstream diffs intentionally preserve whitespace via study-local attributes.

Extended the final lifecycle guard so baseline zombie cleanup cannot mask extra live Observe descendants. Added positive/negative checks for intentional versus unexpected background children. All 18 harness tests pass and all 332 full-run records pass independent reanalysis with the stronger guard; output/line scores are unchanged. No further runtime tests are needed after these comparison-only checks.
