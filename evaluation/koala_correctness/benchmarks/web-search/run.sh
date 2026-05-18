#!/bin/bash
# web-search is skipped for two reasons:
# 1. Performance: the min dataset has 1000 articles; each article spawns a
#    fresh Node.js process for stem.js/getText.js/getURLs.js, costing ~3s per
#    article → >50 min at min inputs, well beyond any reasonable timeout.
# 2. Structural: crawl.sh and combine.sh both use mkfifo + backgrounded
#    readers/writers (limitation #4). Even if the performance were acceptable,
#    incr's strace-based tracker cannot follow data through named pipes whose
#    endpoints live in unrelated processes, causing hangs.
source "$(dirname "${BASH_SOURCE[0]}")/../../lib.sh"
kc_run_benchmark \
    --name web-search \
    --size "$KC_SIZE" \
    --skip-reason "too slow at min (1000 articles × ~3s Node.js startup) and mkfifo+& in crawl.sh/combine.sh (limitation #4)"
