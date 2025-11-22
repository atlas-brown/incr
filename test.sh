cargo build --release
rm -rf cache
cat README.md | ./target/release/incr tr "[:lower:]" "[:upper:]" > out.txt