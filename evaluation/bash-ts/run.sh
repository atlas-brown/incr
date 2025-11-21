#!/bin/sh

cd "$(dirname "$0")" || exit 1

[ ! -d bash ] && git clone http://git.savannah.gnu.org/bash.git
# make -C bash -j4
# make -C bash recho zecho printenv xcase -j4

export PATH="$PATH:$PWD/bash/tests"
export TMPDIR=/tmp

# First, run tests with bash
export THIS_SH=$PWD/bash/bash
export BASH_TSTOUT=/tmp/tstout

cd tests

# sh run-varenv > ../results.bash

# Then, run tests with incr
TOP=$(git rev-parse --show-toplevel)
rm -rf "$TOP/evaluation/bash-ts/cache"
export THIS_SH=$TOP/evaluation/bash-ts/incr.sh
export INCR_TSTOUT=/tmp/tstout

sh run-all > ../results.incr
