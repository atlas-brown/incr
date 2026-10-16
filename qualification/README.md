# Maintained correctness checks

All historical qualification measurements/reports are consolidated in [studies/evaluation-checkpoint-2026-10-16](../studies/evaluation-checkpoint-2026-10-16/README.md). This directory retains current regression/component tests and their bounded process supervisor. Scratch/results are generated explicitly and ignored; installed parser/ML dependencies are in `.venv`, official Bash and Node programs in `.tools`.

Build both Rust repositories, then run serially:

```bash
python3 qualification/regressions.py
python3 qualification/chunk_tests.py
python3 qualification/inherited_fd_tests.py
python3 qualification/native_transform_tests.py
python3 qualification/shell_ast_tests.py
python3 qualification/benchmark_tests.py
bash agents/test_incr_observe.sh
```

`bounded.py` supervises arbitrary validation commands with deadlines and process-tree cleanup. `fast_matrix.py` runs supported policy/configuration checks; inspect its help before execution. For full Bash use [the Bash runner](../studies/bash-parity-audit-2026-10-08/README.md). For all minimum and full workloads use [the single benchmark harness](../studies/paper-size-benchmarks/README.md), replacing the retired duplicate minimum driver. The installed Bash/Node/Python runtimes and versioned minimum seed fixtures are required programs/test inputs, not stale run artifacts. No tests run automatically.
