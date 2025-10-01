#!/bin/bash
# Generate C trace for AT-PARALLEL-002 pixel-0.4mm case with polarization instrumentation

set -e

C_BIN=${NB_C_BIN:-./golden_suite_generator/nanoBragg}

echo "Running C binary for AT-PARALLEL-002 pixel-0.4mm..."
$C_BIN \
  -default_F 100 \
  -cell 100 100 100 90 90 90 \
  -lambda 6.2 \
  -N 5 \
  -distance 100 \
  -seed 1 \
  -detpixels 256 \
  -pixel 0.4 \
  -Xbeam 25.6 \
  -Ybeam 25.6 \
  -mosflm \
  -floatfile /tmp/at002_c.bin \
  > /tmp/at002_c_output.log 2>&1

echo "C binary completed. Output in /tmp/at002_c.bin"
echo "Log in /tmp/at002_c_output.log"

# Check if there's any polarization-related output
if grep -i "polar" /tmp/at002_c_output.log; then
    echo "Found polarization references in C output"
else
    echo "No polarization references found in C output"
fi