#!/bin/sh

cd "$(dirname "$0")" || exit 1

# [ ! -d bash ] && git clone https://github.com/bminor/bash && git -C bash checkout c5c97b3
# ( cd bash; CC=cc ./configure)
# make -C bash -j4
# make -C bash recho zecho printenv xcase -j4

target_test="run-precedence"

export PATH="$PATH:$PWD/bash"
export TMPDIR=/tmp
top=$(git rev-parse --show-toplevel)

# cd tests
cd tests-normln

# First, run tests with bash
export THIS_SH=$top/evaluation/bash-ts/bash/bash
export BASH_TSTOUT=/tmp/tstout

$THIS_SH $target_test > ../results.bash
cp /tmp/tstout ../out.bash

# Then, run tests with incr
rm -rf "$top/evaluation/bash-ts/cache"
export THIS_SH=$top/evaluation/bash-ts/incr.sh
export INCR_TSTOUT=/tmp/tstout

$THIS_SH $target_test > ../results.incr
cp /tmp/tstout ../out.incr

diff ../results.bash ../results.incr > ../results.diff
diff ../out.bash ../out.incr > ../out.diff
