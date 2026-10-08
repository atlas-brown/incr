# Minimum-input benchmark measurements

**Complete candidate qualification**

2144/2144 scheduled measurements; 96/96 benchmark entrypoints.

Image annotation is excluded at the user’s request. Ordinary cases use three cold/warm pairs; DPT uses one pair with the real models and one image. DPT timings are single samples. Weather plotting uses one city-year; web search uses one real page. Other inputs use the supplied minimum.

| Mode | Valid measurements | Invalid measurements |
|---|---:|---:|
| bash | 536 | 0 |
| main | 385 | 151 |
| try | 536 | 0 |
| observe | 536 | 0 |

Speedup is reference time divided by Observe time. Values above 1 favor Observe. Geometric means use only cases with all scheduled samples valid in both modes; invalid main runs are excluded, never counted as fast results.

| Reference | Phase | Matched cases | Geometric mean speedup | Sum-of-medians speedup |
|---|---|---:|---:|---:|
| bash | cold | 96 | 0.138× | 0.811× |
| bash | warm | 96 | 0.182× | 0.826× |
| main | cold | 95 | 1.723× | 1.159× |
| main | warm | 28 | 0.990× | 1.004× |
| try | cold | 96 | 5.140× | 1.243× |
| try | warm | 96 | 1.813× | 1.079× |

Raw invocation JSON includes stdout/stderr hashes, return status, timeout and descendant cleanup evidence, filesystem effects and cache-entry counts. `aggregate-timings.csv` includes sample counts, medians and ranges. `aggregate-comparisons.json` includes per-family comparisons.

The filesystem comparison covers file content, modes, link targets/groups, empty directories and deletions. It does not claim timestamp/ownership identity. Encrypted/compressed archives are compared by decoded payload. Diagnostic timestamps and source locations are normalized narrowly. DPT uses eight OpenMP threads and two TensorFlow threads on this 16-CPU host. Matplotlib font caches are initialized once during fixture setup and copied identically to each mode. Cold means an empty Incr cache, not a flushed operating-system page cache. Warm runs restore the fixture in place while preserving unchanged input inode/ctime. Measurements run serially on a shared development machine; small timings include wrapper and parser startup overhead.

## Invalid measurements

- beginner/beginner-06.sh, main: 1 invalid measurement(s).
- beginner/beginner-13.sh, main: 3 invalid measurement(s).
- beginner/beginner-14.sh, main: 3 invalid measurement(s).
- bio/bio-1.sh, main: 3 invalid measurement(s).
- bio/bio-2.sh, main: 3 invalid measurement(s).
- bio/bio-3.sh, main: 3 invalid measurement(s).
- bio/bio-4-0.sh, main: 3 invalid measurement(s).
- bio/bio-4.sh, main: 3 invalid measurement(s).
- bio/bio-5.sh, main: 3 invalid measurement(s).
- bio/bio-6.sh, main: 3 invalid measurement(s).
- covid/1.sh, main: 3 invalid measurement(s).
- covid/2.sh, main: 3 invalid measurement(s).
- covid/3.sh, main: 3 invalid measurement(s).
- covid/4.sh, main: 3 invalid measurement(s).
- covid/5.sh, main: 1 invalid measurement(s).
- dpt/dpt_1.sh, main: 1 invalid measurement(s).
- dpt/dpt_2.sh, main: 1 invalid measurement(s).
- dpt/dpt_3a.sh, main: 1 invalid measurement(s).
- dpt/dpt_3b.sh, main: 1 invalid measurement(s).
- dpt/dpt_4.sh, main: 1 invalid measurement(s).
- dpt/dpt_5a.sh, main: 1 invalid measurement(s).
- dpt/dpt_5b.sh, main: 1 invalid measurement(s).
- dpt/dpt_5c.sh, main: 1 invalid measurement(s).
- dpt/dpt_5d.sh, main: 1 invalid measurement(s).
- dpt/dpt_5e.sh, main: 1 invalid measurement(s).
- file-mod/file-mod-1.sh, main: 3 invalid measurement(s).
- file-mod/file-mod-2.sh, main: 3 invalid measurement(s).
- file-mod/file-mod-3.sh, main: 3 invalid measurement(s).
- file-mod/file-mod-4.sh, main: 3 invalid measurement(s).
- file-mod/file-mod-5.sh, main: 3 invalid measurement(s).
- file-mod/file-mod-6.sh, main: 3 invalid measurement(s).
- file-mod/file-mod-7.sh, main: 3 invalid measurement(s).
- nginx-analysis/nginx-1.sh, main: 1 invalid measurement(s).
- nginx-analysis/nginx-10.sh, main: 2 invalid measurement(s).
- nginx-analysis/nginx-11.sh, main: 1 invalid measurement(s).
- nginx-analysis/nginx-14.sh, main: 2 invalid measurement(s).
- nginx-analysis/nginx-16.sh, main: 3 invalid measurement(s).
- nginx-analysis/nginx-17.sh, main: 3 invalid measurement(s).
- nginx-analysis/nginx-18.sh, main: 4 invalid measurement(s).
- nginx-analysis/nginx-19.sh, main: 3 invalid measurement(s).
- nginx-analysis/nginx-2.sh, main: 1 invalid measurement(s).
- nginx-analysis/nginx-20.sh, main: 3 invalid measurement(s).
- nginx-analysis/nginx-21.sh, main: 1 invalid measurement(s).
- nginx-analysis/nginx-22.sh, main: 2 invalid measurement(s).
- nginx-analysis/nginx-3.sh, main: 2 invalid measurement(s).
- nginx-analysis/nginx-4.sh, main: 1 invalid measurement(s).
- nlp-ngrams/ngrams-2.sh, main: 1 invalid measurement(s).
- nlp-ngrams/ngrams-3.sh, main: 3 invalid measurement(s).
- nlp-uppercase/uppercase_by_token.sh, main: 1 invalid measurement(s).
- nlp-uppercase/uppercase_by_type.sh, main: 3 invalid measurement(s).
- spell/spell-2.sh, main: 2 invalid measurement(s).
- spell/spell-3.sh, main: 3 invalid measurement(s).
- spell/spell-4.sh, main: 2 invalid measurement(s).
- spell/spell-5.sh, main: 1 invalid measurement(s).
- spell/spell-6.sh, main: 1 invalid measurement(s).
- spell/spell-7.sh, main: 2 invalid measurement(s).
- unixfun/12.sh, main: 3 invalid measurement(s).
- unixfun/7.sh, main: 3 invalid measurement(s).
- unixfun/8.sh, main: 3 invalid measurement(s).
- unixfun/9.sh, main: 3 invalid measurement(s).
- weather/temp-analytics-2.sh, main: 3 invalid measurement(s).
- weather/temp-analytics-3.sh, main: 1 invalid measurement(s).
- weather/tuft-weather-1.sh, main: 2 invalid measurement(s).
- weather/tuft-weather-2.sh, main: 1 invalid measurement(s).
- weather/tuft-weather-3.sh, main: 3 invalid measurement(s).
- web-search/engine.sh, main: 3 invalid measurement(s).
- word-freq/top-n.sh, main: 3 invalid measurement(s).
- word-freq/wf.sh, main: 3 invalid measurement(s).
