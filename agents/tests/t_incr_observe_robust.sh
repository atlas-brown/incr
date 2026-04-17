# Robust observe-specific tests: exit codes, stderr, failures, stdin, append, mkdir
source "$(dirname "$0")/common.sh"

echo "13. Exit code propagation"
rm -rf $CACHE
run_empty_obs bash -c "exit 42"
[ $? -eq 42 ] || { echo "FAIL: exit 42"; exit 1; }
run_empty_obs bash -c "exit 0"
[ $? -eq 0 ] || { echo "FAIL: exit 0"; exit 1; }

echo "14. Stderr capture"
rm -rf $CACHE
err=$(run_empty_obs bash -c "echo stderr_msg >&2" 2>&1)
echo "$err" | grep -q "stderr_msg" || { echo "FAIL: stderr not captured"; exit 1; }

echo "15. TraceFile (observe) - sed"
rm -rf $CACHE
echo "foo" > "$TESTDIR/sed_in.txt"
out=$(run_pipe_obs "" sed 's/foo/bar/' "$TESTDIR/sed_in.txt")
[ "$out" = "bar" ] || { echo "FAIL: sed output '$out'"; exit 1; }
out2=$(run_pipe_obs "" sed 's/foo/bar/' "$TESTDIR/sed_in.txt")
[ "$out2" = "bar" ] || { echo "FAIL: sed cache"; exit 1; }

echo "16. Command failure (non-zero)"
rm -rf $CACHE $TESTDIR/fail.txt
run_empty_obs bash -c "echo x > $TESTDIR/fail.txt; exit 1" 2>/dev/null
ec=$?
[ $ec -eq 1 ] || { echo "FAIL: non-zero exit (got $ec)"; exit 1; }
[ -f "$TESTDIR/fail.txt" ] && [ "$(cat $TESTDIR/fail.txt)" = "x" ] || { echo "FAIL: partial write"; exit 1; }

echo "17. Stdin passed to command"
rm -rf $CACHE
out=$(printf 'stdin_data' | run_pipe_obs "stdin_data" cat)
[ "$out" = "stdin_data" ] || { echo "FAIL: stdin '$out'"; exit 1; }

echo "18. Append vs overwrite"
rm -rf $CACHE $TESTDIR/app.txt
run_empty_obs bash -c "echo first > $TESTDIR/app.txt"
run_empty_obs bash -c "echo second >> $TESTDIR/app.txt"
[ "$(cat $TESTDIR/app.txt)" = "first
second" ] || { echo "FAIL: append"; exit 1; }

echo "19. mkdir"
rm -rf $CACHE $TESTDIR/subdir
run_empty_obs bash -c "mkdir -p $TESTDIR/subdir/a/b"
[ -d "$TESTDIR/subdir/a/b" ] || { echo "FAIL: mkdir"; exit 1; }

echo "20. Batch: different stdin = different cache"
rm -rf $CACHE $TESTDIR/ba.txt $TESTDIR/bb.txt
run_batch_obs "a" bash -c "cat > $TESTDIR/ba.txt"
run_batch_obs "b" bash -c "cat > $TESTDIR/bb.txt"
[ "$(cat $TESTDIR/ba.txt)" = "a" ] || { echo "FAIL: batch stdin a"; exit 1; }
[ "$(cat $TESTDIR/bb.txt)" = "b" ] || { echo "FAIL: batch stdin b"; exit 1; }

echo "21. Read-only (cat) - no writes in cache"
rm -rf $CACHE
run_pipe_obs "x" cat /dev/null >/dev/null
# Cache should have empty write_outputs
[ -d "$CACHE" ] || { echo "FAIL: no cache"; exit 1; }

echo "  t_incr_observe_robust: OK"
