#!/bin/bash

cd "$(dirname "$0")"/.. || exit 1

IN="$1"
IN_NAME="$2"
OUT="$3"

mkdir -p "${OUT}"

# Rewrote the original `cat | while read` loops as file-redirected reads and
# pre-computed chromosome lists. The original pattern drained the pipe's stdin
# inside the loop body when each inner command (e.g. samtools) consumed it,
# which is the case under incr (whose stream executor hashes stdin). The
# observable behavior on bash is unchanged.
chromosomes=$(cut -f 2 ./Gene_locs.txt | sort -u)
while IFS= read -r s_line; do
    sample=$(echo "$s_line" | cut -d " " -f 2)
    pop=$(echo "$s_line" | cut -d " " -f 1)
    [ -z "$pop" ] || [ -z "$sample" ] && continue

    echo "Processing Sample $sample"
    samtools view -H "${IN}/$sample".bam \
        | sed -e 's/SN:\([0-9XY]\)/SN:chr\1/' -e 's/SN:MT/SN:chrM/' \
        | samtools reheader - "${IN}/$sample".bam > "${OUT}/$sample"_corrected.bam
    samtools index -b "${OUT}/$sample"_corrected.bam

    for chr in $chromosomes; do
        echo "Isolating Chromosome $chr from sample ${OUT}/$sample,  "
        samtools view -b "${OUT}/$sample"_corrected.bam chr"$chr" > "${OUT}/$pop"_"$sample"_"$chr".bam
        echo "Indexing Sample ${pop}_${OUT}/$sample "
        samtools index -b "${OUT}/$pop"_"$sample"_"$chr".bam
    done
done < "${IN_NAME}"
