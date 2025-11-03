#!/bin/bash

mkdir -p "$OUT"

sample="HG01941"

samtools view -H "${IN}/${sample}.bam" \
  | sed -e 's/SN:\([0-9XY]\)/SN:chr\1/' -e 's/SN:MT/SN:chrM/' \
  | samtools reheader - "${IN}/${sample}.bam" > "${OUT}/${sample}_corrected.bam"

samtools index -b "${OUT}/${sample}_corrected.bam"
