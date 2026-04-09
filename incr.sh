#!/bin/bash

incr_shell=${INCR_SHELL:-bash}
args=""
flags=""

while getopts "c:o:ueti" opt; do
    case "$opt" in
        c) cmd_str="$OPTARG" ;;
        o) args="$args -o $OPTARG" ;;
	u) flags="$flags -u" ;;
	e) flags="$flags -e" ;;
	t) flags="$flags -t" ;;
	i) flags="$flags -i" ;;
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
cache_dir=${1:-/tmp/incr_cache}

[ -z "$script" ] && echo "Usage: $0 <script>" && exit 1

mkdir -p "$cache_dir"

TOP=$(git rev-parse --show-toplevel)
TRY_PATH="$TOP/src/scripts/try.sh"
tmp_incr="$(dirname "$script")/incr_script_$(basename "$script").sh"
# Sentinel: presence signals cleanup needed; contents ARE the original script.
sentinel="${script}.incr_orig"

# Recover from a previous SIGKILL: restore original from sentinel and continue.
if [ -f "$sentinel" ]; then
    cp "$sentinel" "$script"
    rm -f "$sentinel"
fi

rc=
cleanup() {
    trap '' EXIT INT TERM
    local st=${rc:-$?}
    if [ -f "$sentinel" ]; then
        cp "$sentinel" "$script"
    fi
    rm -f "$sentinel"
    rm -f "$tmp_incr"
    exit $st
}
trap cleanup EXIT INT TERM

python3 ${TOP}/src/scripts/insert.py --sys-path ${TOP}/target/release/incr --try $TRY_PATH --cache "$cache_dir" "$script" > "$tmp_incr"

# sentinel IS the backup; after this point any kill is recoverable
cp "$script" "$sentinel"
cp "$tmp_incr" "$script"

$incr_shell $flags $args -- "$script" "$@"
rc=$?
