#!/bin/bash
# Comprehensive test script for incr + observe integration
# Use: bash test_incr_observe.sh
set -e

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

echo "1. TraceFile (strace) - cat"
rm -rf $CACHE
run_pipe "hello" cat | grep -q hello
run_pipe "hello" cat | grep -q hello  # cache hit

echo "2. TraceFile (observe) - cat"
rm -rf $CACHE
run_pipe_obs "world" cat | grep -q world
run_pipe_obs "world" cat | grep -q world  # cache hit

echo "3. Sandbox (no observe) - write"
rm -rf $CACHE
run_empty bash -c "echo sandbox > $TESTDIR/sb.txt"
[ "$(cat $TESTDIR/sb.txt)" = "sandbox" ] || { echo "FAIL: sandbox"; exit 1; }
run_empty bash -c "echo sandbox > $TESTDIR/sb.txt"  # cache hit
[ "$(cat $TESTDIR/sb.txt)" = "sandbox" ] || { echo "FAIL: sandbox cache"; exit 1; }

echo "4. Observe mode - write"
rm -rf $CACHE $TESTDIR/obs.txt
run_empty_obs bash -c "echo observe > $TESTDIR/obs.txt"
[ "$(cat $TESTDIR/obs.txt)" = "observe" ] || { echo "FAIL: observe"; exit 1; }
rm $TESTDIR/obs.txt
run_empty_obs bash -c "echo observe > $TESTDIR/obs.txt"  # cache hit
[ "$(cat $TESTDIR/obs.txt)" = "observe" ] || { echo "FAIL: observe cache"; exit 1; }

echo "5. Batch executor + observe"
rm -rf $CACHE $TESTDIR/batch.txt
echo "" | $INCR -b --try $TRY --cache $CACHE --observe $OBSERVE bash -c "echo batch > $TESTDIR/batch.txt"
[ "$(cat $TESTDIR/batch.txt)" = "batch" ] || { echo "FAIL: batch"; exit 1; }
rm $TESTDIR/batch.txt
echo "" | $INCR -b --try $TRY --cache $CACHE --observe $OBSERVE bash -c "echo batch > $TESTDIR/batch.txt"
[ "$(cat $TESTDIR/batch.txt)" = "batch" ] || { echo "FAIL: batch cache"; exit 1; }

echo "6. cp (read+write) + cache invalidation"
rm -rf $CACHE
echo "input" > $TESTDIR/in.txt
run_empty_obs cp $TESTDIR/in.txt $TESTDIR/out.txt
[ "$(cat $TESTDIR/out.txt)" = "input" ] || { echo "FAIL: cp"; exit 1; }
rm $TESTDIR/out.txt
run_empty_obs cp $TESTDIR/in.txt $TESTDIR/out.txt  # cache hit
[ "$(cat $TESTDIR/out.txt)" = "input" ] || { echo "FAIL: cp cache"; exit 1; }
echo "modified" > $TESTDIR/in.txt
run_empty_obs cp $TESTDIR/in.txt $TESTDIR/out.txt  # invalidation
[ "$(cat $TESTDIR/out.txt)" = "modified" ] || { echo "FAIL: invalidation"; exit 1; }

echo "7. grep (pure, TraceType::Nothing)"
rm -rf $CACHE
run_pipe "$(printf 'a\nb\nc')" grep -q b
run_pipe "$(printf 'a\nb\nc')" grep -q b  # cache hit

echo "8. Multi-file write"
rm -rf $CACHE $TESTDIR/f1.txt $TESTDIR/f2.txt
run_empty_obs bash -c "echo one > $TESTDIR/f1.txt; echo two > $TESTDIR/f2.txt"
[ "$(cat $TESTDIR/f1.txt)" = "one" ] && [ "$(cat $TESTDIR/f2.txt)" = "two" ] || { echo "FAIL: multi"; exit 1; }
rm $TESTDIR/f1.txt $TESTDIR/f2.txt
run_empty_obs bash -c "echo one > $TESTDIR/f1.txt; echo two > $TESTDIR/f2.txt"
[ "$(cat $TESTDIR/f1.txt)" = "one" ] && [ "$(cat $TESTDIR/f2.txt)" = "two" ] || { echo "FAIL: multi cache"; exit 1; }

echo ""
echo "All 8 test groups passed!"
