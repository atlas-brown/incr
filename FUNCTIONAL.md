## Install

```sh
sudo apt update && sudo apt upgrade
sudo apt install mergerfs strace python3-pip
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
pip3 install --no-cache-dir -r requirements.txt
cargo build --release
```

## Run

Verify the install with the war-and-peace word-frequency pipeline:

```sh
bash ./evaluation/war-and-peace/test.sh
```

This runs the baseline pipeline, then Incr twice, and checks that both Incr outputs match the baseline. Clean up with `bash ./evaluation/war-and-peace/clean.sh`.
