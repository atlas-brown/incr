# Regression: cache.clean() must not remove files from cwd.
# Previously clean() used Path::new("data.incr") instead of cache_dir.join("data.incr").
# Use a distinct filename (not data.incr) to avoid any observe/try interaction.
source "$(dirname "$0")/common.sh"

echo "22. Cache clean does not touch cwd files"
rm -rf $CACHE
RUNDIR="$TESTDIR/run"
mkdir -p "$RUNDIR"
echo "preserved" > "$RUNDIR/preserve_me.txt"
echo "v1" > "$RUNDIR/in.txt"
(cd "$RUNDIR" && echo "" | "$INCR_ROOT/target/release/incr" --try "$INCR_ROOT/src/scripts/try.sh" --cache $CACHE --observe "$INCR_ROOT/../observe/target/release/observe" cp in.txt out.txt) >/dev/null 2>/dev/null
echo "v2" > "$RUNDIR/in.txt"
(cd "$RUNDIR" && echo "" | "$INCR_ROOT/target/release/incr" --try "$INCR_ROOT/src/scripts/try.sh" --cache $CACHE --observe "$INCR_ROOT/../observe/target/release/observe" cp in.txt out.txt) >/dev/null 2>/dev/null
[ "$(cat $RUNDIR/preserve_me.txt)" = "preserved" ] || { echo "FAIL: preserve_me.txt was removed from cwd"; exit 1; }
[ "$(cat $RUNDIR/out.txt)" = "v2" ] || { echo "FAIL: invalidation"; exit 1; }

echo "  t_incr_cache_clean: OK"
