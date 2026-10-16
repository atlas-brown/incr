# Synthetic strengths results

Median complete development episode seconds (six phases), with three independent paired repetitions. Cold, unchanged and edited phases are also retained separately. This is a deliberately synthetic strengths study, not a representative application sample.

| Scenario | Scale | Bash | Original Incr | Observe | Original / Observe |
|---|---|---:|---:|---:|---:|
| checksums | medium | 0.470 | 11.345 | 0.951 | 11.93× |
| checksums | large | 2.762 | 62.616 | 5.756 | 10.88× |
| artifact-generation | medium | 0.265 | 1.285 | 1.215 | 1.06× |
| artifact-generation | large | 1.781 | 6.135 | 8.044 | 0.76× |
| streaming-stages | medium | 0.375 | 12.030 | 1.561 | 7.70× |
| streaming-stages | large | 2.238 | 65.184 | 10.741 | 6.07× |
| build-graph | medium | 0.457 | 6.952 | 1.928 | 3.61× |
| build-graph | large | 1.831 | 13.150 | 9.110 | 1.44× |

All samples passed native stdout/stderr/status and filesystem validation. Ratios of medians and individual paired ratios are descriptive; three repetitions do not establish significance for small differences. Bash-only loops and CPU-heavy work are controls. Dummy commands are explicit overhead stresses. An episode advantage does not imply every unchanged or edited phase wins.

Resource fields are GNU time user seconds, system seconds, maximum-process RSS KiB, filesystem input/output blocks, voluntary and involuntary context switches. Cache activity witnesses count new/rewritten/retained metadata entries, not exact logical hit rates.
