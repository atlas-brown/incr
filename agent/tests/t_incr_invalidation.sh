source "$(dirname "$0")/common.sh"

echo "6. cp + cache invalidation"
rm -rf $CACHE
echo "input" > $TESTDIR/in.txt
run_empty_obs cp $TESTDIR/in.txt $TESTDIR/out.txt
[ "$(cat $TESTDIR/out.txt)" = "input" ] || { echo "FAIL: cp"; exit 1; }
rm $TESTDIR/out.txt
run_empty_obs cp $TESTDIR/in.txt $TESTDIR/out.txt
[ "$(cat $TESTDIR/out.txt)" = "input" ] || { echo "FAIL: cp cache"; exit 1; }
echo "modified" > $TESTDIR/in.txt
run_empty_obs cp $TESTDIR/in.txt $TESTDIR/out.txt
[ "$(cat $TESTDIR/out.txt)" = "modified" ] || { echo "FAIL: invalidation"; exit 1; }

echo "  t_incr_invalidation: OK"
