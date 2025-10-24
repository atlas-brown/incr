#!/bin/bash
# tag: nginx logs
# IN=${IN:-/dependency_untangling/log_data}
# OUT=${OUT:-$PASH_TOP/evaluation/distr_benchmarks/dependency_untangling/input/output/nginx-logs}

pure_func() {
    tempfile=$(mktemp)

    tee $tempfile | cut -d "\"" -f3 | cut -d ' ' -f2 | sort | uniq -c | sort -rn   
    # awk alternative, too slow
    #awk '{print $9}' $tempfile | sort | uniq -c | sort -rn  
    # find broken links broken links
    #awk '($9 ~ /404/)' $tempfile | awk '{print $7}' | sort | uniq -c | sort -rn  
    # Who are requesting broken links (or URLs resulting in 502)
    #awk -F\" '($2 ~ "/wp-admin/install.php"){print $1}' $tempfile | awk '{print $1}' | sort | uniq -c | sort -r   
    ##############################
    # Most requested URLs ########
    #awk -F\" '{print $2}' $tempfile  | awk '{print $2}' | sort | uniq -c | sort -r  
    # Most requested URLs containing XYZ
    #awk -F\" '($2 ~ "ref"){print $2}' $tempfile | awk '{print $2}' | sort | uniq -c | sort -r

    rm $tempfile
}
export -f pure_func
for log in $INPUT/*; do
    cat $log | pure_func
    break
done
