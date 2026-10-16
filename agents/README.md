# Shell integration tests

Run `bash agents/test_incr_observe.sh` after building both repositories. `tests/` covers cache invalidation, streaming, batch execution, filesystem effects, stderr/exit status and fallback behavior. Tests use owned temporary fixtures and explicit options.

Current additional tests are in [qualification](../qualification/README.md); measurements are in [studies](../studies/README.md). Earlier microbenchmark launchers and duplicate design notes have been removed.
