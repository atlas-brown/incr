#!/bin/bash
# pkg/proginf: static program analysis of npm packages using mir-sa (Java).
# pacaur is excluded because it makes live network requests.
# Requires: default-jre-headless (for mir-sa.jar), wget (for inputs).
# Inputs are fetched from atlas.cs.brown.edu/data/prog-inf/; at --min,
# only 2 packages are analysed (~2 seconds).
source "$(dirname "${BASH_SOURCE[0]}")/../../lib.sh"
kc_run_benchmark \
    --name pkg \
    --size "$KC_SIZE" \
    --deps java \
    --timeout-min 120 \
    --timeout-small 600 \
    --timeout-full 3600 \
    --scripts proginf
