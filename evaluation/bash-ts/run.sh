#!/bin/bash

cd "$(dirname "$0")" || exit 1

# [ ! -d bash ] && git clone https://github.com/bminor/bash && git -C bash checkout c5c97b3
# ( cd bash; CC=cc ./configure)
# make -C bash -j4
# make -C bash recho zecho printenv xcase -j4

sudo rm -rf /tmp/cache
rm -f out.* results.*

[ -z "$1" ] && exit 1

results_dir="$PWD/results"
test="$1"
target_test="run-$test"
[ -z "$target_test" ] && exit 1
top=$(git rev-parse --show-toplevel)
export PATH="$PATH:$PWD/bash"
export TMPDIR=/tmp
export BASH_TSTOUT=/tmp/tstout
export BUILD_DIR="$PWD/bash"

mkdir -p "$results_dir"

cd tests || exit 1

# First, run tests with bash
export THIS_SH=$top/evaluation/bash-ts/bash/bash
$THIS_SH $target_test > ../results.bash
cp ../results.bash "$results_dir"/$test.results.bash

# Then, run tests with incr
export THIS_SH=$top/evaluation/bash-ts/incr.sh
$THIS_SH $target_test > ../results.incr
cp ../results.incr "$results_dir"/$test.results.incr

# Finally, diff results
diff ../results.bash ../results.incr > ../results.diff
nl()
{
	# Normalize line numbers
	sed -E 's/line [0-9]+/line xxxx/' $1 
}
# diff <(nl ../out.bash) <(nl ../out.incr) > ../out.diff
