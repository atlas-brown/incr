rm -rf sandbox
for i in $(seq 10)
do
    mkdir -p sandbox
    ./src/try.sh -D sandbox echo "hello world!"
    ./src/try.sh commit sandbox
    sudo rm -rf sandbox
done