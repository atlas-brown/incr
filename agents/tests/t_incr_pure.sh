source "$(dirname "$0")/common.sh"

echo "7. grep (pure)"
rm -rf $CACHE
run_pipe "$(printf 'a\nb\nc')" grep -q b
run_pipe "$(printf 'a\nb\nc')" grep -q b

echo "  t_incr_pure: OK"
