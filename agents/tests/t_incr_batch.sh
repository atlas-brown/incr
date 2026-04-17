source "$(dirname "$0")/common.sh"

echo "5. Batch executor + observe"
rm -rf $CACHE $TESTDIR/batch.txt
echo "" | $INCR -b --try $TRY --cache $CACHE --observe $OBSERVE bash -c "echo batch > $TESTDIR/batch.txt"
[ "$(cat $TESTDIR/batch.txt)" = "batch" ] || { echo "FAIL: batch"; exit 1; }
rm $TESTDIR/batch.txt
echo "" | $INCR -b --try $TRY --cache $CACHE --observe $OBSERVE bash -c "echo batch > $TESTDIR/batch.txt"
[ "$(cat $TESTDIR/batch.txt)" = "batch" ] || { echo "FAIL: batch cache"; exit 1; }

echo "  t_incr_batch: OK"
