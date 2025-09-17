#!/bin/bash
# Build and run script for enhanced C tracing
# 
# This script:
# 1. Applies enhanced tracing to existing nanoBragg.c infrastructure
# 2. Compiles with TRACING=1 flag enabled
# 3. Runs with exact parameters matching Python test
# 4. Captures comprehensive trace output to c_trace.log

set -e  # Exit on any error

# Configuration - exact parameters from the tilted detector test case
LAMBDA=6.2
N=5
CELL="100 100 100 90 90 90"
DEFAULT_F=100
DISTANCE=100
DETPIXELS=1024
XBEAM=51.2
YBEAM=51.2
DETECTOR_ROTX=5
DETECTOR_ROTY=3
DETECTOR_ROTZ=2
DETECTOR_TWOTHETA=20
TARGET_SPIXEL=512
TARGET_FPIXEL=512

echo "============================================================"
echo "C INSTRUMENTATION TRACE GENERATION"
echo "============================================================"
echo "Target pixel: ($TARGET_SPIXEL, $TARGET_FPIXEL)"
echo "Configuration: rotx=${DETECTOR_ROTX}°, roty=${DETECTOR_ROTY}°, rotz=${DETECTOR_ROTZ}°, twotheta=${DETECTOR_TWOTHETA}°"
echo "Pivot mode: SAMPLE (automatic when twotheta != 0)"
echo ""

# Navigate to golden suite generator directory
cd golden_suite_generator

# Backup original file if not already backed up
if [ ! -f nanoBragg.c.orig ]; then
    echo "Creating backup of original nanoBragg.c..."
    cp nanoBragg.c nanoBragg.c.orig
fi

# Apply the simple tracing using Python script
echo "Applying simple tracing enhancements..."
cd ..
if ! python3 simple_c_tracing.py; then
    echo "Error: Failed to apply simple tracing. Exiting."
    exit 1
else
    echo "Simple tracing applied successfully."
    cd golden_suite_generator
fi

# Compile the enhanced version
echo "Compiling enhanced nanoBragg with tracing..."
# Try with OpenMP first, fall back to no OpenMP if needed
if gcc -O2 -lm -fno-fast-math -ffp-contract=off -DTRACING=1 -fopenmp -o nanoBragg_trace nanoBragg.c 2>/dev/null; then
    echo "Compiled with OpenMP support and TRACING enabled"
else
    echo "OpenMP not available, compiling without it..."
    if gcc -O2 -lm -fno-fast-math -ffp-contract=off -DTRACING=1 -o nanoBragg_trace nanoBragg.c; then
        echo "Compiled successfully with TRACING enabled"
    else
        echo "Error: Compilation failed!"
        exit 1
    fi
fi

echo "Compilation successful."

# Run the instrumented version with tracing
echo "Running instrumented nanoBragg with pixel tracing..."
echo "Command: ./nanoBragg_trace -lambda $LAMBDA -N $N -cell $CELL -default_F $DEFAULT_F \\"
echo "         -distance $DISTANCE -detpixels $DETPIXELS \\"
echo "         -Xbeam $XBEAM -Ybeam $YBEAM \\"
echo "         -detector_rotx $DETECTOR_ROTX -detector_roty $DETECTOR_ROTY -detector_rotz $DETECTOR_ROTZ \\"
echo "         -detector_twotheta $DETECTOR_TWOTHETA \\"
echo "         -trace_pixel $TARGET_SPIXEL $TARGET_FPIXEL \\"
echo "         -floatfile c_trace_output.bin"
echo ""

# Run and capture both stdout and stderr
./nanoBragg_trace \
    -lambda $LAMBDA \
    -N $N \
    -cell $CELL \
    -default_F $DEFAULT_F \
    -distance $DISTANCE \
    -detpixels $DETPIXELS \
    -Xbeam $XBEAM \
    -Ybeam $YBEAM \
    -detector_rotx $DETECTOR_ROTX \
    -detector_roty $DETECTOR_ROTY \
    -detector_rotz $DETECTOR_ROTZ \
    -detector_twotheta $DETECTOR_TWOTHETA \
    -trace_pixel $TARGET_SPIXEL $TARGET_FPIXEL \
    -floatfile c_trace_output.bin \
    2>&1 | tee ../c_trace_full.log

# Extract just the trace lines for comparison
echo "Extracting trace lines..."
grep "TRACE_C:" ../c_trace_full.log > ../c_trace.log

echo ""
echo "============================================================"
echo "C TRACE GENERATION COMPLETE"
echo "============================================================"
echo "Files generated:"
echo "  c_trace_full.log - Complete output with trace statements"
echo "  c_trace.log      - Extracted trace lines only"
echo "  c_trace_output.bin - Binary diffraction output"
echo ""
echo "To compare with Python trace:"
echo "  1. Run: KMP_DUPLICATE_LIB_OK=TRUE python scripts/trace_pixel_512_512.py > py_trace.log"
echo "  2. Run: python compare_c_python_traces.py"
echo ""

# Return to original directory
cd ..

# Show summary of trace lines
TRACE_COUNT=$(wc -l < c_trace.log)
echo "Generated $TRACE_COUNT trace lines for analysis."

if [ $TRACE_COUNT -eq 0 ]; then
    echo "WARNING: No trace lines generated! Check the C compilation and execution."
    exit 1
fi

echo "First few trace lines:"
head -5 c_trace.log
echo "..."
echo "Last few trace lines:"
tail -5 c_trace.log

echo ""
echo "C trace generation completed successfully!"