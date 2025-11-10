#!/bin/sh

# First, run tests with bash
export THIS_SH=bash
export BASH_TSTOUT=/tmp/tstout

sh tests/run-all > results.bash

# Then, run tests with incr
export THIS_SH=incr
export INCR_TSTOUT=/tmp/tstout

sh tests/run-all > results.incr
