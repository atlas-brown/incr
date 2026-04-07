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
bash ./evaluation/war-and-peace/without_incr.sh > baseline.txt
bash ./evaluation/war-and-peace/with_incr.sh > incr.txt
diff -u baseline.txt incr.txt
```

`diff` should print nothing. The first `with_incr.sh` run is a cold start; run it again to see cached replay. Clean up with `bash ./evaluation/war-and-peace/clean.sh`.