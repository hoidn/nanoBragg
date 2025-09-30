#!/bin/bash
# Generate C trace for AT-PARALLEL-006 dist-50mm case with polarization instrumentation

set -e

C_BIN=${NB_C_BIN:-./golden_suite_generator/nanoBragg}

echo "Running C binary for AT-PARALLEL-006 dist-50mm-lambda-1.0..."
$C_BIN \
  -default_F 100 \
  -cell 100 100 100 90 90 90 \
  -pixel 0.1 \
  -detpixels 256 \
  -mosflm \
  -N 1 \
  -seed 1 \
  -distance 50 \
  -lambda 1.0 \
  -floatfile /tmp/at006_c.bin \
  > /tmp/at006_c_output.log 2>&1

echo "C binary completed. Output in /tmp/at006_c.bin"
echo "Log in /tmp/at006_c_output.log"

# Check if there's any polarization-related output
echo ""
echo "Polarization references:"
grep -i "polar" /tmp/at006_c_output.log || echo "No polarization references found"

echo ""
echo "Oversample references:"
grep -i "oversample" /tmp/at006_c_output.log || echo "No oversample references found"