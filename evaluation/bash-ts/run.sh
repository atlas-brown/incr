#!/bin/sh

cd "$(dirname "$0")" || exit 1

# [ ! -d bash ] && git clone https://github.com/bminor/bash && git -C bash checkout c5c97b3
# ( cd bash; CC=cc ./configure)
# make -C bash -j4
# make -C bash recho zecho printenv xcase -j4

target_test="run-precedence"

export PATH="$PATH:$PWD/bash"
export TMPDIR=/tmp

# First, run tests with bash
export THIS_SH=$PWD/bash/bash
export BASH_TSTOUT=/tmp/tstout

# cd tests
cd tests-normln

sh $target_test > ../results.bash

# Then, run tests with incr
TOP=$(git rev-parse --show-toplevel)
rm -rf "$TOP/evaluation/bash-ts/cache"
export THIS_SH=$TOP/evaluation/bash-ts/incr.sh
export INCR_TSTOUT=/tmp/tstout

sh $target_test > ../results.incr

diff ../results.bash ../results.incr > ../results.diff
