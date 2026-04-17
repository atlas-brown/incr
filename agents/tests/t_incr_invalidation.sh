source "$(dirname "$0")/common.sh"

echo "6. cp + cache invalidation"
rm -rf $CACHE
# Input must be outside /tmp: observe excludes /tmp reads from dependency tracking.
echo "input" > $TESTDIR_OBS/in.txt
run_empty_obs cp $TESTDIR_OBS/in.txt $TESTDIR_OBS/out.txt
[ "$(cat $TESTDIR_OBS/out.txt)" = "input" ] || { echo "FAIL: cp"; exit 1; }
rm $TESTDIR_OBS/out.txt
run_empty_obs cp $TESTDIR_OBS/in.txt $TESTDIR_OBS/out.txt
[ "$(cat $TESTDIR_OBS/out.txt)" = "input" ] || { echo "FAIL: cp cache"; exit 1; }
echo "modified" > $TESTDIR_OBS/in.txt
run_empty_obs cp $TESTDIR_OBS/in.txt $TESTDIR_OBS/out.txt
[ "$(cat $TESTDIR_OBS/out.txt)" = "modified" ] || { echo "FAIL: invalidation"; exit 1; }

echo "  t_incr_invalidation: OK"
