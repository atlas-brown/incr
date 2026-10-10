# Only backend selection lives here. Coordination is visible in each example.
set -euo pipefail
: "${DEMO:?Run this example through run.sh}"
memo() { "$DEMO/backend.sh" "$@"; }
