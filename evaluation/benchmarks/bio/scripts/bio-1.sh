#!/bin/bash

mkdir -p "$OUT"
read -r _ sample < "$IN_NAME"
[ -n "$sample" ] || { echo "No sample in $IN_NAME" >&2; exit 1; }
samtools view -H "${IN}/${sample}.bam" | sed -e 's/SN:\([0-9XY]\)/SN:chr\1/' -e 's/SN:MT/SN:chrM/' | samtools reheader - "${IN}/${sample}.bam" | dd of="${OUT}/${sample}_corrected.bam" status=none
samtools index -b "${OUT}/${sample}_corrected.bam"
