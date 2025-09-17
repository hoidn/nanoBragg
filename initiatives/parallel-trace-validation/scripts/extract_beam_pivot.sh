#!/bin/bash
# Extract the BEAM pivot section from nanoBragg.c for instrumentation

# Find the line numbers for the BEAM pivot section
START=$(grep -n "detector_pivot == BEAM" golden_suite_generator/nanoBragg.c | grep -B 2 "pivoting detector around direct beam spot" | head -1 | cut -d: -f1)
END=$(grep -n "pix0_vector\[3\]" golden_suite_generator/nanoBragg.c | grep -A 5 "$START" | tail -1 | cut -d: -f1)

# Add some context
START=$((START - 20))
END=$((END + 20))

echo "Extracting lines $START to $END"
sed -n "${START},${END}p" golden_suite_generator/nanoBragg.c > beam_pivot_section.txt
echo "Saved to beam_pivot_section.txt"