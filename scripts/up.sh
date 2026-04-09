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
    sudo apt install -y git mergerfs strace python3-pip curl ca-certificates build-essential pkg-config libssl-dev
}

install_rust() {
    if need_cmd cargo; then
        return
    fi

    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
}

load_rust_env() {
    if [ -f "$HOME/.cargo/env" ]; then
        # shellcheck disable=SC1090
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

    pip3 install --no-cache-dir -r requirements.txt
    cargo build --release

    cat <<EOF
Incr setup complete.
Repository: $REPO_DIR
Binary: $REPO_DIR/target/release/incr
EOF
}

main "$@"
