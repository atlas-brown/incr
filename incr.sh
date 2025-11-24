#!/bin/bash

incr_shell=${INCR_SHELL:-bash}
args=""
flags=""

while getopts "c:o:ue" opt; do
    case "$opt" in
        c) cmd_str="$OPTARG" ;;
        o) args="$args -o $OPTARG" ;;
	u) flags="$flags -u" ;;
	e) flags="$flags -e" ;;
        *) echo "Usage: $0 [-c 'cmd'] <script>" >&2; exit 1 ;;
    esac
done
shift $((OPTIND - 1))

# hack to handle missparing `sh -ce $cmd`
if [ "$cmd_str" = e ]; then
   cmd_str="$@"	
   flags="$flags -e"
fi

if [ -n "$cmd_str" ]; then
    exec -a "$0" "$incr_shell" $flags $args -c "$cmd_str" "$@"
fi

if [ $# -eq 0 ] && [ ! -t 0 ]; then
    # Explicit -s means "read commands from stdin".
    exec -a $0 "$incr_shell" $flags -s $args
fi

script=$1
shift
cache_dir=/tmp/cache

[ -z "$script" ] && echo "Usage: $0 <script>" && exit 1
[ -z "$cache_dir" ] && echo "Usage: $0 <script>" && exit 1

TOP=$(git rev-parse --show-toplevel)
TRY_PATH="$TOP/src/scripts/try.sh"
tmp_incr="$(dirname $script)/incr_script_$(basename $script).sh"
tmp_orig=$(mktemp)

# Ensure cleanup and preserve the right exit status.
rc=
cleanup() {
    # If we recorded the temp script's status, use it; otherwise use last command's.
    local st=${rc:-$?}
    # Restore the original script.
    cp "$tmp_orig" "$script"
    # Delete all tmp files
    rm -f "$tmp_orig"
    # rm -f "$tmp_incr"
    exit $st
}
trap cleanup EXIT INT TERM

python3 ${TOP}/src/scripts/insert.py --bash --sys-path ${TOP}/target/release/incr --try $TRY_PATH --cache "$cache_dir" "$script" > "$tmp_incr"

# Swap the original script with the incrementalized one.
cp "$script" "$tmp_orig"
cp "$tmp_incr" "$script"

# $script now is $tmp_incr
$incr_shell $flags $args -- "$script" "$@"
rc=$?
