#!/bin/bash
# Phase L2b PyTorch Trace Execution Script
#
# Runs the PyTorch CLI with the supervisor command parameters and extracts scaling output.
# This is simpler than building a custom harness since we only need to capture the scaling values.

set -e

# Required environment
export KMP_DUPLICATE_LIB_OK=TRUE

# Output file for trace
TRACE_OUT="reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log"

# Run PyTorch simulation with supervisor command (no noise, float output to temp file)
# Match the supervisor command from phase_i/supervisor_command/README.md
env PYTHONPATH=src python -m nanobrag_torch \
  -mat A.mat \
  -floatfile /tmp/pytorch_trace_img.bin \
  -hkl scaled.hkl \
  -nonoise \
  -nointerpolate \
  -oversample 1 \
  -exposure 1 \
  -flux 1e18 \
  -beamsize 1.0 \
  -spindle_axis -1 0 0 \
  -Xbeam 217.742295 \
  -Ybeam 213.907080 \
  -distance 231.274660 \
  -lambda 0.976800 \
  -pixel 0.172 \
  -detpixels_x 2463 \
  -detpixels_y 2527 \
  -odet_vector -0.000088 0.004914 -0.999988 \
  -sdet_vector -0.005998 -0.999970 -0.004913 \
  -fdet_vector 0.999982 -0.005998 -0.000118 \
  -pix0_vector_mm -216.336293 215.205512 -230.200866 \
  -beam_vector 0.00051387949 0.0 -0.99999986 \
  -Na 36 \
  -Nb 47 \
  -Nc 29 \
  -osc 0.1 \
  -phi 0 \
  -phisteps 10 \
  -detector_rotx 0 \
  -detector_roty 0 \
  -detector_rotz 0 \
  -twotheta 0 \
  2>&1 | tee "$TRACE_OUT"

echo "PyTorch trace captured to $TRACE_OUT"

# Extract pixel (685, 1039) intensity for verification
# (We'd need to add trace instrumentation to the simulator itself to extract
# the intermediate scaling values I_before_scaling, fluence, etc.)
