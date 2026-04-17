#!/bin/bash
# Min: optional samtools view -s subsample after wget (valid BAM; no dd/head). BIO_MIN_KEEP_FRAC (default 0.5); 1 = full. Seed 42.

cd "$(realpath "$(dirname "$0")")" || exit 1
URL='https://atlas.cs.brown.edu/data'

IN="inputs"
IN_NAME="input.txt"
size="large"
mkdir -p "$IN"
in_dir="$IN/bio-full"
for arg in "$@"; do
    case "$arg" in
        --small)
            IN_NAME="input_small.txt"
            size="medium"
            in_dir="$IN/bio-small"
            ;;
        --min)
            IN_NAME="input_min.txt"
            in_dir="$IN/bio-min"
            size="min"
            ;;
    esac
done

mkdir -p outputs "$in_dir"
cp $IN_NAME "$in_dir"
cp "./Gene_locs.txt" "$in_dir"

if [[ ! -f "$IN_NAME" ]]; then
    echo "Input file '$IN_NAME' not found." >&2
    exit 1
fi

# Min: HG00421 only (same sample as small).
if [[ $size == "min" ]]; then
    sample="HG00421"
    out_file="$in_dir/${sample}.bam"
    if [[ ! -f "$out_file" ]]; then
        tmp_file="${out_file}.tmp"
        link="${URL}/bio/medium/${sample}.bam"
        if wget -O "$tmp_file" --no-check-certificate "$link"; then
            mv "$tmp_file" "$out_file"
            keep="${BIO_MIN_KEEP_FRAC:-0.5}"
            if [[ "$keep" != "1" && "$keep" != "1.0" ]] && command -v samtools >/dev/null 2>&1; then
                s_arg="42.${keep#*.}"
                shrink_tmp="${out_file}.subsampled"
                if samtools view -b -s "$s_arg" -o "$shrink_tmp" "$out_file" 2>/dev/null && [[ -s "$shrink_tmp" ]]; then
                    mv "$shrink_tmp" "$out_file"
                else
                    rm -f "$shrink_tmp"
                fi
            fi
        else
            echo "Failed to download: $link" >&2
            rm -f "$tmp_file"
            exit 1
        fi
    fi
    exit 0
fi

while IFS= read -r s_line; do
    sample=$(echo "$s_line" | cut -d ' ' -f 2)

    out_file="$in_dir/$sample.bam"

    if [[ ! -f "$out_file" ]]; then
        tmp_file="${out_file}.tmp"
        link="${URL}/bio/${size}/${sample}.bam"
        if wget -O "$tmp_file" --no-check-certificate "$link"; then
            mv "$tmp_file" "$out_file"
        else
            echo "Failed to download: $link" >&2
            rm -f "$tmp_file"
        fi
    fi
done < "$IN_NAME"
