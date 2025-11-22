# sudo rm -rf "../../../cache"
sleep 1
time ./scripts/chunk.sh > out.txt && sha256sum out.txt && rm out.txt