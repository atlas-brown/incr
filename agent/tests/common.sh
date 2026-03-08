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

mkdir -p "$TESTDIR"
trap "rm -rf $CACHE $TESTDIR" EXIT

run_pipe() { local stdin="$1"; shift; echo "$stdin" | $INCR --try $TRY --cache $CACHE "$@"; }
run_pipe_obs() { local stdin="$1"; shift; echo "$stdin" | $INCR --try $TRY --cache $CACHE --observe $OBSERVE "$@"; }
run_empty() { echo "" | $INCR --try $TRY --cache $CACHE "$@"; }
run_empty_obs() { echo "" | $INCR --try $TRY --cache $CACHE --observe $OBSERVE "$@"; }
run_pipe_obs_s() { local stdin="$1"; shift; echo "$stdin" | $INCR -s --try $TRY --cache $CACHE --observe $OBSERVE "$@"; }
run_batch_obs() { local stdin="$1"; shift; echo "$stdin" | $INCR -b --try $TRY --cache $CACHE --observe $OBSERVE "$@"; }
