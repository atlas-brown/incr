script_name=$(mktemp script_XXXXX.incr.sh)
python3 ./evaluation/insert.py "$1" > "$script_name"
chmod 755 "$script_name"
. "$script_name"