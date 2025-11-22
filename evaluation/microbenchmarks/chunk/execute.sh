# sudo rm -rf "../../../cache"
sleep 0.01
time ./scripts/chunk.sh > out.txt
sha256sum out.txt
rm out.txt