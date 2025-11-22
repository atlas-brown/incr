cargo build --release
rm -rf cache
cat evaluation/war-and-peace/book_large.txt | time ./target/release/incr tr "[:lower:]" "[:upper:]" > out.txt