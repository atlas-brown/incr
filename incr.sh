#!/bin/bash -p

incr_shell=${INCR_SHELL:-/bin/bash}
# A native launcher can preserve exec -a's argv[0] across the script interpreter.
incr_shell_argv0=${INCR_ARGV0:-$0}
unset INCR_ARGV0
args=()
flags=()
parser_flags=()
has_command=0
read_stdin=0

# Preserve Bash option ordering, including long options before short options.
while (($#)); do
    case "$1" in
        --) shift; break ;;
        --rcfile|--init-file)
            (($# >= 2)) || exit 2
            flags+=("$1" "$2"); shift 2 ;;
        --norc|--noprofile|--posix|--restricted|--verbose|--login|--help|--version)
            flags+=("$1"); shift ;;
        +o)
            (($# >= 2)) || exit 2
            flags+=("$1" "$2"); shift 2 ;;
        +?*) flags+=("$1"); shift ;;
        -?*)
            option_letters=${1#-}
            shift
            while [[ -n "$option_letters" ]]; do
                opt=${option_letters:0:1}
                option_letters=${option_letters:1}
                case "$opt" in
                    c) has_command=1 ;;
                    b) parser_flags+=(--bash) ;;
                    s) read_stdin=1 ;;
                    o)
                        if [[ -n "$option_letters" ]]; then
                            flags+=(-o "$option_letters"); option_letters=
                        else
                            (($#)) || exit 2
                            flags+=(-o "$1"); shift
                        fi ;;
                    u|e|t|i|n|v|x|r|l|a|B|C|E|T|P|h|m|p|f|d|D|H) flags+=("-$opt") ;;
                    *) echo "$0: invalid option: -$opt" >&2; exit 2 ;;
                esac
            done ;;
        *) break ;;
    esac
done

if ((has_command)); then
    if (($# == 0)); then
        echo "$0: -c: option requires an argument" >&2
        exit 2
    fi
    cmd_str=$1
    shift
    exec -a "$incr_shell_argv0" "$incr_shell" "${flags[@]}" "${args[@]}" -c "$cmd_str" "$@"
fi

if ((read_stdin)) || (($# == 0)); then
    exec -a "$incr_shell_argv0" "$incr_shell" "${flags[@]}" "${args[@]}" -s -- "$@"
fi

script=$1
shift

if [ -n "${INCR_CACHE_DIR:-}" ]; then
    cache_dir=$INCR_CACHE_DIR
elif [ $# -gt 0 ]; then
    cache_dir=$1
    shift
else
    cache_dir=/tmp/incr_cache
fi

[ -z "$script" ] && echo "Usage: $0 [-b] <script>" && exit 1

# Let Bash diagnose missing paths, directories, binary inputs, and files that
# cannot be parsed as text. Preserve its status instead of a parser error.
if [ ! -f "$script" ] || [ ! -r "$script" ] ||
   ! LC_ALL=C command -p grep -Iq . "$script"; then
    exec -a "$incr_shell_argv0" "$incr_shell" "${flags[@]}" "${args[@]}" -- "$script" "$@"
fi

# These modes expose startup/source details or suppress BASH_ENV. Execute
# natively because a private transformed file cannot preserve those details.
for flag in "${flags[@]}"; do
    case "$flag" in
        -p|-i|-r|-n|-v|-x|-l|-a|-t|--restricted|--verbose|--login|privileged|noexec|verbose|xtrace|onecmd|allexport)
            exec -a "$incr_shell_argv0" "$incr_shell" "${flags[@]}" "${args[@]}" -- "$script" "$@" ;;
    esac
done
command -p mkdir -p "$cache_dir"

TOP=${INCR_TOP:-$(cd -- "$(command -p dirname -- "${BASH_SOURCE[0]}")" && pwd)}
TRY_PATH="${INCR_TRY_PATH:-$TOP/src/scripts/try.sh}"
SYS_PATH="${INCR_SYS_PATH:-$TOP/target/release/incr}"
OBSERVE_PATH=""
# INCR_OBSERVE=0 forces default mode (try+strace); 1 or unset uses observe when available
observe_candidate="${INCR_OBSERVE_PATH:-$TOP/../observe/target/release/observe}"
if [ "${INCR_OBSERVE:-1}" != "0" ] && [ -x "$observe_candidate" ]; then
    OBSERVE_PATH="$observe_candidate"
elif [ "${INCR_OBSERVE:-}" = "1" ]; then
    echo "Observe requested but not executable: $observe_candidate" >&2
    exit 1
fi
# Each invocation owns a transformed copy. The caller's script is never
# rewritten, so parallel invocations and interruption cannot corrupt it.
tmp_dir=$(command -p mktemp -d "$cache_dir/incr-script.XXXXXXXX") || exit 1
command -p mkdir -- "$tmp_dir/script" || exit 1
tmp_incr="$tmp_dir/script/$(command -p basename -- "$script")"
tmp_body="$tmp_dir/body"
cleanup() {
    local st=$1
    trap '' EXIT INT TERM
    command -p rm -f -- "$tmp_incr" "$tmp_body"
    command -p rmdir -- "$tmp_dir/script" "$tmp_dir"
    exit "$st"
}
trap 'cleanup "$?"' EXIT
trap 'cleanup 130' INT
trap 'cleanup 143' TERM

transform_args=(--sys-path "$SYS_PATH" --try-path "$TRY_PATH" --cache-path "$cache_dir")
transform_args+=("${parser_flags[@]}")
[ -n "$OBSERVE_PATH" ] && transform_args+=(--observe-path "$OBSERVE_PATH")
if ! command -p "${INCR_PYTHON:-python3}" "$TOP/src/scripts/insert.py" "${transform_args[@]}" "$script" > "$tmp_body"; then
    exit 1
fi

if command -p cmp -s -- "$script" "$tmp_body"; then
    command -p rm -f -- "$tmp_incr" "$tmp_body"
    command -p rmdir -- "$tmp_dir/script" "$tmp_dir"
    exec -a "$incr_shell_argv0" "$incr_shell" "${flags[@]}" "${args[@]}" -- "$script" "$@"
fi

# A real script preserves Bash's top-level error and control-flow semantics.
# Set $0 inside the program: Bash resets it after startup files have run.
# Source-introspective scripts take the native path above.
printf 'BASH_ARGV0=%q\n' "$script" > "$tmp_incr"
command -p cat -- "$tmp_body" >> "$tmp_incr"
"$incr_shell" "${flags[@]}" "${args[@]}" -- "$tmp_incr" "$@"
exit "$?"
