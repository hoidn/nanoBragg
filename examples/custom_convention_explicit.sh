#!/bin/bash

# Explicit CUSTOM Convention Example
# ===================================
#
# This script demonstrates CORRECT usage of CUSTOM convention with explicit axis definitions.
# This shows how to safely use axis parameters without triggering convention switching bugs.
#
# KEY SAFETY FEATURES:
# 1. Explicit -convention CUSTOM parameter
# 2. All axes explicitly defined and documented
# 3. Coordinate system clearly specified
# 4. No silent convention switching
#
# 🟡 ADVANCED: This requires careful verification of coordinate systems

set -e  # Exit on any error

# Validate before running
echo "🔍 Running startup warnings check..."
if ! python startup_warnings.py -- "$0"; then
    echo "❌ Configuration check failed - aborting"
    exit 1
fi

echo "✅ Configuration validated - proceeding with CUSTOM convention simulation"
echo ""

# =============================================================================
# CUSTOM Convention Parameters
# =============================================================================

# Crystal parameters
LAMBDA=6.2                    # X-ray wavelength in Angstroms
CELL="100 100 100 90 90 90"  # Unit cell: a b c alpha beta gamma  
N=5                           # Crystal size in unit cells (5x5x5)
DEFAULT_F=100                 # Default structure factor magnitude

# Detector geometry  
DISTANCE=100                  # Detector distance in mm
DETPIXELS=1024               # Detector size (1024x1024 pixels)

# Beam center (for CUSTOM convention - no automatic offset)
XBEAM=512.0                  # X beam center (pixels) - no automatic 0.5 offset
YBEAM=512.0                  # Y beam center (pixels) - no automatic 0.5 offset

# =============================================================================
# EXPLICIT CUSTOM Convention Setup
# =============================================================================
# WARNING: CUSTOM convention requires explicit definition of ALL axes
# Make sure you understand the coordinate system before using this!

# Explicitly specify CUSTOM convention (CRITICAL!)
CONVENTION="CUSTOM"

# Define coordinate system axes explicitly
# These define the lab coordinate system - verify they match your setup!
SPINDLE_AXIS="0 1 0"         # Spindle (phi) rotation axis: Y-axis (vertical)
TWOTHETA_AXIS="0 1 0"        # Two-theta rotation axis: Y-axis (vertical)
VERT_AXIS="0 1 0"           # Vertical axis reference: Y-axis

# Detector rotations in CUSTOM coordinate system
DETECTOR_ROTX=5              # Rotation around X-axis  
DETECTOR_ROTY=3              # Rotation around Y-axis
DETECTOR_ROTZ=2              # Rotation around Z-axis
TWOTHETA=15                  # Two-theta rotation around specified axis

# =============================================================================
# Output Configuration
# =============================================================================

OUTPUT_DIR="custom_convention_output"
mkdir -p "$OUTPUT_DIR"

FLOAT_FILE="$OUTPUT_DIR/custom_explicit.bin"      # Raw float intensities
SMV_FILE="$OUTPUT_DIR/custom_explicit.img"        # SMV format image
NOISE_FILE="$OUTPUT_DIR/custom_explicit_noise.img" # With Poisson noise

# =============================================================================
# Execute nanoBragg with EXPLICIT CUSTOM Convention
# =============================================================================

echo "🚀 Running nanoBragg with EXPLICIT CUSTOM convention configuration..."
echo ""
echo "⚠️  CUSTOM CONVENTION ACTIVE - Coordinate system:"
echo "  Convention: $CONVENTION (EXPLICITLY SET)"
echo "  Spindle axis: $SPINDLE_AXIS"
echo "  Twotheta axis: $TWOTHETA_AXIS"  
echo "  Vertical axis: $VERT_AXIS"
echo ""
echo "Simulation parameters:"
echo "  Lambda: $LAMBDA Å"
echo "  Cell: $CELL"
echo "  Crystal size: ${N}x${N}x${N} unit cells"
echo "  Detector: ${DETPIXELS}x${DETPIXELS} pixels at $DISTANCE mm"
echo "  Beam center: ($XBEAM, $YBEAM) pixels (no MOSFLM offset)"
echo "  Rotations: rotx=$DETECTOR_ROTX°, roty=$DETECTOR_ROTY°, rotz=$DETECTOR_ROTZ°"
echo "  Twotheta: $TWOTHETA° (around custom axis: $TWOTHETA_AXIS)"
echo ""

# The nanoBragg command with EXPLICIT CUSTOM convention
# NOTE: Order matters - convention must be specified before axis parameters
./nanoBragg \
    -convention $CONVENTION \
    -spindle_axis $SPINDLE_AXIS \
    -twotheta_axis $TWOTHETA_AXIS \
    -vert_axis $VERT_AXIS \
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
echo "✅ CUSTOM convention simulation completed!"

# =============================================================================
# Critical Validation for CUSTOM Convention
# =============================================================================

echo ""
echo "🔬 CUSTOM Convention Validation (CRITICAL):"

# Check output files exist
for file in "$FLOAT_FILE" "$SMV_FILE" "$NOISE_FILE"; do
    if [[ -f "$file" ]]; then
        size=$(du -h "$file" | cut -f1)
        echo "  ✓ $file ($size)"
    else
        echo "  ❌ Missing: $file"
    fi
done

# Detailed validation for CUSTOM convention
echo ""
echo "📊 CUSTOM Convention Analysis:"
if command -v python3 &> /dev/null; then
    python3 << EOF
import struct
import os
import numpy as np

# Read and analyze the float file
float_file = "$FLOAT_FILE"
if os.path.exists(float_file):
    with open(float_file, 'rb') as f:
        data = f.read()
    
    num_pixels = len(data) // 4
    expected_pixels = $DETPIXELS * $DETPIXELS
    
    print(f"  Pixels: {num_pixels:,} (expected: {expected_pixels:,})")
    
    # Convert to numpy array for analysis
    if num_pixels == expected_pixels:
        intensities = np.frombuffer(data, dtype=np.float32)
        intensities = intensities.reshape(($DETPIXELS, $DETPIXELS))
        
        print(f"  Shape: {intensities.shape}")
        print(f"  Min intensity: {intensities.min():.3f}")
        print(f"  Max intensity: {intensities.max():.3f}")
        print(f"  Mean intensity: {intensities.mean():.3f}")
        print(f"  Non-zero pixels: {np.count_nonzero(intensities):,}/{num_pixels:,}")
        
        # Check for reasonable intensity distribution
        if intensities.max() > 0 and np.count_nonzero(intensities) > 100:
            print("  ✓ Intensity distribution looks reasonable")
        else:
            print("  ⚠️  Unusual intensity distribution - verify coordinate system")
    else:
        print("  ❌ Pixel count mismatch - file may be corrupted")
else:
    print(f"  ❌ Cannot analyze: {float_file} not found")
EOF
fi

# =============================================================================
# CRITICAL: Coordinate System Verification
# =============================================================================

echo ""
echo "⚠️  CRITICAL CUSTOM Convention Checks:"
echo ""
echo "1. 🧭 Coordinate System Verification:"
echo "   • Spindle axis: $SPINDLE_AXIS"
echo "     ↳ This is the phi rotation axis - verify it matches your goniometer"
echo "   • Twotheta axis: $TWOTHETA_AXIS" 
echo "     ↳ This is the detector swing axis - verify direction"
echo "   • Vertical axis: $VERT_AXIS"
echo "     ↳ This defines 'up' in your lab frame"
echo ""

echo "2. 🔄 Rotation Verification:"
echo "   • All rotations are applied in CUSTOM coordinate system"
echo "   • Verify detector_rotx/roty/rotz match your intended geometry"
echo "   • Twotheta rotation uses axis: $TWOTHETA_AXIS"
echo ""

echo "3. 📐 Beam Center Verification:" 
echo "   • CUSTOM convention: NO automatic 0.5 pixel offset"
echo "   • Beam center: ($XBEAM, $YBEAM) is exact pixel coordinates"
echo "   • Compare with MOSFLM results - may differ by 0.5 pixels"
echo ""

# =============================================================================
# Comparison with MOSFLM Convention
# =============================================================================

echo "🔍 Comparison with MOSFLM Convention:"
echo ""
echo "To verify your CUSTOM convention is equivalent to MOSFLM:"
echo ""
echo "1. Run equivalent MOSFLM simulation:"
echo "   bash examples/safe_mosflm_rotation.sh"
echo ""
echo "2. Compare results:"
echo "   python << 'EOF'"
echo "import numpy as np"
echo ""
echo "# Load both images"
echo "custom = np.fromfile('$FLOAT_FILE', dtype=np.float32).reshape(($DETPIXELS, $DETPIXELS))"
echo "mosflm = np.fromfile('safe_mosflm_output/mosflm_tilted.bin', dtype=np.float32).reshape(($DETPIXELS, $DETPIXELS))"
echo ""
echo "# Calculate correlation"
echo "correlation = np.corrcoef(custom.flatten(), mosflm.flatten())[0, 1]"
echo "print(f'CUSTOM vs MOSFLM correlation: {correlation:.6f}')"
echo ""
echo "if correlation > 0.999:"
echo "    print('✅ CUSTOM convention matches MOSFLM - coordinate systems equivalent')"
echo "elif correlation > 0.9:"
echo "    print('⚠️  Good correlation but not perfect - check axis definitions')"
echo "else:"
echo "    print('❌ Poor correlation - coordinate systems are different!')"
echo "EOF"
echo ""

# =============================================================================
# Documentation and Warnings
# =============================================================================

echo "📝 CUSTOM Convention Usage Notes:"
echo ""
echo "✅ This configuration is SAFE because:"
echo "  • Explicitly specifies -convention CUSTOM"
echo "  • All axes are explicitly defined"
echo "  • No silent convention switching"
echo "  • All parameters are documented"
echo ""

echo "⚠️  CUSTOM Convention Warnings:"
echo "  • Requires deep understanding of coordinate systems"
echo "  • Results may differ from MOSFLM/XDS conventions"
echo "  • Manual verification of all axis definitions required"
echo "  • Beam center calculations are different (no auto-offset)"
echo ""

echo "🚫 Do NOT use CUSTOM convention if:"
echo "  • You're not sure about coordinate system definitions"
echo "  • You want results identical to MOSFLM/XDS"
echo "  • You're porting from existing MOSFLM/XDS workflows"
echo ""

echo "🔗 For safer alternatives:"
echo "  • examples/safe_mosflm_rotation.sh - MOSFLM convention (recommended)"
echo "  • Use -convention XDS for XDS-style coordinate systems"
echo ""

echo "🎯 CUSTOM convention simulation completed!"
echo "   Remember to validate results against known references!"

# =============================================================================
# Expert Notes
# =============================================================================

# For crystallography experts:
#
# CUSTOM Convention allows you to define:
# - Arbitrary spindle (phi) rotation axis
# - Arbitrary twotheta (detector swing) axis  
# - Arbitrary vertical reference axis
#
# This is useful for:
# - Non-standard goniometer geometries
# - Special experimental setups
# - Matching other simulation software conventions
#
# However, it requires careful validation:
# - All axes must be unit vectors
# - Coordinate system must be right-handed
# - All parameters must be consistent with chosen axes
# - Results should be validated against known references
#
# Most users should stick with MOSFLM or XDS conventions unless
# they have specific requirements for custom coordinate systems.