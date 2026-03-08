# Same as with_cache.sh but uses observe for tracing (faster).
# Run from incr/: bash evaluation/war-and-peace/with_cache_observe.sh
INCR="./target/release/incr"
TRY="./src/scripts/try.sh"
CACHE="/tmp/cache_wp_observe"
OBSERVE="../observe/target/release/observe"

$INCR -t $TRY -c $CACHE --observe $OBSERVE -- cat ./evaluation/war-and-peace/book-large.txt | \
$INCR -t $TRY -c $CACHE --observe $OBSERVE -- tr "[:upper:]" "[:lower:]" | \
$INCR -t $TRY -c $CACHE --observe $OBSERVE -- tr -s "[:space:]" "\n" | \
$INCR -t $TRY -c $CACHE --observe $OBSERVE -- sort | \
$INCR -t $TRY -c $CACHE --observe $OBSERVE -- uniq -c | \
$INCR -t $TRY -c $CACHE --observe $OBSERVE -- sort -nr
