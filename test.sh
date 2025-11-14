rm -rf cache
./target/release/incr python hello.py
# cat README.md | cargo run tr "[:lower:]" "[:upper:]"