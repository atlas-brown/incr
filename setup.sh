#!/bin/bash

cd $(dirname $0)

# install Rust if not installed
if ! command -v cargo &> /dev/null; then
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
fi

# build tee-cache
cd tee-cache || exit
cargo build --release
cd ..