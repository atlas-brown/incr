# Overview  
The paper makes the following claims requiring artifact evaluation on page 2:  

1. **Fine-grained dependency tracking**: Incr introduces lightweight interposition probes that capture interactions across the filesystem, shell environment, and other external resources.
2. **Correct incrementalization via memoization**: Incr enables incrementalization by memoizing dependencies and effects, including both transient data streams and side effects, and safe reuse of prior effects.
3. **Runtime optimizations**: Incr introduces a series runtime optimizations, including eager stream processing, introspection, and compaction.
4. **Optional tuning interface**: Incr optionally accepts crowdsourced annotations and developer configurations to enhance, disable, or relax parts of incrementalization.

This artifact targets the following badges (mirroring [the OSDI26 artifact "evaluation process"](https://www.usenix.org/conference/osdi26/call-for-artifacts)):  

* [x] [Artifact available](#artifact-available): Reviewers are expected to confirm public availability of core components (~5mins) 

Additionally, we provide complete instructions to confirm that
* Incr is [functional](#artifact-functional): functional executables verified via a miniam "Hello world" example (~10mins).
* Results presented in the papers are [reproducible](#results-reproducible): Incr's efficient incrementalization of diverse shell programs, demonstrated by its performance compared to Bash (Fig.4, ~x hours).

**To "kick the tires" for this artifact:** (1) skim this file to understand the artifact structure (2 minutes), and (2) jump straight to the [exercisability](#exercisability) section to build Incr and run a minimal pipeline (5--10 minutes).

# Artifact Available (~5mins)
Confirm Incr is publicly available and that the repository already contains the main implementation and evaluation scaffolding. The final camera-ready artifact should point reviewers to:

1. **Primary repository:** `XXX`
2. **Archival DOI / Zenodo record:** `XXX`
3. **Paper PDF used by the AEC:** `XXX`
4. **External benchmark/data sources:** `XXX`

The current repository already includes:

1. the Incr implementation under [src](./src),
2. the top-level project overview in [README.md](./README.md),
3. the executable entrypoint [incr.sh](./incr.sh),
4. the benchmark drivers under [evaluation/benchmarks](./evaluation/benchmarks),
5. the Bash behavioral-equivalence harness under [evaluation/bash-ts](./evaluation/bash-ts), and
6. bundled examples such as [evaluation/war-and-peace](./evaluation/war-and-peace).

The final artifact should also provide stable links for benchmark inputs derived from Koala and for any external annotation sources used in the paper.

<a name="artifact-functional"></a>
# Artifact Functional (~10mins)

Confirm sufficient documentation, key components as described in the paper, and the system's exercisability.

**Documentation:** The repository already contains the core implementation and the main evaluation entry points:

* [src/main.rs](./src/main.rs): CLI entrypoint and execution-mode selection
* [src/config.rs](./src/config.rs): default paths, tracing mode, caching constants, and debug flags
* [src/execution](./src/execution): execution engines
* [src/cache](./src/cache): cache representation and persistence
* [src/annotation](./src/annotation): optional annotation support
* [src/scripts](./src/scripts): helper scripts for insertion/incrementization
* [evaluation/benchmarks/run.sh](./evaluation/benchmarks/run.sh): main benchmark driver
* [evaluation/bash-ts/run.sh](./evaluation/bash-ts/run.sh): Bash test-suite comparison harness
* [evaluation/analysis](./evaluation/analysis): plotting/statistics helpers

**Completeness:** The current paper claims correspond to the following repository elements:

1. fine-grained dependency tracking and memoization are implemented in the tracing/execution/cache path rooted at [src/main.rs](./src/main.rs), [src/execution](./src/execution), and [src/cache](./src/cache);
2. runtime optimizations such as streaming, batching, chunking, introspection, and compression are reflected by flags in [src/main.rs](./src/main.rs) and constants/configuration in [src/config.rs](./src/config.rs);
3. optional tuning through annotations and developer configuration is represented by [src/annotation](./src/annotation) together with the paper's `INCR="..."` examples (`XXX add the exact parser/config reference if we want this section to be more concrete`);
4. shell behavioral equivalence is exercised by the Bash test-suite harness in [evaluation/bash-ts/run.sh](./evaluation/bash-ts/run.sh).

<a name="exercisability"></a>
**Exercisability:** The shortest reviewer path is to build Incr and run a minimal pipeline.

Current environment assumptions:

* Linux close to Ubuntu 22.04
* Rust toolchain
* `python3` and `pip3`
* `strace`
* `bash`
* `mergerfs`
* `sudo` access for sandboxed execution paths used by some benchmarks

The current top-level setup notes in [README.md](./README.md) are:

For distro xxx:
```sh
sudo apt update
sudo apt upgrade
sudo apt install mergerfs
pip3 install --no-cache-dir -r requirements.txt
```

Build Incr from the repository root:

```sh
cargo build
cargo build --release
```

The repository also includes an optional Docker container enviroment via [Dockerfile](./Dockerfile):

```sh
docker build -t incr .
docker run -it --rm -v $(pwd):/app --privileged incr
```

To run a minimal example:

```sh
bash ./evaluation/war-and-peace/without_cache.sh > /tmp/incr-baseline.txt
bash ./evaluation/war-and-peace/with_cache.sh > /tmp/incr-output.txt
diff -u /tmp/incr-baseline.txt /tmp/incr-output.txt
```

The expected result is:

1. both scripts finish successfully,
2. both outputs match, and
3. Incr populates its cache directory (`XXX document this cleanly for reviewers`).

Reviewers can also invoke the binary directly:

```sh
./incr.sh \
  --try "$(pwd)/src/scripts/try.sh" \
  --cache "$(pwd)/cache" \
  cat ./evaluation/war-and-peace/book-small.txt
```

<a name="results-reproducible"></a>
# Results Reproducible (~x mins)

The paper's evaluation is broader than a single plot. Based on the current paper draft, the main reproducibility targets are:

1. **Re-execution performance**: Incr accelerates incremental re-execution across 14 scenarios totalling 81 deltas.
2. **Cold-start overhead**: Incr incurs overhead on the first run due to tracing, isolation, and memoization.
3. **Behavioral equivalence**: Incr closely matches Bash behavior on the Bash test suite and on the real-world benchmark scenarios.
4. **Runtime optimizations**: eager stream processing, introspection, and storage compaction improve practicality.
5. **Optional annotations**: crowdsourced annotations further improve re-execution speed and reduce cold-start overhead.

The paper draft currently describes experiments on a Cloudlab `m510` machine with 8 cores, 64GB RAM, 256GB NVMe, Ubuntu 22.04, and Linux 5.15. Before submission, we should either:

* provide a VM/container matching this setup, or
* explicitly state that reviewers may use a reasonably provisioned local Linux machine and should expect runtime variation.

**Terminology correspondence:** There are currently some naming mismatches between the paper and the repository:

* paper `dict` corresponds to repo `word-freq`
* paper `ngram` corresponds to repo `nlp-ngrams`
* paper `uppercase` corresponds to repo `nlp-uppercase`
* paper `unixgame` corresponds to repo `unixfun`
* paper `nginx` corresponds to repo `nginx-analysis`
* paper `image` corresponds to repo `image-annotation`
* paper `music` does not appear in the current top-level benchmark driver and may still need to be wired into the artifact

The current benchmark driver in [evaluation/benchmarks/run.sh](./evaluation/benchmarks/run.sh) enumerates:

* `beginner`
* `bio`
* `covid`
* `dpt`
* `file-mod`
* `image-annotation`
* `nginx-analysis`
* `nlp-uppercase`
* `nlp-ngrams`
* `poet`
* `spell`
* `unixfun`
* `weather`
* `word-freq`

## Re-execution performance

The main end-to-end result in the current paper draft is that Incr accelerates re-execution over Bash across the benchmark suite by memoizing unaffected work across deltas.

The current methodology in the paper is:

1. for each program modification, run the script under both Bash and Incr,
2. compute speedup as `bash runtime / incr runtime`,
3. repeat each re-execution 3 times, and
4. report averages over runs.

The paper draft currently reports, for the fully automatic configuration without annotations:

* 14 scenarios
* 81 deltas in the benchmark table
* 85 re-executions in the results text (`XXX reconcile this 81 vs. 85 count before submission`)
* average speedup `\gavg`
* maximum speedup `\gmax`

The repository-side rough entry point is:

```sh
cd evaluation/benchmarks
bash ./run.sh
```

The script currently:

1. cleans each benchmark,
2. runs its `execute.sh`,
3. copies timing results into `evaluation/run_results`, and
4. records cache size.

Current caveats:

* some benchmark directories or external data dependencies may still require separate setup,
* the script uses `sudo` and writes into `/tmp`,
* output-hash generation is still marked `TODO`, and
* the final paper-to-script correspondence has not yet been fully documented.

Once stabilized, this section should reproduce the main re-execution figure(s) from the paper (`XXX insert exact figure numbers after the draft settles`).

## Cold-start overhead

The paper separately evaluates the first-run overhead of enabling Incr before any incremental reuse occurs. This is the worst case for the system because tracing, isolation, and memoization are active but no reuse is possible yet.

The draft currently reports that, for benchmarks whose Incr execution exceeds five seconds:

* average overhead: `101.05%`
* maximum overhead: `732.45%`
* best case: `-48.46%` (that is, a speedup)

The current artifact does not yet have a polished single-command reproduction section for this result. However, the needed inputs appear to already exist in the paper repo under:

* `incr-paper/data/default/default_{1,2,3}/*-time.csv`

and the plotting/statistics logic appears in:

* [evaluation/analysis](./evaluation/analysis) in this repo, and
* `incr-paper/script/overhead.py` / `overhead-relative.py` in the paper repo (`XXX decide which scripts belong in the final public artifact bundle`).

## Behavioral equivalence

The paper's behavioral-equivalence section uses the Bash test suite together with the real-world benchmark scenarios.

The current paper draft claims:

* Bash version `5.2.37(1)-release`
* 83 test categories
* 534 test files
* 10,282 ground-truth output lines
* 99.9% equivalence (`10,279 / 10,282`)

The current harness is:

* [evaluation/bash-ts/run.sh](./evaluation/bash-ts/run.sh)

Rough flow:

```sh
cd evaluation/bash-ts
bash ./run.sh <test-name>
```

This generates paired result files such as:

* `results/<test>.results.bash`
* `results/<test>.results.incr`

The paper draft also notes two known divergence classes:

1. recursive `alias` definitions, and
2. one `execscript` case involving `PATH` being unset.

Before submission, this section should explicitly say:

* whether the Bash source tree is bundled or must be built locally,
* which revision is expected,
* whether we provide precomputed result files, and
* exactly how reviewers should compare outputs.

## Effects of runtime optimizations

The paper evaluates three runtime optimizations separately:

1. **Eager stream processing**
2. **Introspection**
3. **Storage compaction**

The current draft reports:

* eager stream processing reduces a synthetic pipeline's first execution from `9m 50s` to `3m 22s` and leaves reuse roughly unchanged,
* introspection reduces subsequent iterations of a 20-command synthetic pipeline from `35s` to `31s`,
* compaction reduces cache size by an average of `55.7%` with an average speedup degradation of `1.9%`.

The corresponding datasets already exist in `incr-paper/data`, including:

* `data/introspect/introspect_1`
* `data/compaction/compaction_1`
* `data/microbenchmark/eager`
* `data/microbenchmark/introspect`

The artifact still needs a cleaner reviewer-facing reproduction script for these results. For now, this section serves as a placeholder skeleton and should later point either to:

* scripts in this repository under [evaluation](./evaluation), or
* archived scripts moved in from `incr-paper/script`.

## Effects of optional annotations

The paper also evaluates the impact of optional crowdsourced annotations.

The current draft reports:

* additional average speedup of `1.46x` across all benchmarks,
* up to `24.40x` additional speedup in `music`,
* reduction of average cold-start overhead from `101.05%` to `43.55%`,
* reduction of worst-case overhead from `732.45%` to `278.15%`.

The corresponding archived data already appear to exist under:

* `incr-paper/data/annotation/annotation_1`
* `incr-paper/data/microbenchmark/chunk`
* `incr-paper/data/microbenchmark/argsplit`
* `incr-paper/data/microbenchmark/group`

The final artifact should explain:

1. how to enable annotations in the released binary,
2. which annotation corpus is shipped,
3. which benchmarks actually use them, and
4. how the synthetic chunking and argument-splitting experiments are invoked.

# Optional: Additional Experiments

The current paper draft suggests several results beyond the shortest reviewer path:

* full benchmark-suite re-execution performance with multiple runs,
* cold-start overhead analysis,
* Bash test-suite behavioral-equivalence checking,
* optimization-focused microbenchmarks, and
* optional annotation experiments.
