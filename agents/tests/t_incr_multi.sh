source "$(dirname "$0")/common.sh"

echo "8. Multi-file write"
rm -rf $CACHE $TESTDIR/f1.txt $TESTDIR/f2.txt
run_empty_obs bash -c "echo one > $TESTDIR/f1.txt; echo two > $TESTDIR/f2.txt"
[ "$(cat $TESTDIR/f1.txt)" = "one" ] && [ "$(cat $TESTDIR/f2.txt)" = "two" ] || { echo "FAIL: multi"; exit 1; }
rm $TESTDIR/f1.txt $TESTDIR/f2.txt
run_empty_obs bash -c "echo one > $TESTDIR/f1.txt; echo two > $TESTDIR/f2.txt"
[ "$(cat $TESTDIR/f1.txt)" = "one" ] && [ "$(cat $TESTDIR/f2.txt)" = "two" ] || { echo "FAIL: multi cache"; exit 1; }

echo "  t_incr_multi: OK"
