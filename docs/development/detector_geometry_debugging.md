# Detector Geometry Debugging: Lessons Learned

## Executive Summary

During Phase 4 of the General Detector Geometry implementation, we encountered a critical bug where the `cubic_tilted_detector` test initially showed only 0.28 correlation with the golden reference image (target: ≥0.99). Through systematic debugging, we discovered multiple root causes related to coordinate conventions, unit conversions, and rotation axis specifications. This document captures the debugging process, findings, and critical lessons for future development.

## The Problem

### Initial Symptoms
- `test_cubic_tilted_detector_reproduction`: **-0.015 correlation** (first attempt)
- `test_cubic_tilted_detector_reproduction`: **0.28 correlation** (after initial fixes)
- `test_simple_cubic_reproduction`: Regression from >0.999 to 0.977 correlation
- Detector basis vectors not matching C-code reference values

### Expected vs Actual
- **Expected**: ≥0.990 correlation for tilted detector, ≥0.99 for simple cubic
- **Actual**: Correlations far below threshold, indicating fundamental geometry errors

## Debugging Process

### 1. Detector Vector Comparison (First Clue)
```python
# PyTorch vectors (incorrect)
Fast axis: [0.3107, -0.0853, 0.9467]

# C-code reference vectors
Fast axis: [0.0312, -0.0967, 0.9948]
```
The basis vectors were completely wrong, indicating the rotation calculations were incorrect.

### 2. Unit Conversion Issues
```python
# Detector pix0_vector comparison
PyTorch: [1120873.6667, 653100.4061, -556023.3054]  # Angstroms
Expected: [1120873728.0, 653100416.0, -556023296.0]  # Wrong units!
```
Initial comparison showed a factor of ~1000 difference. Investigation revealed:
- C-code outputs PIX0_VECTOR in **meters**
- PyTorch internal representation in **Angstroms**
- Test was comparing different units

### 3. Pixel Coordinate Convention
The simple_cubic test regression revealed a fundamental issue with pixel coordinate calculation:

```python
# OLD method (correct for C-code compatibility)
pixel_position = origin + (index - beam_center) * pixel_size * basis

# NEW method (incorrect initial implementation)  
pixel_position = pix0 + index * pixel_size * basis
where pix0 = origin + (0.5 - beam_center) * pixel_size * basis
```

The 0.5 offset assumed pixel centers at integer indices, but the C-code uses pixel edges at integer indices.

### 4. Detector Pivot Mode
Investigation revealed the detector implementation was modified to support BEAM pivot mode, with complex conditional logic:

```python
if detector_pivot == BEAM:
    # Different pix0_vector calculation
    # Different coordinate system origin
else:  # SAMPLE pivot
    # Original calculation method
```

### 5. Two-Theta Rotation Axis (Root Cause)
The critical bug was in the two-theta rotation axis specification:

```python
# WRONG - gave 0.28 correlation
twotheta_axis=[0.0, 1.0, 0.0]  # Y-axis rotation

# CORRECT - gives 0.993 correlation  
# MOSFLM default (from C-code line 1194)
twotheta_axis=[0.0, 0.0, -1.0]  # -Z axis rotation
```

## Root Causes Discovered

### 1. **Convention Confusion**
- MOSFLM vs XDS detector conventions have different:
  - Initial basis vector orientations
  - Beam vector directions ([1,0,0] vs [0,0,1])
  - Two-theta rotation axes ([0,0,-1] vs [1,0,0])
  - Coordinate system handedness

### 2. **Incomplete C-Code Analysis**
- The C-code has implicit defaults not obvious from command-line parsing
- MOSFLM convention uses -Z axis for two-theta, not +Y axis
- Default values are set in multiple places throughout the code

### 3. **Unit System Inconsistencies**
- C-code uses mixed units internally (meters, millimeters, Angstroms)
- Output formats vary (PIX0_VECTOR in meters, distances in mm)
- PyTorch implementation must maintain consistent internal units (Angstroms)

### 4. **Pixel Indexing Ambiguity**
- Pixel edge vs pixel center convention
- The C-code places pixel edges at integer indices
- Common imaging libraries often place pixel centers at integer indices

## Lessons Learned

### 1. **Always Verify Convention Defaults**
```python
# BAD: Assume a "reasonable" default
twotheta_axis = [0.0, 1.0, 0.0]  # Seems logical for vertical axis

# GOOD: Check the actual C-code default
# From nanoBragg.c line 1194:
twotheta_axis[1]=twotheta_axis[2]=0; twotheta_axis[3]=-1; /* MOSFLM convention */
```

### 2. **Document Coordinate Systems Explicitly**
```python
class DetectorConfig:
    """
    Coordinate System:
    - Origin: Sample position (0,0,0)
    - Beam direction: +X axis (MOSFLM convention)
    - Lab frame: Right-handed, Y up, Z completing the system
    - Pixel indexing: (slow, fast) with edges at integer indices
    - Units: All distances in mm (user input), converted to Angstroms internally
    """
```

### 3. **Unit Annotations in Variable Names**
```python
# BAD: Ambiguous units
distance = 100.0
pix0_vector = [112.08, 65.31, -55.60]

# GOOD: Clear unit specification
distance_mm = 100.0
distance_angstroms = mm_to_angstroms(distance_mm)
pix0_vector_meters = [0.11208, 0.06531, -0.05560]
pix0_vector_angstroms = meters_to_angstroms(pix0_vector_meters)
```

### 4. **Trace-Driven Debugging is Essential**
The parallel trace comparison methodology was crucial:
1. Generate C-code trace with specific debug output
2. Generate PyTorch trace with identical output format
3. Compare line-by-line to find divergence
4. Focus debugging on the exact point of divergence

### 5. **Test Multiple Configurations Early**
Don't just test the default configuration:
- Test with rotations (exposed the basis vector bug)
- Test with different pivot modes (exposed the pix0_vector bug)
- Test with different conventions (exposed the axis bug)

### 6. **Preserve Original Behavior by Default**
When adding new features (like BEAM pivot mode), ensure the default behavior exactly matches the original:
```python
# Default should match original C-code behavior
detector_pivot: DetectorPivot = DetectorPivot.SAMPLE  # Not BEAM
```

## Recommended Coordinate/Notation Conventions

### 1. **Coordinate System Documentation Template**
```markdown
## Coordinate System: [Component Name]

**Origin**: [Description of where (0,0,0) is located]
**Primary Axis**: [Which direction is X/Y/Z, what it represents]  
**Handedness**: [Right-handed or left-handed]
**Units**: [Internal units for all calculations]
**Conventions**: [Any special conventions, e.g., rotation order]

### Transformations
- From [Source] to [Target]: [Transformation description]
- Rotation Convention: [Intrinsic/Extrinsic, Active/Passive]
- Matrix Convention: [Row/Column vectors]
```

### 2. **Variable Naming Convention**
```python
# Pattern: {quantity}_{units}_{coordinate_system}_{note}
distance_mm_input = 100.0  # User input in mm
distance_angstroms = mm_to_angstroms(distance_mm_input)  # Internal
beam_pos_lab_meters = [0.1, 0.0, 0.0]  # Lab frame, meters
beam_pos_detector_pixels = [512, 512]  # Detector frame, pixels
```

### 3. **Rotation Specification**
```python
# Always specify:
# 1. Rotation axis (unit vector)
# 2. Rotation angle (with units)
# 3. Active/passive convention
# 4. Order for multiple rotations

rotation = Rotation(
    axis=[0, 0, 1],  # Unit vector along Z
    angle_deg=15.0,  # Explicitly include units
    convention="active",  # Object rotates, not coordinates
    order="intrinsic"  # Rotations in body frame
)
```

### 4. **Test Data Conventions**
```python
# Golden test parameters should include:
detector_params = {
    "distance_mm": 100.0,  # Explicit units
    "beam_center_mm": {"x": 61.2, "y": 61.2},  # Not just [61.2, 61.2]
    "rotations_deg": {"x": 5, "y": 3, "z": 2},  # Clear axis mapping
    "rotation_order": "XYZ",  # Explicit order
    "twotheta": {
        "angle_deg": 15.0,
        "axis": [0, 0, -1],  # Never rely on defaults
        "pivot": "beam"  # Explicit pivot mode
    }
}
```

## Conclusion

The detector geometry debugging revealed that seemingly small details (rotation axes, unit conventions, coordinate origins) can cause catastrophic failures in scientific simulations. The key lesson is that **implicit conventions are dangerous** - every geometric transformation, unit conversion, and coordinate system must be explicitly documented and verified against reference implementations.

The successful resolution (achieving 0.993 correlation) came from:
1. Systematic comparison with C-code behavior
2. Explicit handling of all conventions
3. Careful unit tracking throughout the codebase
4. Comprehensive testing of non-default configurations

This debugging experience reinforces the importance of the project's "trace-driven validation" methodology and the critical need for explicit, well-documented conventions in scientific computing.