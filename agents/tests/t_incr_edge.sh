source "$(dirname "$0")/common.sh"

echo "9. Stream + head (BrokenPipe)"
rm -rf $CACHE
data=$(for i in $(seq 1 10000); do echo "line $i"; done)
run_pipe_obs_s "$data" cat 2>/dev/null | head -1 > "$TESTDIR/head_out.txt"
code=${PIPESTATUS[0]}
[ "$(cat $TESTDIR/head_out.txt)" = "line 1" ] || { echo "FAIL: head output"; exit 1; }
[ "$code" = "141" ] || { echo "FAIL: expected 141, got $code"; exit 1; }

echo "10. Cache hit + head (BrokenPipe)"
rm -rf $CACHE
run_pipe_obs_s "$data" cat >/dev/null
run_pipe_obs_s "$data" cat 2>/dev/null | head -1 > "$TESTDIR/head_out.txt"
code=${PIPESTATUS[0]}
[ "$(cat $TESTDIR/head_out.txt)" = "line 1" ] || { echo "FAIL: cache hit output"; exit 1; }
[ "$code" = "141" ] || { echo "FAIL: expected 141, got $code"; exit 1; }

echo "11. Observe write"
rm -rf $CACHE $TESTDIR/edge.txt
run_empty_obs bash -c "echo written > $TESTDIR/edge.txt"
[ "$(cat $TESTDIR/edge.txt)" = "written" ] || { echo "FAIL: edge write"; exit 1; }

echo "12. No trace file leak"
rm -rf $CACHE
run_pipe_obs "data" cat >/dev/null
run_pipe_obs "data" cat >/dev/null
stray=$(ls $CACHE/observe_*.json 2>/dev/null || true)
[ -z "$stray" ] || { echo "FAIL: stray trace files: $stray"; exit 1; }

echo "  t_incr_edge: OK"
