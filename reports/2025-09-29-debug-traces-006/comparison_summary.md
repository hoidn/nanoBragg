# AT-PARALLEL-006 Polarization Trace Comparison - Pixel (64,128)

## Executive Summary

**FIRST DIVERGENCE IDENTIFIED:** Diffracted direction vector has Y/Z components swapped between C and PyTorch.

## Trace Comparison

### Pixel Position (Lab Frame, Meters)
- **C:**  `0.05  4.99999999999997e-05  -0.00645`
- **Py:** `0.05  0.00645  -4.99999999999997e-05`
- **Status:** Y and Z components are SWAPPED

### Diffracted Direction Unit Vector (Lab Frame)
- **C:**  `0.991781438880871  0.000991781438880865  -0.127939805615632`
- **Py:** `0.991781438880871  0.127939805615632  -0.000991781438880865`
- **Status:** **DIVERGENCE! Y and Z components are SWAPPED**

### Incident Direction Unit Vector
- **C:**  `1  0  -0` (essentially [1, 0, 0])
- **Py:** `1  0  0`
- **Status:** ✓ IDENTICAL

### Polarization Axis
- **C:**  `0  0  1`
- **Py:** `0  0  1`
- **Status:** ✓ IDENTICAL

### Polarization Factor
- **C:**  `0.991815211254306`
- **Py:** `0.991815211057580`
- **Difference:** `1.97e-10` (0.00000002%)
- **Status:** ✓ ESSENTIALLY IDENTICAL (numerical precision difference only)

### Final Pixel Intensity
- **C:**  `0.038702470184066`
- **Py:** `0.038702470176390`
- **Ratio (Py/C):** `0.999999801697`
- **Difference:** `-2.0e-8` (0.000002%)
- **Status:** Near-perfect agreement

## Root Cause Analysis

### The Bug
The diffracted direction vector calculation has Y and Z components swapped. This appears to be a coordinate system mapping error between the detector pixel coordinates and the lab frame diffracted direction.

### Why This Causes the Cross Pattern
1. **Polarization depends on scattering geometry**: `polar = f(incident, diffracted, polarization_axis)`
2. **Axis swap affects polarization asymmetrically**: When Y and Z are swapped:
   - Pixels along horizontal axis (varying fast/F, fixed slow/S) have wrong geometry
   - Pixels along vertical axis (varying slow/S, fixed fast/F) have wrong geometry
   - Diagonal corners happen to work due to symmetry
3. **Error is NOT radial**: The pattern is a cross (F/S axes), not a ring (distance from center)

### Expected Error Pattern
Given that Y↔Z swap:
- Center pixel (128,128): Y and Z are small and similar → small error
- Pixel (64,128): Large Y, small Z → swapping causes wrong polarization angle
- Pixel (128,64): Small Y, large Z → swapping causes wrong polarization angle
- Diagonal (64,64) or (192,192): Y≈Z → swap has minimal effect

This **EXACTLY matches** the observed AT-PARALLEL-006 error pattern!

## Hypothesis

The bug is in the detector pixel coordinate generation or the conversion from pixel coordinates to lab frame diffracted direction.

**Likely culprits:**
1. `Detector.get_pixel_lab_coords_meters()` may have F/S axes swapped
2. The diffracted direction calculation (normalization of pixel_coords) inherits this swap
3. MOSFLM convention applies axis mapping (Fbeam←Ybeam, Sbeam←Xbeam) which may be incorrectly applied

## Next Steps

1. **Verify detector basis vectors**: Check `fdet_vector` and `sdet_vector` in C vs PyTorch
2. **Check pix0_vector calculation**: Verify beam center mapping and axis order
3. **Review MOSFLM convention mapping**: Ensure F/S→Lab frame transformation is correct
4. **Fix the coordinate system bug**: Correct the Y/Z swap in pixel coordinate generation or diffracted direction calculation

## Files for Investigation

- `/home/ollie/Documents/nanoBragg/src/nanobrag_torch/models/detector.py` (lines ~200-300: coordinate generation)
- `/home/ollie/Documents/nanoBragg/golden_suite_generator/nanoBragg.c` (lines ~2867-2886: C pixel coordinate calculation)
- `/home/ollie/Documents/nanoBragg/docs/architecture/detector.md` (coordinate system specification)

## Trace Files

- C trace: `/home/ollie/Documents/nanoBragg/reports/2025-09-29-debug-traces-006/c_trace_pixel_64_128.log`
- PyTorch trace: `/home/ollie/Documents/nanoBragg/reports/2025-09-29-debug-traces-006/py_full_output.log` (lines 8-31)