#!/bin/bash

cd "$(dirname "$0")" || exit 1

[ ! -d bash ] && git clone https://git.savannah.gnu.org/git/bash.git && git -C bash checkout c5c97b3
( cd bash && CC=cc ./configure)
make -C bash -j4
make -C bash recho zecho printenv xcase -j4

sudo rm -rf /tmp/cache
rm -f results.*

results_dir="$PWD/results"
mkdir -p "$results_dir"
top=$(git rev-parse --show-toplevel)
export PATH="$PATH:$PWD/bash"
export TMPDIR=/tmp
export BASH_TSTOUT=/tmp/tstout
export BUILD_DIR="$PWD/bash"

cd tests || exit 1

run_test() {
  test="$1"
  target_test="$test"
  [ -z "$target_test" ] && exit 1
  
  # First, run tests with bash
  export THIS_SH=$top/evaluation/bash-ts/bash/bash
  $THIS_SH $target_test > ../results.bash
  cp ../results.bash "$results_dir"/$test.results.bash
  
  # Then, run tests with incr
  export THIS_SH=$top/incr.sh
  $THIS_SH -b $target_test > ../results.incr
  cp ../results.incr "$results_dir"/$test.results.incr
}

if [ -n "$1" ]; then
	run_test "$1"
	exit 0
fi

all_tests="$(find . -type f -name "run-*" | sed 's/run-//' | grep -v all | grep -v minimal)"
tests="run-dollars run-execscript run-func run-getopts run-ifs-tests run-input-test run-invert run-more-exp run-nquote run-ifs-posix run-posix2 run-posixpat run-precedence run-quote run-read run-rhs-exp run-strip run-tilde run-dynvar run-iquote run-type run-comsub-eof run-comsub-posix"

if [ -n "$INCR_BASH_TEST_FULL" ];
then
  tests="$all_tests"
fi

for test in $tests; do
	run_test "${test#./}"
done
