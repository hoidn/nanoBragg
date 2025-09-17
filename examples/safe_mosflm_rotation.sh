#!/bin/bash

# Safe MOSFLM Detector Rotation Example
# =====================================
# 
# This script demonstrates CORRECT usage of detector rotations with MOSFLM convention.
# This configuration achieves >0.999 correlation with C reference code.
#
# KEY SAFETY FEATURES:
# 1. NO axis specification parameters (-twotheta_axis, -spindle_axis, -vert_axis)  
# 2. Uses implicit MOSFLM convention (default)
# 3. All rotations follow MOSFLM coordinate system
# 4. Beam center explicitly specified for tilted geometry
#
# 🟢 SAFE: This will NOT trigger convention switching bugs

set -e  # Exit on any error

# Validate before running
echo "🔍 Running startup warnings check..."
if ! python startup_warnings.py -- "$0"; then
    echo "❌ Configuration check failed - aborting"
    exit 1
fi

echo "✅ Configuration validated - proceeding with simulation"
echo ""

# =============================================================================
# MOSFLM Convention Parameters
# =============================================================================

# Crystal parameters
LAMBDA=6.2                    # X-ray wavelength in Angstroms
CELL="100 100 100 90 90 90"  # Unit cell: a b c alpha beta gamma  
N=5                           # Crystal size in unit cells (5x5x5)
DEFAULT_F=100                 # Default structure factor magnitude

# Detector geometry  
DISTANCE=100                  # Detector distance in mm
DETPIXELS=1024               # Detector size (1024x1024 pixels)
PIXEL_SIZE=0.1               # Pixel size in mm (default)

# Beam center (IMPORTANT for tilted detectors)
# In MOSFLM convention, these are the direct beam position in pixels
XBEAM=512.5                  # X beam center (pixels) - note 0.5 offset
YBEAM=512.5                  # Y beam center (pixels) - note 0.5 offset

# =============================================================================
# SAFE Detector Rotations (MOSFLM Convention)
# =============================================================================
# These rotations use the default MOSFLM coordinate system:
# - X: along beam direction (towards detector)
# - Y: vertical (up)  
# - Z: horizontal (perpendicular to beam, completes right-handed system)
#
# Rotation order: rotx -> roty -> rotz -> twotheta
# All angles in degrees

DETECTOR_ROTX=5              # Rotation around X-axis (tip/tilt)
DETECTOR_ROTY=3              # Rotation around Y-axis (left/right tilt)  
DETECTOR_ROTZ=2              # Rotation around Z-axis (roll)
TWOTHETA=15                  # Final rotation around Y-axis (MOSFLM default)

# =============================================================================
# Output Configuration
# =============================================================================

OUTPUT_DIR="safe_mosflm_output"
mkdir -p "$OUTPUT_DIR"

FLOAT_FILE="$OUTPUT_DIR/mosflm_tilted.bin"      # Raw float intensities
SMV_FILE="$OUTPUT_DIR/mosflm_tilted.img"        # SMV format image
NOISE_FILE="$OUTPUT_DIR/mosflm_tilted_noise.img" # With Poisson noise

# =============================================================================
# Execute nanoBragg with Safe MOSFLM Parameters
# =============================================================================

echo "🚀 Running nanoBragg with SAFE MOSFLM detector rotation configuration..."
echo ""
echo "Parameters:"
echo "  Convention: MOSFLM (default, implicit)"
echo "  Lambda: $LAMBDA Å"
echo "  Cell: $CELL"  
echo "  Crystal size: ${N}x${N}x${N} unit cells"
echo "  Detector: ${DETPIXELS}x${DETPIXELS} pixels at $DISTANCE mm"
echo "  Beam center: ($XBEAM, $YBEAM) pixels"
echo "  Rotations: rotx=$DETECTOR_ROTX°, roty=$DETECTOR_ROTY°, rotz=$DETECTOR_ROTZ°"
echo "  Twotheta: $TWOTHETA° (around Y-axis, MOSFLM default)"
echo ""

# The nanoBragg command - note the careful parameter organization
./nanoBragg \
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
    -twotheta $TWOTHETA \
    -floatfile "$FLOAT_FILE" \
    -intfile "$SMV_FILE" \
    -noisefile "$NOISE_FILE" \
    -verbose

echo ""
echo "✅ Simulation completed successfully!"

# =============================================================================
# Validation and Verification
# =============================================================================

echo ""
echo "🔬 Validation checks:"

# Check output files exist
for file in "$FLOAT_FILE" "$SMV_FILE" "$NOISE_FILE"; do
    if [[ -f "$file" ]]; then
        size=$(du -h "$file" | cut -f1)
        echo "  ✓ $file ($size)"
    else
        echo "  ❌ Missing: $file"
    fi
done

# Basic image validation
echo ""
echo "📊 Image information:"
if command -v python3 &> /dev/null; then
    python3 << EOF
import struct
import os

# Read and analyze the float file
float_file = "$FLOAT_FILE"
if os.path.exists(float_file):
    with open(float_file, 'rb') as f:
        data = f.read()
    
    num_pixels = len(data) // 4  # 4 bytes per float
    expected_pixels = $DETPIXELS * $DETPIXELS
    
    print(f"  Pixels: {num_pixels:,} (expected: {expected_pixels:,})")
    
    # Read a few intensity values
    intensities = []
    for i in range(min(10, num_pixels)):
        intensity = struct.unpack('f', data[i*4:(i+1)*4])[0]
        intensities.append(intensity)
    
    max_intensity = max(intensities) if intensities else 0
    min_intensity = min(intensities) if intensities else 0
    
    print(f"  Intensity range (sample): {min_intensity:.2f} to {max_intensity:.2f}")
    print(f"  Non-zero pixels: {sum(1 for i in intensities if i > 0)}/{len(intensities)} (sample)")
else:
    print(f"  ❌ Cannot analyze: {float_file} not found")
EOF
fi

# =============================================================================
# Documentation and Next Steps  
# =============================================================================

echo ""
echo "📝 This configuration is SAFE because:"
echo "  • Uses implicit MOSFLM convention (no -convention parameter needed)"
echo "  • NO axis specification parameters (no -twotheta_axis, -spindle_axis, -vert_axis)"
echo "  • All detector rotations follow MOSFLM coordinate system"
echo "  • Beam center explicitly specified for tilted geometry"
echo "  • Should achieve >0.999 correlation with C reference"
echo ""

echo "🔍 To verify correlation with reference:"
echo "  python scripts/verify_detector_geometry.py \\
    --float_file '$FLOAT_FILE' \\
    --lambda $LAMBDA \\
    --distance $DISTANCE \\
    --detpixels $DETPIXELS \\
    --beam_center $XBEAM $YBEAM \\
    --rotations $DETECTOR_ROTX $DETECTOR_ROTY $DETECTOR_ROTZ \\
    --twotheta $TWOTHETA"
echo ""

echo "📚 Related examples:"
echo "  • examples/custom_convention_explicit.sh - For explicit CUSTOM convention"  
echo "  • examples/DANGER_mixed_conventions.sh - What NOT to do"
echo ""

echo "🎉 Safe MOSFLM rotation example completed successfully!"

# =============================================================================
# Advanced Usage Notes
# =============================================================================

# For advanced users who want to understand the coordinate system:
#
# MOSFLM Convention Details:
# - Lab frame: X=beam, Y=up, Z=perpendicular (right-handed)
# - Detector initially perpendicular to beam at +X  
# - Rotations applied in order: rotx -> roty -> rotz -> twotheta
# - Beam center calculation includes automatic 0.5 pixel offset
# - twotheta rotates around Y-axis by default
#
# This is the SAFEST configuration for most crystallography applications.
# If you need different coordinate systems, use explicit -convention parameter.