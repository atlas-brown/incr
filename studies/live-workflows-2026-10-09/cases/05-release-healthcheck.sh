#!/usr/bin/env bash
source "$DEMO/lib.sh"
# Deploy, ask the caller to check the live path, and roll back if unhealthy.
mkdir v1 v2
echo v1 > v1/index; echo v2 > v2/index
ln -s v1 current
: > verdict
memo bash -eu -c '
    ln -s v2 next; mv -Tf next current
    echo check
    until grep -q . verdict; do sleep .02; done
    if [[ $(cat verdict) != healthy ]]; then
        ln -s v1 rollback; mv -Tf rollback current
    fi
' | {
    read -r request; [[ $request == check ]]
    version=$(cat current/index)
    echo "healthcheck: $version"
    if [[ $version == v2 ]]; then echo healthy; else echo unhealthy; fi > verdict
}
