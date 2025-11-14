rm -rf cache
cat README.md | cargo run tr "[:lower:]" "[:upper:]"