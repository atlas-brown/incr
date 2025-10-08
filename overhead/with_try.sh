for i in $(seq 10)
do
    mkdir -p "sandbox_$i"
    ./src/try.sh -D "sandbox_$i" echo "hello world!"
    ./src/try.sh commit "sandbox_$i"
    sudo rm -rf "sandbox_$i"
done