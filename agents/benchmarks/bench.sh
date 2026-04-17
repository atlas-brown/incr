#!/bin/bash
# Performance comparison: incr with strace vs incr with observe
# Run from incr/: bash agents/benchmarks/bench.sh
#
# Cold = cache cleared before EACH run. Warm = cache hits, no clearing.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INCR_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$INCR_ROOT"

INCR="./target/release/incr"
TRY="./src/scripts/try.sh"
OBSERVE="../observe/target/release/observe"
ITERATIONS=5

[ -x "$INCR" ] || { echo "Build incr: cargo build --release"; exit 1; }
[ -x "$OBSERVE" ] || { echo "Build observe: cd ../observe && cargo build --release"; exit 1; }

run_repeat() {
    local cmd="$1" n="$2" clear_cache="$3"
    local start end
    start=$(date +%s.%N)
    for i in $(seq 1 "$n"); do
        case "$clear_cache" in
            strace) rm -rf $CACHE_STRACE 2>/dev/null || true ;;
            observe) rm -rf $CACHE_OBSERVE 2>/dev/null || true ;;
        esac
        eval "$cmd"
    done
    end=$(date +%s.%N)
    echo "scale=4; ($end - $start) / $n" | bc
}

emit() { echo "BENCH:$1:$2:$3"; }

CACHE_STRACE="/tmp/incr_bench_strace_$$"
CACHE_OBSERVE="/tmp/incr_bench_observe_$$"
TESTDIR="/tmp/incr_bench_dir_$$"
mkdir -p "$TESTDIR"
trap "rm -rf $CACHE_STRACE $CACHE_OBSERVE $TESTDIR" EXIT

# Create test files
echo "x" > "$TESTDIR/input.txt"
echo -e "a\nb\nc\nd\ne" > "$TESTDIR/sed.txt"
dd if=/dev/zero of="$TESTDIR/large.bin" bs=1024 count=100 2>/dev/null

echo "=============================================="
echo "incr performance: strace vs observe ($ITERATIONS iter)"
echo "=============================================="

# 1. TraceFile - cat (small)
echo ""; echo "1. cat (small file)"
rm -rf $CACHE_STRACE $CACHE_OBSERVE
t_s=$(run_repeat "echo 'd' | $INCR --try $TRY --cache $CACHE_STRACE cat $TESTDIR/input.txt > /dev/null" $ITERATIONS strace)
t_o=$(run_repeat "echo 'd' | $INCR --try $TRY --cache $CACHE_OBSERVE --observe $OBSERVE cat $TESTDIR/input.txt > /dev/null" $ITERATIONS observe)
echo "   cold: strace ${t_s}s, observe ${t_o}s"; emit "cat_cold" "strace" "$t_s"; emit "cat_cold" "observe" "$t_o"
t_sw=$(run_repeat "echo 'd' | $INCR --try $TRY --cache $CACHE_STRACE cat $TESTDIR/input.txt > /dev/null" $ITERATIONS "")
t_ow=$(run_repeat "echo 'd' | $INCR --try $TRY --cache $CACHE_OBSERVE --observe $OBSERVE cat $TESTDIR/input.txt > /dev/null" $ITERATIONS "")
echo "   warm: strace ${t_sw}s, observe ${t_ow}s"; emit "cat_warm" "strace" "$t_sw"; emit "cat_warm" "observe" "$t_ow"

# 2. TraceFile - cat (larger)
echo ""; echo "2. cat (100KB file)"
rm -rf $CACHE_STRACE $CACHE_OBSERVE
t_s=$(run_repeat "echo '' | $INCR --try $TRY --cache $CACHE_STRACE cat $TESTDIR/large.bin > /dev/null" $ITERATIONS strace)
t_o=$(run_repeat "echo '' | $INCR --try $TRY --cache $CACHE_OBSERVE --observe $OBSERVE cat $TESTDIR/large.bin > /dev/null" $ITERATIONS observe)
echo "   cold: strace ${t_s}s, observe ${t_o}s"; emit "cat_large_cold" "strace" "$t_s"; emit "cat_large_cold" "observe" "$t_o"
t_sw=$(run_repeat "echo '' | $INCR --try $TRY --cache $CACHE_STRACE cat $TESTDIR/large.bin > /dev/null" $ITERATIONS "")
t_ow=$(run_repeat "echo '' | $INCR --try $TRY --cache $CACHE_OBSERVE --observe $OBSERVE cat $TESTDIR/large.bin > /dev/null" $ITERATIONS "")
echo "   warm: strace ${t_sw}s, observe ${t_ow}s"; emit "cat_large_warm" "strace" "$t_sw"; emit "cat_large_warm" "observe" "$t_ow"

# 3. TraceFile - sed
echo ""; echo "3. sed (read-only)"
rm -rf $CACHE_STRACE $CACHE_OBSERVE
t_s=$(run_repeat "echo '' | $INCR --try $TRY --cache $CACHE_STRACE sed 's/a/x/' $TESTDIR/sed.txt > /dev/null" $ITERATIONS strace)
t_o=$(run_repeat "echo '' | $INCR --try $TRY --cache $CACHE_OBSERVE --observe $OBSERVE sed 's/a/x/' $TESTDIR/sed.txt > /dev/null" $ITERATIONS observe)
echo "   cold: strace ${t_s}s, observe ${t_o}s"; emit "sed_cold" "strace" "$t_s"; emit "sed_cold" "observe" "$t_o"
t_sw=$(run_repeat "echo '' | $INCR --try $TRY --cache $CACHE_STRACE sed 's/a/x/' $TESTDIR/sed.txt > /dev/null" $ITERATIONS "")
t_ow=$(run_repeat "echo '' | $INCR --try $TRY --cache $CACHE_OBSERVE --observe $OBSERVE sed 's/a/x/' $TESTDIR/sed.txt > /dev/null" $ITERATIONS "")
echo "   warm: strace ${t_sw}s, observe ${t_ow}s"; emit "sed_warm" "strace" "$t_sw"; emit "sed_warm" "observe" "$t_ow"

# 4. Write - echo to file
echo ""; echo "4. write (echo > file)"
rm -rf $CACHE_STRACE $CACHE_OBSERVE
rm -f "$TESTDIR/out_s.txt" "$TESTDIR/out_o.txt"
t_s=$(run_repeat "echo '' | $INCR --try $TRY --cache $CACHE_STRACE bash -c \"echo x > $TESTDIR/out_s.txt\"" $ITERATIONS strace)
t_o=$(run_repeat "echo '' | $INCR --try $TRY --cache $CACHE_OBSERVE --observe $OBSERVE bash -c \"echo x > $TESTDIR/out_o.txt\"" $ITERATIONS observe)
echo "   cold: strace ${t_s}s, observe ${t_o}s"; emit "write_cold" "strace" "$t_s"; emit "write_cold" "observe" "$t_o"
t_sw=$(run_repeat "echo '' | $INCR --try $TRY --cache $CACHE_STRACE bash -c \"echo x > $TESTDIR/out_s.txt\"" $ITERATIONS "")
t_ow=$(run_repeat "echo '' | $INCR --try $TRY --cache $CACHE_OBSERVE --observe $OBSERVE bash -c \"echo x > $TESTDIR/out_o.txt\"" $ITERATIONS "")
echo "   warm: strace ${t_sw}s, observe ${t_ow}s"; emit "write_warm" "strace" "$t_sw"; emit "write_warm" "observe" "$t_ow"

# 5. cp (read+write)
echo ""; echo "5. cp (read+write)"
rm -rf $CACHE_STRACE $CACHE_OBSERVE
echo "src" > "$TESTDIR/cp_src.txt"
rm -f "$TESTDIR/cp_dest_s.txt" "$TESTDIR/cp_dest_o.txt"
t_s=$(run_repeat "echo '' | $INCR --try $TRY --cache $CACHE_STRACE cp $TESTDIR/cp_src.txt $TESTDIR/cp_dest_s.txt" $ITERATIONS strace)
t_o=$(run_repeat "echo '' | $INCR --try $TRY --cache $CACHE_OBSERVE --observe $OBSERVE cp $TESTDIR/cp_src.txt $TESTDIR/cp_dest_o.txt" $ITERATIONS observe)
echo "   cold: strace ${t_s}s, observe ${t_o}s"; emit "cp_cold" "strace" "$t_s"; emit "cp_cold" "observe" "$t_o"
t_sw=$(run_repeat "echo '' | $INCR --try $TRY --cache $CACHE_STRACE cp $TESTDIR/cp_src.txt $TESTDIR/cp_dest_s.txt" $ITERATIONS "")
t_ow=$(run_repeat "echo '' | $INCR --try $TRY --cache $CACHE_OBSERVE --observe $OBSERVE cp $TESTDIR/cp_src.txt $TESTDIR/cp_dest_o.txt" $ITERATIONS "")
echo "   warm: strace ${t_sw}s, observe ${t_ow}s"; emit "cp_warm" "strace" "$t_sw"; emit "cp_warm" "observe" "$t_ow"

# 6. grep (pure)
echo ""; echo "6. grep (pure)"
rm -rf $CACHE_STRACE $CACHE_OBSERVE
t_s=$(run_repeat "echo -e 'a\nb\nc' | $INCR --try $TRY --cache $CACHE_STRACE grep -q b $TESTDIR/sed.txt" $ITERATIONS strace)
t_o=$(run_repeat "echo -e 'a\nb\nc' | $INCR --try $TRY --cache $CACHE_OBSERVE --observe $OBSERVE grep -q b $TESTDIR/sed.txt" $ITERATIONS observe)
echo "   cold: strace ${t_s}s, observe ${t_o}s"; emit "grep_cold" "strace" "$t_s"; emit "grep_cold" "observe" "$t_o"

# 7. Multi-command script: cp -> sed -> cat (read chain)
echo ""; echo "7. script: cp | sed | cat (3 commands)"
rm -rf $CACHE_STRACE $CACHE_OBSERVE
rm -f "$TESTDIR/chain_b.txt" "$TESTDIR/chain_c.txt"
t_s=$(run_repeat "echo '' | $INCR --try $TRY --cache $CACHE_STRACE bash -c \"cp $TESTDIR/sed.txt $TESTDIR/chain_b.txt && sed 's/a/x/' $TESTDIR/chain_b.txt > $TESTDIR/chain_c.txt && cat $TESTDIR/chain_c.txt > /dev/null\"" $ITERATIONS strace)
t_o=$(run_repeat "echo '' | $INCR --try $TRY --cache $CACHE_OBSERVE --observe $OBSERVE bash -c \"cp $TESTDIR/sed.txt $TESTDIR/chain_b.txt && sed 's/a/x/' $TESTDIR/chain_b.txt > $TESTDIR/chain_c.txt && cat $TESTDIR/chain_c.txt > /dev/null\"" $ITERATIONS observe)
echo "   cold: strace ${t_s}s, observe ${t_o}s"; emit "script_chain_cold" "strace" "$t_s"; emit "script_chain_cold" "observe" "$t_o"
t_sw=$(run_repeat "echo '' | $INCR --try $TRY --cache $CACHE_STRACE bash -c \"cp $TESTDIR/sed.txt $TESTDIR/chain_b.txt && sed 's/a/x/' $TESTDIR/chain_b.txt > $TESTDIR/chain_c.txt && cat $TESTDIR/chain_c.txt > /dev/null\"" $ITERATIONS "")
t_ow=$(run_repeat "echo '' | $INCR --try $TRY --cache $CACHE_OBSERVE --observe $OBSERVE bash -c \"cp $TESTDIR/sed.txt $TESTDIR/chain_b.txt && sed 's/a/x/' $TESTDIR/chain_b.txt > $TESTDIR/chain_c.txt && cat $TESTDIR/chain_c.txt > /dev/null\"" $ITERATIONS "")
echo "   warm: strace ${t_sw}s, observe ${t_ow}s"; emit "script_chain_warm" "strace" "$t_sw"; emit "script_chain_warm" "observe" "$t_ow"

# 8. Multi-command script: echo + cp + grep (writes then read)
echo ""; echo "8. script: echo | cp | grep (3 commands)"
rm -rf $CACHE_STRACE $CACHE_OBSERVE
rm -f "$TESTDIR/script_f1.txt" "$TESTDIR/script_f2.txt"
t_s=$(run_repeat "echo '' | $INCR --try $TRY --cache $CACHE_STRACE bash -c \"echo hello > $TESTDIR/script_f1.txt && cp $TESTDIR/script_f1.txt $TESTDIR/script_f2.txt && grep -q hello $TESTDIR/script_f2.txt\"" $ITERATIONS strace)
t_o=$(run_repeat "echo '' | $INCR --try $TRY --cache $CACHE_OBSERVE --observe $OBSERVE bash -c \"echo hello > $TESTDIR/script_f1.txt && cp $TESTDIR/script_f1.txt $TESTDIR/script_f2.txt && grep -q hello $TESTDIR/script_f2.txt\"" $ITERATIONS observe)
echo "   cold: strace ${t_s}s, observe ${t_o}s"; emit "script_write_cold" "strace" "$t_s"; emit "script_write_cold" "observe" "$t_o"
t_sw=$(run_repeat "echo '' | $INCR --try $TRY --cache $CACHE_STRACE bash -c \"echo hello > $TESTDIR/script_f1.txt && cp $TESTDIR/script_f1.txt $TESTDIR/script_f2.txt && grep -q hello $TESTDIR/script_f2.txt\"" $ITERATIONS "")
t_ow=$(run_repeat "echo '' | $INCR --try $TRY --cache $CACHE_OBSERVE --observe $OBSERVE bash -c \"echo hello > $TESTDIR/script_f1.txt && cp $TESTDIR/script_f1.txt $TESTDIR/script_f2.txt && grep -q hello $TESTDIR/script_f2.txt\"" $ITERATIONS "")
echo "   warm: strace ${t_sw}s, observe ${t_ow}s"; emit "script_write_warm" "strace" "$t_sw"; emit "script_write_warm" "observe" "$t_ow"

# 9. Batch executor - write
echo ""; echo "9. batch write"
rm -rf $CACHE_STRACE $CACHE_OBSERVE
rm -f "$TESTDIR/batch_s.txt" "$TESTDIR/batch_o.txt"
t_s=$(run_repeat "echo '' | $INCR -b --try $TRY --cache $CACHE_STRACE bash -c \"echo batch > $TESTDIR/batch_s.txt\"" $ITERATIONS strace)
t_o=$(run_repeat "echo '' | $INCR -b --try $TRY --cache $CACHE_OBSERVE --observe $OBSERVE bash -c \"echo batch > $TESTDIR/batch_o.txt\"" $ITERATIONS observe)
echo "   cold: strace ${t_s}s, observe ${t_o}s"; emit "batch_write_cold" "strace" "$t_s"; emit "batch_write_cold" "observe" "$t_o"
t_sw=$(run_repeat "echo '' | $INCR -b --try $TRY --cache $CACHE_STRACE bash -c \"echo batch > $TESTDIR/batch_s.txt\"" $ITERATIONS "")
t_ow=$(run_repeat "echo '' | $INCR -b --try $TRY --cache $CACHE_OBSERVE --observe $OBSERVE bash -c \"echo batch > $TESTDIR/batch_o.txt\"" $ITERATIONS "")
echo "   warm: strace ${t_sw}s, observe ${t_ow}s"; emit "batch_write_warm" "strace" "$t_sw"; emit "batch_write_warm" "observe" "$t_ow"

echo ""; echo "=============================================="; echo "Done"
