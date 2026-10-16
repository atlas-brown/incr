# Study paper-02

Suite: paper. Profile: paper.
Native shell transformation: enabled, with Python fallback.

Directory stat/access assumption: enabled; directory content reads remain tracked.

Static performance annotations: disabled in both implementations.

63/63 invocations; 63 valid. Complete: True.

| Reference | Valid paired edits | Arithmetic mean | Geometric mean | Maximum |
|---|---:|---:|---:|---:|
| bash | 6 | 64.231× | 64.206× | 66.552× |
| original | 6 | 3.219× | 3.183× | 3.624× |

Complete-sequence means (seconds); speedup is Bash time divided by mode time.

| Family | Bash | Original Incr | Observe | Bash / original | Bash / Observe |
|---|---:|---:|---:|---:|---:|
| image-annotation | 240.742 | 77.942 | 57.715 | 3.089× | 4.171× |

See timings.csv and invocation JSON for resources, hashes, output manifests, diagnostics, and cleanup evidence.
Identical successive source versions are retained as warm-repeat measurements and excluded from edit aggregates.
An incomplete study or failed sequence is never presented as a complete benchmark comparison.
