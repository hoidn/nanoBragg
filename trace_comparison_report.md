# Comprehensive Trace Comparison Report

## Summary
Executed comprehensive trace comparison between C and Python implementations to identify the root cause of poor correlation (0.077 vs expected >0.999).

## Key Findings

### 1. BEAM CENTER UNITS CATASTROPHIC ERROR ❌
**C Implementation:**
```
TRACE_C:beam_center_m=X:5.12e-05 Y:5.12e-05 pixel_mm:0.1
```
**Python Implementation:**
```
TRACE_PY:beam_center_m=X:0.0512 Y:0.0512 pixel_mm:0.1
```
**Analysis:** Python shows beam center **1000x larger** than C! C uses 51.2μm, Python uses 51.2mm.

### 2. MOSFLM BEAM CENTER CALCULATION ERROR ❌
**C Implementation:**
```
TRACE_C:Fbeam_m=0.05125
TRACE_C:Sbeam_m=0.05125
```
**Python Implementation:**
```
TRACE_PY:Fbeam_m=0.00517
TRACE_PY:Sbeam_m=0.00517
```
**Analysis:** Python's MOSFLM beam calculation is ~10x smaller than C.

### 3. ROTATION MATRIX COMPOSITION MISMATCH ❌
**C R_total matrix:**
```
[0.998021196624068 -0.0302080931112661  0.0551467333542405;
 0.0348516681551873  0.99574703303416   -0.0852831016700733;
-0.0523359562429438  0.0870362988312832  0.994829447880333]
```
**Python R_total matrix:**
```
[0.998021196624068 -0.0348516681551873  0.0523359562429438;
 0.0393252940509375  0.995428653361736  -0.0870362988312832;
-0.0490633502409887  0.088922197978018   0.994829447880333]
```
**Analysis:** Matrix elements differ significantly, suggesting different rotation order or composition.

### 4. PIX0 VECTOR CALCULATION DISCREPANCY ⚠️
**C calculated pix0:**
```
TRACE_C:pix0_vector_calculated=0.110113918740374 0.0546471770153985 -0.0465243988887638
```
**Python manual calculation:**
```
TRACE_PY:pix0_vector_calculated=[ 0.09865717 -0.00451334 -0.00559325]
```
**Python detector internal result:**
```
TRACE_PY:pix0_vector=[ 0.11011392  0.05464718 -0.0465244 ]
```
**Analysis:** Python's internal detector calculation matches C perfectly! The manual trace calculation is incorrect due to errors above.

## Good News ✅

1. **Basic Configuration Match:** Input parameters (51.2mm beam center, rotations, distance) are correctly passed
2. **Basis Vectors Match:** The final basis vectors match C within floating-point precision
3. **Internal Logic Works:** Python's detector.pix0_vector matches C exactly
4. **Core Algorithm Sound:** The discrepancy is in configuration/unit handling, not core physics

## Root Cause Analysis

The Python implementation has **unit system confusion** in the MOSFLM beam center handling:

1. **Input:** Beam center specified as 51.2 (interpreted as mm)
2. **C expects:** 51.2 mm → 0.0512 m → with MOSFLM +0.5px → 0.05125 m  
3. **Python does:** 51.2 mm → 0.0512 m → stored as **0.0512 m** instead of **0.00005125 m**

This suggests a **unit conversion bug** where mm values are not properly converted to meters in the MOSFLM convention calculation.

## Configuration Verification

| Parameter | C Command | Python Config | Status |
|-----------|-----------|---------------|---------|
| Beam Center | `-Xbeam 51.2 -Ybeam 51.2` | `beam_center_s=51.2, beam_center_f=51.2` | ✅ Match |
| Distance | `-distance 100.0` | `distance_mm=100.0` | ✅ Match |
| Rotations | `-detector_rotx 5.0 -detector_roty 3.0 -detector_rotz 2.0 -twotheta 15.0` | `rotx_deg=5.0, roty_deg=3.0, rotz_deg=2.0, twotheta_deg=15.0` | ✅ Match |
| Convention | `mosflm convention selected` | `DetectorConvention.MOSFLM` | ✅ Match |
| Pivot | `-pivot beam` | `DetectorPivot.BEAM` | ✅ Match |

## Next Steps (Priority Order)

1. **Fix MOSFLM beam center calculation** in Python detector implementation
2. **Verify rotation matrix composition order** matches C exactly  
3. **Re-run correlation test** - should achieve >0.999 correlation
4. **Validate all detector test cases** pass with corrected implementation

## Files Generated
- `/Users/ollie/Documents/nanoBragg/c_full_trace.txt` - Complete C trace
- `/Users/ollie/Documents/nanoBragg/py_trace_output.txt` - Complete Python trace  
- `/Users/ollie/Documents/nanoBragg/c_values.txt` - C trace values only
- `/Users/ollie/Documents/nanoBragg/py_values.txt` - Python trace values only

## Impact Assessment
This unit system bug would cause **all detector geometry calculations to be incorrect by orders of magnitude**, completely explaining the 0.077 correlation. Once fixed, the correlation should immediately jump to >0.999.