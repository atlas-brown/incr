#!/bin/sh
set -eu

REPO_URL="${INCR_REPO_URL:-https://github.com/atlas-brown/incr}"
INSTALL_DIR="${INCR_DIR:-$HOME/incr}"

need_cmd() {
    command -v "$1" >/dev/null 2>&1
}

install_system_deps() {
    export DEBIAN_FRONTEND=noninteractive
    sudo apt update
    sudo apt upgrade -y
    sudo apt install -y git mergerfs strace python3-pip python3-venv curl ca-certificates build-essential pkg-config libssl-dev libtool
}

install_rust() {
    if need_cmd cargo; then
        return
    fi

    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
}

load_rust_env() {
    if [ -f "$HOME/.cargo/env" ]; then
        # shellcheck disable=SC1091
        . "$HOME/.cargo/env"
    fi
}

prepare_repo() {
    if [ -f "./Cargo.toml" ] && [ -f "./requirements.txt" ]; then
        pwd
        return
    fi

    if [ ! -d "$INSTALL_DIR/.git" ]; then
        git clone "$REPO_URL" "$INSTALL_DIR"
    fi

    cd "$INSTALL_DIR"
    pwd
}

install_python_deps() {
    python_cmd="${INCR_PYTHON:-python3}"

    if ! need_cmd "$python_cmd"; then
        echo "$python_cmd not found" >&2
        exit 1
    fi

    if ! "$python_cmd" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
        echo "$python_cmd must be Python 3.10 or newer" >&2
        exit 1
    fi

    if [ ! -x ".venv/bin/python" ]; then
        "$python_cmd" -m venv .venv
    fi

    ./.venv/bin/python -m pip install --no-cache-dir -r requirements.txt
}

main() {
    install_system_deps
    install_rust
    load_rust_env

    if ! need_cmd cargo; then
        echo "cargo not found after rustup installation" >&2
        exit 1
    fi

    REPO_DIR="$(prepare_repo)"
    cd "$REPO_DIR"

    install_python_deps
    cargo build --release

    cat <<EOF
Incr setup complete.
Repository: $REPO_DIR
Python: $REPO_DIR/.venv/bin/python
Binary: $REPO_DIR/target/release/incr
EOF
}

main "$@"
