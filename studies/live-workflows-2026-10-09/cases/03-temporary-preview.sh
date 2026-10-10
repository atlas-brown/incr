#!/usr/bin/env bash
source "$DEMO/lib.sh"
# A renderer keeps its temporary output until its caller finishes the preview.
: > viewed
memo bash -eu -c '
    directory=$(mktemp -d ./preview.XXXXXX)
    trap '\''rm -rf "$directory"'\'' EXIT
    echo "<h1>Preview</h1>" > "$directory/index.html"
    echo "$directory/index.html"
    until grep -q viewed viewed; do sleep .02; done
' | while IFS= read -r page; do
    if [[ -f $page ]]; then cat "$page"; else echo 'preview: unavailable'; fi
    echo viewed > viewed
done
[[ -z $(find . -maxdepth 1 -name 'preview.*' -print -quit) ]]
echo 'preview: cleaned'
