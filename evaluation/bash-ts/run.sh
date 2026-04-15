#!/bin/bash
set -e

cd "$(dirname "$0")" || exit 1

bash_git_url="https://git.savannah.gnu.org/git/bash.git"
bash_git_ref="c5c97b3"

if [ ! -d bash/.git ]; then
  if [ -e bash ]; then
    echo "error: ./bash exists but is not a git checkout" >&2
    exit 1
  fi
  git clone "$bash_git_url" bash
fi

if ! git -C bash rev-parse --verify "${bash_git_ref}^{commit}" >/dev/null 2>&1; then
  git -C bash fetch --tags origin
fi

bash_git_commit="$(git -C bash rev-parse "${bash_git_ref}^{commit}")"

# The vendored bash checkout is a disposable build tree. Reset it before
# pinning the requested commit so previous configure/build output can't block
# the checkout.
git -C bash reset --hard
git -C bash clean -fdx
git -C bash checkout --detach "$bash_git_commit"

bash_build_dir="$PWD/bash"
results_dir="$PWD/results"
test_timeout_secs="${INCR_BASH_TEST_TIMEOUT_SECS:-60}"
incr_this_sh="/tmp/bash"
filter_diff_script="$PWD/filter_diff_noise.py"

# The vendored bash tree may contain stale objects from a different host build.
# Scrub build artifacts before reconfiguring so the in-repo build stays usable.
if [ -f "$bash_build_dir/Makefile" ]; then
  make -C "$bash_build_dir" distclean >/dev/null 2>&1 || true
fi
find "$bash_build_dir" \
  \( -name '*.o' -o -name '*.a' -o -name '*.so' -o -name '*.dylib' \) -delete
rm -f \
  "$bash_build_dir/bash" \
  "$bash_build_dir/bashversion" \
  "$bash_build_dir/recho" \
  "$bash_build_dir/zecho" \
  "$bash_build_dir/printenv" \
  "$bash_build_dir/xcase"

( cd "$bash_build_dir" && CC=cc ./configure)
make -C "$bash_build_dir" -j4
make -C "$bash_build_dir" recho zecho printenv xcase -j4

rm -rf /tmp/cache /tmp/incr_cache /tmp/tstout
rm -f results.*
mkdir -p "$results_dir"
rm -f "$results_dir"/*.results.bash "$results_dir"/*.results.incr
top=$(git rev-parse --show-toplevel)
export PATH="$PATH:$bash_build_dir"
export TMPDIR=/tmp
export BASH_TSTOUT=/tmp/tstout
export BUILD_DIR="$bash_build_dir"

cd tests || exit 1

run_capture() {
  result_file="$1"
  label="$2"
  shift 2

  stdout_file=$(mktemp)
  stderr_file=$(mktemp)
  timeout_marker=$(mktemp)
  rm -f "$timeout_marker"

  if command -v setsid >/dev/null 2>&1; then
    set +e
    setsid "$@" >"$stdout_file" 2>"$stderr_file" &
    cmd_pid=$!

    (
      sleep "$test_timeout_secs"
      : >"$timeout_marker"
      kill -TERM "-$cmd_pid" 2>/dev/null || exit 0
      sleep 5
      kill -KILL "-$cmd_pid" 2>/dev/null || true
    ) &
    watchdog_pid=$!

    wait "$cmd_pid"
    status=$?
    set -e
    kill "$watchdog_pid" 2>/dev/null || true
    wait "$watchdog_pid" 2>/dev/null || true
  else
    set +e
    "$@" >"$stdout_file" 2>"$stderr_file"
    status=$?
    set -e
  fi

  cp "$stdout_file" "$result_file"

  if [ -f "$timeout_marker" ]; then
    {
      printf 'TIMEOUT after %ss: %s\n' "$test_timeout_secs" "$label"
      cat "$stderr_file"
    } >"$result_file"
  elif [ "$status" -ne 0 ] && [ ! -s "$stdout_file" ]; then
    {
      printf 'EXIT %s: %s\n' "$status" "$label"
      cat "$stderr_file"
    } >"$result_file"
  fi

  rm -f "$stdout_file" "$stderr_file" "$timeout_marker"
}

run_test() {
  test="$1"
  target_test="$test"
  [ -z "$target_test" ] && exit 1
  
  # First, run tests with bash
  export THIS_SH="$bash_build_dir/bash"
  run_capture ../results.bash "bash $target_test" "$THIS_SH" "$target_test"
  python3 "$filter_diff_script" -i ../results.bash
  cp ../results.bash "$results_dir"/$test.results.bash
  
  # Then, run tests with incr
  ln -sf "$PWD/../incr-bash-ts.sh" "$incr_this_sh"
  export THIS_SH="$incr_this_sh"
  run_capture ../results.incr "incr -b $target_test" env INCR_SHELL="$bash_build_dir/bash" "$THIS_SH" "$target_test"
  python3 "$filter_diff_script" -i ../results.incr
  cp ../results.incr "$results_dir"/$test.results.incr
}

if [ -n "$1" ]; then
	run_test "$1"
	exit 0
fi

all_tests="$(find . -type f -name "run-*" | grep -v all | grep -v minimal)"
tests="run-dollars run-execscript run-func run-getopts run-ifs run-input-test run-invert run-more-exp run-nquote run-ifs-posix run-posix2 run-posixpat run-precedence run-quote run-read run-rhs-exp run-strip run-tilde run-dynvar run-iquote run-type run-comsub-eof run-comsub-posix"

if [ -n "$INCR_BASH_TEST_FULL" ];
then
  tests="$all_tests"
fi

echo $tests 

for test in $tests; do
	run_test "${test#./}"
done
