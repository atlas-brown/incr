cargo build --release
rm -rf cache
cat evaluation/war-and-peace/book.txt | time ./target/release/incr tr "[:lower:]" "[:upper:]" > out.txt