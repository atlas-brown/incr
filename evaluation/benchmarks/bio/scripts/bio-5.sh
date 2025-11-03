#!/bin/bash

mkdir -p "$OUT"

echo -e "sample\treads" > "${OUT}/read_counts.tsv"

cat "$IN_NAME" | while read pop sample; do
  [ -z "$pop" ] || [ -z "$sample" ] && continue
  echo "Processing $sample..."
  samtools view -H "${IN}/${sample}.bam" \
    | sed -e 's/SN:\([0-9XY]\)/SN:chr\1/' -e 's/SN:MT/SN:chrM/' \
    | samtools reheader - "${IN}/${sample}.bam" > "${OUT}/${sample}_corrected.bam"
  samtools index -b "${OUT}/${sample}_corrected.bam"

  for chr in $(cut -f2 Gene_locs.txt | sort -u); do
    samtools view -b "${OUT}/${sample}_corrected.bam" chr"$chr" > "${OUT}/${pop}_${sample}_${chr}.bam"
    samtools index -b "${OUT}/${pop}_${sample}_${chr}.bam"
  done

  reads=$(samtools idxstats "${OUT}/${sample}_corrected.bam" | awk '{sum+=$3} END {print sum}')
  echo -e "$sample\t$reads" >> "${OUT}/read_counts.tsv"
done
