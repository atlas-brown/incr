# Synthetic strengths results

Median complete development episode seconds (six phases), with three independent paired repetitions. Cold, unchanged and edited phases are also retained separately. This is a deliberately synthetic strengths study, not a representative application sample.

| Scenario | Scale | Bash | Original Incr | Observe | Original / Observe |
|---|---|---:|---:|---:|---:|
| builtin-control | small | 0.530 | 0.289 | 0.289 | 1.00× |
| builtin-control | medium | 1.733 | 1.615 | 1.615 | 1.00× |
| builtin-control | large | 6.483 | 6.431 | 6.544 | 0.98× |
| compute-control | small | 0.789 | 3.279 | 0.765 | 4.29× |
| compute-control | medium | 3.561 | 5.702 | 3.280 | 1.74× |
| compute-control | large | 15.881 | 16.133 | 13.598 | 1.19× |
| dummy-straightline | small | 0.082 | 9.074 | 0.211 | 42.95× |
| dummy-straightline | medium | 0.312 | 54.857 | 1.298 | 42.25× |
| dummy-straightline | large | 1.344 | 292.136 | 6.970 | 41.91× |
| dummy-loop | small | 0.065 | 5.011 | 0.160 | 31.26× |
| dummy-loop | medium | 0.666 | 63.651 | 2.382 | 26.72× |
| dummy-loop | large | 2.789 | 252.584 | 9.310 | 27.13× |
| checksums | small | 0.107 | 1.974 | 0.182 | 10.85× |
| checksums | medium | 0.489 | 11.881 | 1.054 | 11.27× |
| checksums | large | 2.842 | 63.299 | 6.036 | 10.49× |
| text-summaries | small | 0.118 | 4.012 | 0.327 | 12.26× |
| text-summaries | medium | 0.643 | 23.492 | 1.869 | 12.57× |
| text-summaries | large | 3.497 | 126.474 | 10.146 | 12.47× |
| directory-inventory | small | 0.103 | 4.986 | 0.171 | 29.22× |
| directory-inventory | medium | 0.449 | 25.041 | 0.970 | 25.82× |
| directory-inventory | large | 2.297 | 127.798 | 5.585 | 22.88× |
| artifact-generation | small | 0.083 | 8.531 | 0.284 | 30.09× |
| artifact-generation | medium | 0.360 | 46.935 | 1.852 | 25.34× |
| artifact-generation | large | 2.075 | 245.212 | 10.583 | 23.17× |
| redirected-transform | small | 0.066 | 0.628 | 0.172 | 3.65× |
| redirected-transform | medium | 0.309 | 1.519 | 1.061 | 1.43× |
| redirected-transform | large | 1.714 | 6.353 | 6.445 | 0.99× |
| staged-artifacts | small | 0.203 | 23.055 | 0.909 | 25.35× |
| staged-artifacts | medium | 0.914 | 81.290 | 3.684 | 22.06× |
| staged-artifacts | large | 3.582 | 314.836 | 15.788 | 19.94× |
| partitioned-logs | small | 0.105 | 2.796 | 0.264 | 10.58× |
| partitioned-logs | medium | 0.452 | 13.054 | 1.373 | 9.51× |
| partitioned-logs | large | 2.512 | 66.569 | 8.450 | 7.88× |
| parameter-sweep | small | 0.243 | 7.949 | 0.605 | 13.13× |
| parameter-sweep | medium | 1.239 | 47.077 | 3.707 | 12.70× |
| parameter-sweep | large | 7.124 | 253.449 | 20.800 | 12.18× |
| growing-manifest | small | 0.089 | 3.206 | 0.219 | 14.62× |
| growing-manifest | medium | 0.294 | 14.190 | 0.903 | 15.72× |
| growing-manifest | large | 1.727 | 69.621 | 5.454 | 12.77× |
| localized-script-edit | small | 0.086 | 1.182 | 0.197 | 5.99× |
| localized-script-edit | medium | 0.368 | 2.055 | 1.156 | 1.78× |
| localized-script-edit | large | 2.255 | 7.555 | 7.004 | 1.08× |
| shared-dependency | small | 0.091 | 2.077 | 0.194 | 10.69× |
| shared-dependency | medium | 0.349 | 11.836 | 1.192 | 9.93× |
| shared-dependency | large | 2.394 | 63.343 | 7.112 | 8.91× |
| streaming-stages | small | 0.076 | 2.365 | 0.230 | 10.28× |
| streaming-stages | medium | 0.402 | 11.989 | 1.340 | 8.94× |
| streaming-stages | large | 2.432 | 64.787 | 8.284 | 7.82× |
| build-graph | small | 0.137 | 3.261 | 0.427 | 7.63× |
| build-graph | medium | 0.517 | 7.257 | 1.710 | 4.24× |
| build-graph | large | 1.921 | 13.049 | 7.224 | 1.81× |

All samples passed native stdout/stderr/status and filesystem validation. Ratios of medians and individual paired ratios are descriptive; three repetitions do not establish significance for small differences. Bash-only loops and CPU-heavy work are controls. Dummy commands are explicit overhead stresses. An episode advantage does not imply every unchanged or edited phase wins.

Resource fields are GNU time user seconds, system seconds, maximum-process RSS KiB, filesystem input/output blocks, voluntary and involuntary context switches. Cache activity witnesses count new/rewritten/retained metadata entries, not exact logical hit rates.

Zero-cache samples remain uncached execution measurements. A separate same-binary, same-policy diagnostic verifies backend coverage; cache counts do not prove reuse.
