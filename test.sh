cargo build --release
sudo rm -rf cache
cat ./evaluation/war-and-peace/book_large.txt | cargo flamegraph --root --no-inline --release -- -a tr "[:upper:]" "[:lower:]" > out.txt