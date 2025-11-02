input_dir="$IN"
output_dir="$OUT"
input_file="$OUT/all.txt"
find "$input_dir" -type f -exec cat {} + > "$input_file"
freq_out="$output_dir/freq.txt"

# Sort by frequency
tr -sc 'A-Za-z' '\012' < "$input_file" |
    sort | 
    uniq -c | 
    sort -nr > "$freq_out"
