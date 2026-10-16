# Synthetic strengths results

**Cache-presence warning diagnosed:** artifact installation performs extended-attribute operations that Observe traces but cannot cache for replay. A separate same-binary Observe diagnostic reproduced that barrier, and the earlier same-binary installation pilot verified dynamic Observe backend coverage. See instrumentation-review.json. The original cache-presence audit remains false; all raw-output, native-reference and coverage checks passed. Do not interpret this case as evidence of replay reuse.

Median complete development episode seconds (six phases), with three independent paired repetitions. Cold, unchanged and edited phases are also retained separately. This is a deliberately synthetic strengths study, not a representative application sample.

| Scenario | Scale | Bash | Original Incr | Observe | Original / Observe |
|---|---|---:|---:|---:|---:|
| builtin-control | small | 0.303 | 0.296 | 0.293 | 1.01× |
| builtin-control | medium | 1.694 | 1.743 | 1.733 | 1.01× |
| builtin-control | large | 6.507 | 6.669 | 6.705 | 0.99× |
| compute-control | small | 0.758 | 3.087 | 0.769 | 4.01× |
| compute-control | medium | 3.630 | 5.630 | 3.302 | 1.70× |
| compute-control | large | 16.368 | 16.093 | 13.597 | 1.18× |
| dummy-straightline | small | 0.083 | 8.924 | 0.189 | 47.34× |
| dummy-straightline | medium | 0.280 | 53.909 | 1.071 | 50.33× |
| dummy-straightline | large | 1.093 | 287.368 | 6.968 | 41.24× |
| dummy-loop | small | 0.063 | 4.799 | 0.157 | 30.48× |
| dummy-loop | medium | 0.571 | 62.547 | 2.145 | 29.15× |
| dummy-loop | large | 2.556 | 247.748 | 8.992 | 27.55× |
| checksums | small | 0.097 | 1.922 | 0.198 | 9.72× |
| checksums | medium | 0.439 | 11.517 | 0.945 | 12.19× |
| checksums | large | 2.631 | 62.048 | 5.924 | 10.47× |
| text-summaries | small | 0.102 | 3.845 | 0.279 | 13.78× |
| text-summaries | medium | 0.497 | 23.084 | 1.714 | 13.46× |
| text-summaries | large | 3.173 | 124.515 | 9.679 | 12.86× |
| directory-inventory | small | 0.089 | 4.972 | 0.166 | 29.93× |
| directory-inventory | medium | 0.406 | 24.259 | 0.853 | 28.45× |
| directory-inventory | large | 2.193 | 125.536 | 5.207 | 24.11× |
| artifact-generation | small | 0.082 | 8.811 | 0.270 | 32.66× |
| artifact-generation | medium | 0.354 | 48.931 | 1.778 | 27.52× |
| artifact-generation | large | 1.957 | 255.788 | 10.402 | 24.59× |
| redirected-transform | small | 0.068 | 0.589 | 0.220 | 2.68× |
| redirected-transform | medium | 0.249 | 1.288 | 1.353 | 0.95× |
| redirected-transform | large | 1.416 | 6.327 | 8.257 | 0.77× |
| staged-artifacts | small | 0.212 | 24.144 | 0.899 | 26.85× |
| staged-artifacts | medium | 0.792 | 86.117 | 4.081 | 21.10× |
| staged-artifacts | large | 3.301 | 333.519 | 17.144 | 19.45× |
| partitioned-logs | small | 0.091 | 2.675 | 0.269 | 9.96× |
| partitioned-logs | medium | 0.408 | 12.425 | 1.657 | 7.50× |
| partitioned-logs | large | 2.507 | 66.443 | 10.406 | 6.38× |
| parameter-sweep | small | 0.200 | 7.593 | 0.533 | 14.26× |
| parameter-sweep | medium | 1.151 | 46.807 | 3.508 | 13.34× |
| parameter-sweep | large | 7.134 | 247.762 | 19.609 | 12.64× |
| growing-manifest | small | 0.076 | 3.087 | 0.196 | 15.74× |
| growing-manifest | medium | 0.314 | 13.448 | 0.825 | 16.31× |
| growing-manifest | large | 1.790 | 68.623 | 5.001 | 13.72× |
| localized-script-edit | small | 0.082 | 1.229 | 0.221 | 5.57× |
| localized-script-edit | medium | 0.298 | 2.118 | 1.502 | 1.41× |
| localized-script-edit | large | 1.980 | 8.089 | 9.855 | 0.82× |
| shared-dependency | small | 0.074 | 2.077 | 0.213 | 9.75× |
| shared-dependency | medium | 0.282 | 11.646 | 1.362 | 8.55× |
| shared-dependency | large | 2.148 | 63.179 | 8.451 | 7.48× |
| streaming-stages | small | 0.087 | 2.361 | 0.231 | 10.24× |
| streaming-stages | medium | 0.356 | 12.198 | 1.581 | 7.71× |
| streaming-stages | large | 2.319 | 64.625 | 10.664 | 6.06× |
| build-graph | small | 0.143 | 3.350 | 0.457 | 7.33× |
| build-graph | medium | 0.445 | 7.231 | 1.976 | 3.66× |
| build-graph | large | 2.036 | 12.591 | 9.128 | 1.38× |

All samples passed native stdout/stderr/status and filesystem validation. Ratios of medians and individual paired ratios are descriptive; three repetitions do not establish significance for small differences. Bash-only loops and CPU-heavy work are controls. Dummy commands are explicit overhead stresses. An episode advantage does not imply every unchanged or edited phase wins.

Resource fields are GNU time user seconds, system seconds, maximum-process RSS KiB, filesystem input/output blocks, voluntary and involuntary context switches. Cache activity witnesses count new/rewritten/retained metadata entries, not exact logical hit rates.
