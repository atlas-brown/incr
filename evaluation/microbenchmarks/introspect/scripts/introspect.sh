cat "$IN" | \
tr 'a-zA-Z' 'a-zA-Z' | \
sed '' | \
awk '{for(i=0;i<100;i++); print $0}' | \
grep -a "" | \
cat | \
tail -n +1 | \
cut -b 1- | \
sed -e 's/^//' | \
awk '1' | \
tr '0-9' '0-9' | \
cat | \
grep -a -E "" | \
sed -n 'p' | \
awk '//' | \
tail -n +1 | \
cut -b 1- | \
sed -e 's/$//' | \
cat | \
awk '{if(1)print}'