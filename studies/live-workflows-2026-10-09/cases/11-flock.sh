#!/usr/bin/env bash
source "$DEMO/lib.sh"
# An existing job holds the lock while another job tries the same lock path.
# --close keeps the parent's lock FD out of the child's inherited descriptors.
flock --exclusive --close deploy.lock "$DEMO/backend.sh" bash -eu -c '
    exec 9>>deploy.lock
    if flock --nonblock 9; then echo "lock: overlap"; else echo "lock: busy"; fi
'
