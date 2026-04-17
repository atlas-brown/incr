# Shared setup for incr + observe tests.
# Source from test files. Run from incr/.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INCR_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$INCR_ROOT"

INCR="./target/release/incr"
TRY="./src/scripts/try.sh"
OBSERVE="../observe/target/release/observe"
CACHE="/tmp/incr_test_cache_$$"
TESTDIR="/tmp/incr_test_dir_$$"
# /tmp reads are excluded from observe's dependency tracking (OBSERVE_READ_EXCLUDED_PATHS).
# Tests that need observe to track input file reads (e.g. cp invalidation) must put inputs
# under TESTDIR_OBS, which is outside /tmp.
TESTDIR_OBS="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/incr_test_obs_$$"

mkdir -p "$TESTDIR" "$TESTDIR_OBS"
trap "rm -rf $CACHE $TESTDIR $TESTDIR_OBS" EXIT

run_pipe() { local stdin="$1"; shift; echo "$stdin" | $INCR --try $TRY --cache $CACHE "$@"; }
run_pipe_obs() { local stdin="$1"; shift; echo "$stdin" | $INCR --try $TRY --cache $CACHE --observe $OBSERVE "$@"; }
run_empty() { echo "" | $INCR --try $TRY --cache $CACHE "$@"; }
run_empty_obs() { echo "" | $INCR --try $TRY --cache $CACHE --observe $OBSERVE "$@"; }
run_pipe_obs_s() { local stdin="$1"; shift; echo "$stdin" | $INCR -s --try $TRY --cache $CACHE --observe $OBSERVE "$@"; }
run_batch_obs() { local stdin="$1"; shift; echo "$stdin" | $INCR -b --try $TRY --cache $CACHE --observe $OBSERVE "$@"; }
