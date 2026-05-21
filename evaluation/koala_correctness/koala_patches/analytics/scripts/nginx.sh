#!/bin/bash
# tag: nginx logs
# IN=${IN:-/dependency_untangling/log_data}
# OUT=${OUT:-$PASH_TOP/evaluation/distr_benchmarks/dependency_untangling/input/output/nginx-logs}
mkdir -p $2

# Inlined the original `pure_func` shell function. The function call itself
# works fine under incr — incr detects exported (`export -f`) functions via
# the `BASH_FUNC_pure_func%%` env var and dispatches them through `bash -c`.
# The real bug is that the function body's first wrapped command (`mktemp`)
# drains the function's piped stdin before its `tee` can read it. Inlining
# (and replacing piped stdin with `cp "$log" "$tempfile"`) lets every later
# stage read from the file rather than a piped stdin.
#
# Each pipeline appends to $logname rather than using `{ ... } > $logname`
# because incr's script rewriter only attaches the group redirect to the last
# statement inside the brace group, so the first N-1 statements' stdout would
# otherwise be lost.
for log in $1/*; do
    logname=$2/$(basename $log)
    tempfile=$(mktemp)
    cp "$log" "$tempfile"
    : > "$logname"
    cut -d "\"" -f3 <"$tempfile" | cut -d ' ' -f2 | sort | uniq -c | sort -rn >> "$logname"
    awk '{print $9}' "$tempfile" | sort | uniq -c | sort -rn >> "$logname"
    awk '($9 ~ /404/)' "$tempfile" | awk '{print $7}' | sort | uniq -c | sort -rn >> "$logname"
    awk '($9 ~ /502/)' "$tempfile" | awk '{print $7}' | sort | uniq -c | sort -r >> "$logname"
    awk -F\" '($2 ~ "/wp-admin/install.php"){print $1}' "$tempfile" | awk '{print $1}' | sort | uniq -c | sort -r >> "$logname"
    awk '($9 ~ /404/)' "$tempfile" | awk -F\" '($2 ~ "^GET .*.php")' | awk '{print $7}' | sort | uniq -c | sort -r | head -n 20 >> "$logname"
    awk -F\" '{print $2}' "$tempfile" | awk '{print $2}' | sort | uniq -c | sort -r >> "$logname"
    awk -F\" '($2 ~ "ref"){print $2}' "$tempfile" | awk '{print $2}' | sort | uniq -c | sort -r >> "$logname"
    rm "$tempfile"
done
