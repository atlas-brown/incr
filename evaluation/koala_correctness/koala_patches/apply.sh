#!/bin/bash
# Apply (or revert) the koala-patches in this directory against a koala repo.
#
# Layout: every file under koala_patches/ that is not this script or the README
# corresponds to the same relative path under the target koala repo. For
# example,
#
#     koala_patches/nlp/scripts/bigrams.sh  ->  <koala>/nlp/scripts/bigrams.sh
#
# On --apply, the original file at the destination is preserved as
# `<dest>.kc_orig` before being overwritten. --revert restores those backups.
# Both subcommands are idempotent.
#
# Usage:
#     apply.sh --apply  <koala-repo>
#     apply.sh --revert <koala-repo>
#     apply.sh --check  <koala-repo>
set -euo pipefail

usage() {
    sed -n '2,16p' "$0"
    exit "${1:-2}"
}

[[ $# -eq 2 ]] || usage
action=$1
koala=$2
[[ -d "$koala" ]] || { echo "apply.sh: not a directory: $koala" >&2; exit 2; }
koala=$(cd "$koala" && pwd)

patches_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# All patch files (relative paths) — anything under patches_dir except this
# script and the README.
mapfile -t patches < <(
    cd "$patches_dir"
    find . -type f \
        \! -name 'apply.sh' \
        \! -name 'README.md' \
        -printf '%P\n' | sort
)

apply_one() {
    local rel=$1
    local src="$patches_dir/$rel"
    local dest="$koala/$rel"
    if [[ ! -f "$dest" ]]; then
        echo "  MISSING  $rel (no upstream file in $koala)" >&2
        return 1
    fi
    if cmp -s "$src" "$dest"; then
        echo "  SKIP     $rel (already patched)"
        return 0
    fi
    if [[ ! -f "$dest.kc_orig" ]]; then
        cp -p "$dest" "$dest.kc_orig"
    fi
    cp -p "$src" "$dest"
    echo "  PATCH    $rel"
}

revert_one() {
    local rel=$1
    local dest="$koala/$rel"
    if [[ -f "$dest.kc_orig" ]]; then
        mv "$dest.kc_orig" "$dest"
        echo "  REVERT   $rel"
        return 0
    fi
    echo "  SKIP     $rel (no backup; assuming already pristine)"
}

check_one() {
    local rel=$1
    local src="$patches_dir/$rel"
    local dest="$koala/$rel"
    if [[ ! -f "$dest" ]]; then
        echo "  MISSING  $rel"
        return 1
    fi
    if cmp -s "$src" "$dest"; then
        echo "  PATCHED  $rel"
    else
        echo "  UPSTREAM $rel"
    fi
}

case "$action" in
    --apply)
        echo "Applying koala patches from $patches_dir to $koala"
        rc=0
        for rel in "${patches[@]}"; do apply_one "$rel" || rc=$?; done
        exit "$rc"
        ;;
    --revert)
        echo "Reverting koala patches in $koala"
        for rel in "${patches[@]}"; do revert_one "$rel"; done
        ;;
    --check)
        echo "Checking $koala against patches in $patches_dir"
        for rel in "${patches[@]}"; do check_one "$rel"; done
        ;;
    *) usage 2 ;;
esac
