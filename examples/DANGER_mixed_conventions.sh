#!/bin/bash

# DANGER: Mixed Convention Example - DO NOT USE!
# ==============================================
#
# 🚨 WARNING: This script demonstrates the DANGEROUS parameter combinations
# that cause silent convention switching and correlation bugs.
#
# ❌ THIS WILL FAIL: Correlation with C reference will be <0.9 instead of >0.999
# ❌ THIS LOOKS "ALMOST RIGHT": Results appear reasonable but are scientifically wrong
# ❌ THIS IS THE #1 SOURCE OF BUGS: Silent switching without warnings
#
# 🛑 DO NOT RUN THIS SCRIPT FOR PRODUCTION SIMULATIONS!
#
# This is provided for educational purposes only to show what NOT to do.

set -e  # Exit on any error

# Force validation check - this WILL show critical warnings
echo "🚨 Running startup warnings check (THIS WILL SHOW CRITICAL WARNINGS)..."
if ! python startup_warnings.py -- "$0"; then
    echo ""
    echo "🛑 EXPECTED RESULT: Critical warnings detected!"
    echo "   This demonstrates why the warning system is essential."
    echo ""
    echo "📚 To see safe alternatives:"
    echo "   • examples/safe_mosflm_rotation.sh"
    echo "   • examples/custom_convention_explicit.sh"
    echo ""
    exit 1
fi

# This code should never execute due to the validation failure above
echo "❌ ERROR: Validation should have failed - something is wrong with startup_warnings.py"
exit 1

# =============================================================================
# DANGEROUS MIXED CONVENTION PARAMETERS (FOR REFERENCE ONLY)
# =============================================================================
# 
# The following parameters demonstrate the dangerous combination:
# 1. MOSFLM detector rotations (detector_rotx, detector_roty, detector_rotz, twotheta)
# 2. CUSTOM convention triggers (-twotheta_axis, -spindle_axis, -vert_axis)
# 3. NO explicit -convention parameter
#
# This causes nanoBragg to silently switch from MOSFLM to CUSTOM convention,
# making some parameters use MOSFLM coordinate system and others use CUSTOM.
#
# The result is a chimera that satisfies neither convention properly.

# Crystal parameters (these are fine)
LAMBDA=6.2
CELL="100 100 100 90 90 90"
N=5
DEFAULT_F=100

# Detector geometry (these are fine)
DISTANCE=100
DETPIXELS=1024
XBEAM=512.5    # MOSFLM-style beam center with 0.5 offset
YBEAM=512.5

# 🚨 DANGER ZONE: Mixed convention parameters
# These look innocent but cause the bug!
DETECTOR_ROTX=5              # ✓ MOSFLM detector rotation
DETECTOR_ROTY=3              # ✓ MOSFLM detector rotation  
DETECTOR_ROTZ=2              # ✓ MOSFLM detector rotation
TWOTHETA=15                  # ✓ MOSFLM detector rotation

# 💥 THE KILLER PARAMETER: This triggers CUSTOM convention!
TWOTHETA_AXIS="0 1 0"        # ❌ CUSTOM axis specification

# Additional CUSTOM triggers (any one of these causes the bug)
SPINDLE_AXIS="0 1 0"         # ❌ CUSTOM axis specification  
VERT_AXIS="0 1 0"           # ❌ CUSTOM axis specification

# What happens:
# 1. nanoBragg starts in MOSFLM mode (default)
# 2. Processes detector_rotx/roty/rotz/twotheta as MOSFLM parameters
# 3. Encounters -twotheta_axis and silently switches to CUSTOM mode
# 4. Reprocesses some parameters with CUSTOM coordinate system
# 5. Results in hybrid state that matches neither convention
# 6. Detector geometry calculations become inconsistent
# 7. Correlation drops from >0.999 to <0.9
# 8. User gets "almost right" results and doesn't notice the bug

# =============================================================================
# Output files (for demonstration of bug detection)
# =============================================================================

OUTPUT_DIR="DANGEROUS_mixed_output"
FLOAT_FILE="$OUTPUT_DIR/mixed_conventions_BROKEN.bin"
SMV_FILE="$OUTPUT_DIR/mixed_conventions_BROKEN.img"

# The dangerous nanoBragg command that would be executed:
DANGEROUS_COMMAND="./nanoBragg \
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
    -twotheta_axis $TWOTHETA_AXIS \
    -spindle_axis $SPINDLE_AXIS \
    -vert_axis $VERT_AXIS \
    -floatfile $FLOAT_FILE \
    -intfile $SMV_FILE \
    -verbose"

# =============================================================================
# Educational Analysis of the Bug
# =============================================================================

echo ""
echo "🎓 EDUCATIONAL ANALYSIS: Why This Combination Is Dangerous"
echo "=========================================================="
echo ""

echo "❌ PROBLEM: Mixed Convention Parameters"
echo "  MOSFLM parameters: -detector_rotx $DETECTOR_ROTX -detector_roty $DETECTOR_ROTY -detector_rotz $DETECTOR_ROTZ -twotheta $TWOTHETA"
echo "  CUSTOM triggers:   -twotheta_axis $TWOTHETA_AXIS -spindle_axis $SPINDLE_AXIS -vert_axis $VERT_AXIS"
echo "  Missing:          -convention CUSTOM"
echo ""

echo "💥 WHAT HAPPENS INTERNALLY:"
echo "  1. nanoBragg starts in MOSFLM mode (default)"
echo "  2. Processes detector rotations using MOSFLM coordinate system"
echo "  3. Encounters axis parameters and switches to CUSTOM mode"
echo "  4. Some calculations now use CUSTOM coordinate system"
echo "  5. Result: Inconsistent geometry calculations"
echo ""

echo "📊 OBSERVABLE SYMPTOMS:"
echo "  • Correlation with C reference: <0.9 (should be >0.999)"
echo "  • Results look 'almost right' - wrong by ~few pixels"
echo "  • Detector geometry appears reasonable on visual inspection"
echo "  • Bragg peaks in approximately correct positions"
echo "  • VERY HARD TO DETECT without systematic validation"
echo ""

echo "🔧 CORRECT SOLUTIONS:"
echo ""
echo "Solution 1 - Pure MOSFLM (RECOMMENDED):"
echo "  ./nanoBragg \\"
echo "    -lambda $LAMBDA \\"
echo "    -distance $DISTANCE \\"
echo "    -detpixels $DETPIXELS \\"
echo "    -Xbeam $XBEAM \\"
echo "    -Ybeam $YBEAM \\"
echo "    -detector_rotx $DETECTOR_ROTX \\"
echo "    -detector_roty $DETECTOR_ROTY \\"
echo "    -detector_rotz $DETECTOR_ROTZ \\"
echo "    -twotheta $TWOTHETA \\"
echo "    -floatfile safe_mosflm.bin"
echo "  # REMOVE: All axis parameters"
echo "  # RESULT: Uses MOSFLM coordinate system consistently"
echo ""

echo "Solution 2 - Explicit CUSTOM:"
echo "  ./nanoBragg \\"
echo "    -convention CUSTOM \\"
echo "    -lambda $LAMBDA \\"
echo "    -distance $DISTANCE \\"
echo "    -detpixels $DETPIXELS \\"
echo "    -Xbeam $XBEAM \\"
echo "    -Ybeam $YBEAM \\"
echo "    -detector_rotx $DETECTOR_ROTX \\"
echo "    -detector_roty $DETECTOR_ROTY \\"
echo "    -detector_rotz $DETECTOR_ROTZ \\"
echo "    -twotheta $TWOTHETA \\"
echo "    -twotheta_axis $TWOTHETA_AXIS \\"
echo "    -spindle_axis $SPINDLE_AXIS \\"
echo "    -vert_axis $VERT_AXIS \\"
echo "    -floatfile safe_custom.bin"
echo "  # ADD: Explicit -convention CUSTOM"
echo "  # RESULT: Uses CUSTOM coordinate system consistently"
echo ""

# =============================================================================
# Historical Context
# =============================================================================

echo "📚 HISTORICAL CONTEXT:"
echo "  This bug has caused WEEKS of debugging in nanoBragg projects because:"
echo "  • The parameter combination looks reasonable"
echo "  • Results appear 'close enough' on casual inspection" 
echo "  • Correlation degradation is gradual, not catastrophic"
echo "  • No error messages or warnings from nanoBragg"
echo "  • Only detected through systematic correlation analysis"
echo ""

echo "🔍 DETECTION METHODS:"
echo "  • Always run correlation analysis against C reference"
echo "  • Use startup_warnings.py before every simulation"
echo "  • Follow validation_checklist.md systematically"
echo "  • Visual inspection is NOT sufficient - need quantitative validation"
echo ""

# =============================================================================
# Prevention Strategies
# =============================================================================

echo "🛡️  PREVENTION STRATEGIES:"
echo ""
echo "1. ALWAYS run startup_warnings.py first:"
echo "   python startup_warnings.py your_script.sh"
echo ""
echo "2. Use safe example scripts as templates:"
echo "   • examples/safe_mosflm_rotation.sh"
echo "   • examples/custom_convention_explicit.sh"
echo ""
echo "3. Follow the validation checklist:"
echo "   • validation_checklist.md"
echo ""
echo "4. Use preflight_check.py for automated validation:"
echo "   python preflight_check.py --config your_parameters.conf"
echo ""
echo "5. Systematic correlation analysis:"
echo "   python scripts/verify_detector_geometry.py"
echo ""

# =============================================================================
# Developer Notes
# =============================================================================

echo "🔧 FOR DEVELOPERS:"
echo "  This example demonstrates why nanoBragg needs:"
echo "  • Better parameter validation at startup"
echo "  • Explicit warnings for convention switching"
echo "  • Clear documentation of parameter interactions"
echo "  • Automated correlation checking in the build system"
echo ""

echo "💡 IMPROVEMENT IDEAS:"
echo "  • Add --strict mode that rejects mixed conventions"
echo "  • Warn when axis parameters are used without explicit convention"
echo "  • Add correlation check to the C code itself"
echo "  • Provide parameter validation functions"
echo ""

echo "🎯 This example shows the #1 most dangerous nanoBragg configuration."
echo "   Always use startup_warnings.py to catch these issues!"

# =============================================================================
# Test the Warning System
# =============================================================================

echo ""
echo "🧪 TESTING THE WARNING SYSTEM:"
echo ""
echo "This script should have been blocked by startup_warnings.py."
echo "If you're seeing this message, there's a bug in the warning system."
echo ""
echo "To test the warning system manually:"
echo "  python startup_warnings.py -- -detector_rotx 5 -detector_roty 3 -twotheta_axis '0 1 0'"
echo ""
echo "Expected result: CRITICAL warning about convention switching."

# This script should never reach here in normal usage