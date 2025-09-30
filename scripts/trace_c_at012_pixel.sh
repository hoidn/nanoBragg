#!/bin/bash
# Generate C trace for AT-PARALLEL-012 triclinic case at pixel (368, 262)
# This pixel is the strongest peak identified in Attempt #9 diagnostics

set -e

PIXEL_F=262
PIXEL_S=368

echo "Generating C trace for AT-PARALLEL-012 at pixel (fpixel=$PIXEL_F, spixel=$PIXEL_S)..."

# Run C binary with trace flags
./golden_suite_generator/nanoBragg \
  -misset -89.968546 -31.328953 177.753396 \
  -cell 70 80 90 75 85 95 \
  -default_F 100 \
  -N 5 \
  -lambda 1.0 \
  -detpixels 512 \
  -pixel 0.1 \
  -distance 100 \
  -trace_pixel $PIXEL_F $PIXEL_S \
  -floatfile /tmp/at012_c_trace.bin \
  2>&1 | tee reports/2025-09-29-debug-traces-012/c_trace_pixel_${PIXEL_S}_${PIXEL_F}.log

echo ""
echo "C trace saved to: reports/2025-09-29-debug-traces-012/c_trace_pixel_${PIXEL_S}_${PIXEL_F}.log"
echo "Output image: /tmp/at012_c_trace.bin"