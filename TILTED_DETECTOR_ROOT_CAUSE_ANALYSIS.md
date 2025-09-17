# Tilted Detector Root Cause Analysis

## Problem Summary
Tilted detector configurations show 4.0% correlation with C reference, while baseline shows 99.34% correlation.

## Root Cause Identified

### Issue 1: Convention Switching
When `-twotheta_axis` parameter is specified, the C code automatically switches from MOSFLM to CUSTOM convention. This was not implemented in Python code.

**Evidence:**
- C code outputs "custom convention selected" vs "mosflm convention selected"
- CUSTOM convention does not add the 0.5 pixel offset that MOSFLM adds
- Python code was always adding the 0.5 pixel offset

### Issue 2: Basis Vector Calculation Differences (MAJOR)
Even after fixing the convention issue, there are significant differences in the calculated basis vectors:

**C Reference Basis Vectors:**
```
fdet_vec: [0.0551467, -0.0852831,  0.9948294]
sdet_vec: [0.0302081, -0.9957470, -0.0870363]
odet_vec: [0.9980212,  0.0348517, -0.0523360]
pix0_vec: [0.0952345,  0.0588270, -0.0517022]
```

**Python Calculated Basis Vectors:**
```
fdet_vec: [0.0226524, -0.0990012,  0.9948294]
sdet_vec: [-0.3121792, -0.9460279, -0.0870363]
odet_vec: [0.9497531, -0.3085935, -0.0523360]
pix0_vec: [0.1098136,  0.0226984, -0.0517580]
```

**Analysis:**
- The Z components (fdet_vec[2], sdet_vec[2], odet_vec[2]) match exactly
- The X and Y components differ significantly
- This suggests the rotation calculations are fundamentally different

## Potential Causes of Basis Vector Differences

### 1. Rotation Matrix Construction
- Different order of rotation application
- Different sign conventions for rotations
- Different axis definitions

### 2. Two-theta Rotation Implementation
- Different axis of rotation
- Different direction (positive vs negative)
- Different point of application in the rotation sequence

### 3. Convention-Dependent Initial Vectors
The C code might use different initial basis vectors for CUSTOM vs MOSFLM convention, not just different offset calculations.

## Investigation Evidence

### C Code Convention Detection Logic
```c
// Line 739: -twotheta_axis triggers CUSTOM convention
if(strstr(argv[i], "-twotheta_axis") && (argc > (i+3)))
{
    beam_convention = CUSTOM;
    // ... sets axis values
}
```

### C Code Convention Behavior
```c
// MOSFLM convention (lines 1234-1238):
Fbeam = Ybeam + 0.5*pixel_size;
Sbeam = Xbeam + 0.5*pixel_size;

// CUSTOM convention (lines 1289-1293):
Fbeam = Xbeam;  // No offset
Sbeam = Ybeam;  // No offset
```

### Measured pix0_vector Differences
```
Python:    [0.109814,  0.022698, -0.051758]
C:         [0.095234,  0.058827, -0.051702]
Magnitude: 0.039 meters (39 mm difference!)
```

## Next Steps Required

### 1. Deep Dive into C Rotation Implementation
Need to extract the exact rotation matrices and sequences used by the C code for comparison.

### 2. Step-by-Step Rotation Verification
Create a script that applies rotations step-by-step and compares intermediate results with C code.

### 3. Convention-Aware Basis Vector Calculation
Implement the correct basis vector calculation that matches C code's CUSTOM convention logic.

### 4. End-to-End Verification
Once basis vectors match, verify that the full simulation produces the expected correlation.

## Technical Impact

This basis vector difference affects:
- **Detector geometry**: Pixel positions in 3D space
- **Scattering calculations**: Ray-detector intersections
- **Overall simulation**: Complete diffraction pattern

The 39mm difference in pix0_vector alone is enough to completely misalign the detector geometry, explaining the 4% correlation.

## Priority: CRITICAL
This is the root cause of the correlation issue and must be resolved before proceeding with other detector geometry work.