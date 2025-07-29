#!/bin/bash
# Script to regenerate triclinic P1 golden test data
# Created: 2025-07-29

# Set environment variable for PyTorch compatibility
export KMP_DUPLICATE_LIB_OK=TRUE

# Change to repository root (3 directories up from this script)
cd "$(dirname "$0")/../../.."

# Define parameters
MISSET_ANGLES="-89.968546 -31.328953 177.753396"
CELL_PARAMS="70 80 90 75 85 95"
DEFAULT_F=100
N_CELLS=5
LAMBDA=1.0
DETPIXELS=512

# Generate golden image
echo "Generating triclinic P1 golden image..."
./nanoBragg \
  -misset $MISSET_ANGLES \
  -cell $CELL_PARAMS \
  -default_F $DEFAULT_F \
  -N $N_CELLS \
  -lambda $LAMBDA \
  -detpixels $DETPIXELS \
  -floatfile tests/golden_data/triclinic_P1/image.bin

# Generate trace log
echo "Generating triclinic P1 trace log..."
./nanoBragg \
  -misset $MISSET_ANGLES \
  -cell $CELL_PARAMS \
  -default_F $DEFAULT_F \
  -N $N_CELLS \
  -lambda $LAMBDA \
  -detpixels $DETPIXELS \
  -floatfile tests/golden_data/triclinic_P1/image_trace.bin \
  > tests/golden_data/triclinic_P1/trace.log 2>&1

echo "Golden data generation complete!"
echo "Generated files:"
echo "  - tests/golden_data/triclinic_P1/image.bin"
echo "  - tests/golden_data/triclinic_P1/trace.log"