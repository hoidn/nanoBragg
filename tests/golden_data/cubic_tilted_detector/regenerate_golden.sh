#!/bin/bash
# Parameters: cubic cell, tilted detector with rotations
# This script regenerates the golden test data for the cubic_tilted_detector test case

# Navigate to the test directory
cd "$(dirname "$0")"

# Run nanoBragg with tilted detector parameters
../../../golden_suite_generator/nanoBragg \
    -lambda 6.2 \
    -N 5 \
    -cell 100 100 100 90 90 90 \
    -default_F 100 \
    -distance 100 \
    -detsize 102.4 \
    -detpixels 1024 \
    -Xbeam 61.2 -Ybeam 61.2 \
    -detector_rotx 5 -detector_roty 3 -detector_rotz 2 \
    -twotheta 15 \
    -oversample 1 \
    -floatfile image.bin \
    > trace.log 2>&1