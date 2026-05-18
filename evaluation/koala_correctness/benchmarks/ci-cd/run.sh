#!/bin/bash
# ci-cd/makeself: every makeself test script defines helper functions and then
# calls them as bare top-level commands (e.g. `testDefault`, `testNocomp`,
# `testCurrentDate`). incr's executor wraps those call sites and attempts to
# exec the function name as an external binary, which always fails (limitation
# #1 – shell functions can't be exec'd). No straightforward patch exists
# because the pattern is pervasive across all 11 test scripts.
# ci-cd/xz-clang requires clang, which is not installed.
source "$(dirname "${BASH_SOURCE[0]}")/../../lib.sh"
kc_run_benchmark \
    --name ci-cd \
    --size "$KC_SIZE" \
    --skip-reason "incr: test scripts call shell functions as commands (makeself); clang required (xz-clang)"
