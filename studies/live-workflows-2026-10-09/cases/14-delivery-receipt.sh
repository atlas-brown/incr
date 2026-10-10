#!/usr/bin/env bash
source "$DEMO/lib.sh"
# The consumer deletes a retry ticket to acknowledge successful delivery.
echo previous > pending
: > receipt
memo bash -eu -c '
    echo invoice-42 > pending
    echo invoice-42
    until grep -q receipt receipt; do sleep .02; done
    if [[ -e pending ]]; then echo retry; else echo delivered; fi
' | {
    read -r invoice
    echo "consumer: $invoice"
    rm pending
    echo receipt > receipt
    read -r result
    echo "sender: $result"
}
