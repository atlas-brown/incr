source "$(dirname "$0")/common.sh"

echo "1. TraceFile (strace) - cat"
rm -rf $CACHE
run_pipe "hello" cat | grep -q hello
run_pipe "hello" cat | grep -q hello

echo "2. TraceFile (observe) - cat"
rm -rf $CACHE
run_pipe_obs "world" cat | grep -q world
run_pipe_obs "world" cat | grep -q world

echo "3. Sandbox (no observe) - write"
rm -rf $CACHE
run_empty bash -c "echo sandbox > $TESTDIR/sb.txt"
[ "$(cat $TESTDIR/sb.txt)" = "sandbox" ] || { echo "FAIL: sandbox"; exit 1; }
run_empty bash -c "echo sandbox > $TESTDIR/sb.txt"
[ "$(cat $TESTDIR/sb.txt)" = "sandbox" ] || { echo "FAIL: sandbox cache"; exit 1; }

echo "4. Observe mode - write"
rm -rf $CACHE $TESTDIR/obs.txt
run_empty_obs bash -c "echo observe > $TESTDIR/obs.txt"
[ "$(cat $TESTDIR/obs.txt)" = "observe" ] || { echo "FAIL: observe"; exit 1; }
rm $TESTDIR/obs.txt
run_empty_obs bash -c "echo observe > $TESTDIR/obs.txt"
[ "$(cat $TESTDIR/obs.txt)" = "observe" ] || { echo "FAIL: observe cache"; exit 1; }

echo "  t_incr_basic: OK"
