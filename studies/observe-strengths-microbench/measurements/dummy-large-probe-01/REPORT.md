# Synthetic strengths results

Median complete development episode seconds (six phases), with three independent paired repetitions. Cold, unchanged and edited phases are also retained separately. This is a deliberately synthetic strengths study, not a representative application sample.

| Scenario | Scale | Bash | Original Incr | Observe | Original / Observe |
|---|---|---:|---:|---:|---:|
| dummy-loop | large | 2.350 | 248.925 | 8.732 | 28.51× |

All samples passed native stdout/stderr/status and filesystem validation. Ratios of medians and individual paired ratios are descriptive; three repetitions do not establish significance for small differences. Bash-only loops and CPU-heavy work are controls. Dummy commands are explicit overhead stresses. An episode advantage does not imply every unchanged or edited phase wins.

Resource fields are GNU time user seconds, system seconds, maximum-process RSS KiB, filesystem input/output blocks, voluntary and involuntary context switches. Cache activity witnesses count new/rewritten/retained metadata entries, not exact logical hit rates.
