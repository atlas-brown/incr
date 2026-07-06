# incr

Bolt-on incremental execution for the shell. Incr wraps shell commands to track their file dependencies and memoize their results, so that unchanged commands are skipped on re-execution and their outputs are replayed from cache.

## Setup

The default path is Docker. Clone the repo, then run Incr through the top-level `incr` wrapper:

```sh
git clone https://github.com/atlas-brown/incr
cd incr
chmod +x ./incr
sudo install -m 755 ./incr /usr/local/bin/incr
incr ./evaluation/hello-world.sh
```

The first run builds a local Docker image named `incr`. Later runs reuse that image and keep the incrementalization cache in `./.incr-cache` in whatever directory you launch `incr` from.

If you prefer native setup on Ubuntu 22.04, use [up.sh](./up.sh) or install the dependencies manually. The native path remains Ubuntu-specific because it relies on `strace`, `mergerfs`, Rust, Python packages, and privileged cleanup behavior.

See [INSTRUCTIONS.md](./INSTRUCTIONS.md) for full evaluation instructions.

### Docker

```sh
docker build -t incr .
docker run -it --rm --privileged incr
```

Toggle `DEBUG` and `DEBUG_LOGS` in `src/config.rs` for debug output.

## Quick Start

To sanity-check the install with a minimal example:

```sh
incr ./evaluation/hello-world.sh
```

This should print the same `Hello, world!`-style output as the underlying shell script, while exercising the Docker-backed `incr` entrypoint.

## Benchmarks

See [INSTRUCTIONS.md](./INSTRUCTIONS.md) for full benchmark setup and the behavioral-equivalence harness.

## Citing Incr

If you use Incr or build on any component in this repository, please cite the following paper:

```bibtex
@inproceedings{incr:osdi:2026,
  title = {Incr: Faster Re-execution via Bolt-on Incrementalization},
  author = {Xie, Yizheng and Lamprou, Evangelos and Xia, Jerry and Vasilakis, Nikos},
  booktitle = {20th USENIX Symposium on Operating Systems Design and Implementation (OSDI 26)},
  year = {2026},
  publisher = {USENIX Association},
  tags = {performance}
}
```

## License & Contributing

Incr is an open-source, collaborative, [MIT-licensed](./LICENSE) project developed by the [ATLAS group](https://atlas.cs.brown.edu/) at [Brown University](https://cs.brown.edu/). If you'd like to contribute, please see [CONTRIBUTING.md](./CONTRIBUTING.md) — contributions, bug reports, and reproducibility feedback are welcome.
