TOP=$(git rev-parse --show-toplevel)
PROGRAM="${TOP}/target/release/incr -a"

find "./inputs/pg-small" -type f -name '*.txt' -exec cat {} + |
$PROGRAM tr "[:upper:]" "[:lower:]" |
$PROGRAM grep -Pa "(?=.{50,})\b\w*([aeiouyAEIOUY]\w*){5,}\b"