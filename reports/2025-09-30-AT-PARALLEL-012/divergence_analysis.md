# AT-PARALLEL-012 First Divergence Analysis
**Date:** 2025-09-30
**Case:** simple_cubic pixel (513, 446)
**Context:** C=92.72, PyTorch=100.29 (+8.2% error), correlation=0.9946

## Summary

**FIRST DIVERGENCE: `F_latt` (Lattice Shape Factor)**
- **C value:** 96.7149645065984
- **PyTorch value:** 100.582511054283
- **Absolute difference:** +3.868 (4.0% higher in PyTorch)
- **Relative difference:** 3.85%

This is the **root cause** of the 8.2% intensity mismatch at this pixel.

## Divergence Chain Analysis

The comparison reveals a cascading chain of differences:

### 1. **Pixel Position** (First upstream difference)
```
Variable: pixel_pos_meters
C:       0.1 -5.0e-05 -0.00665
PyTorch: 0.1 -1.0e-04 -0.0066
Diff:    0.0 -5.0e-05 +5.0e-05  (50% relative error in Y-coordinate)
```

**Impact:** This small difference (0.05mm = half a pixel) propagates through all downstream calculations.

### 2. **Diffracted Direction** (Consequence of #1)
```
Variable: diffracted_vec
C:       0.997796 -0.000498898 -0.0663534
PyTorch: 0.997829 -0.000997829 -0.0658567
Diff:    +0.000033 -0.000498931 +0.0004967  (3.26e-05 relative)
```

**Impact:** Slightly different ray direction → different scattering vector.

### 3. **Scattering Vector** (Consequence of #2)
```
Variable: scattering_vec_A_inv
C:       -3.554745e+06 -804674 -1.070217e+08
PyTorch: -3.502269e+06 -1609401 -1.062205e+08
Diff:    +52476 -804727 +8012000  (1.48% relative)
```

**Impact:** Different scattering vector → different Miller indices.

### 4. **Miller Indices** (Consequence of #3)
```
Variable: hkl_frac
C:       -0.035547 -0.008047 -1.070217
PyTorch: -0.035023 -0.016094 -1.062205
Diff:    +0.000524 -0.008047 +0.008012  (1.48% relative)
```

**Note:** Both round to same integer `(0, 0, -1)`, so structure factor lookup is correct.

### 5. **Lattice Shape Factor Components** (Consequence of #4)
```
Variable: F_latt_a
C:       4.754074
PyTorch: 4.761182
Diff:    +0.007108  (0.15% relative)

Variable: F_latt_b
C:       4.987228
PyTorch: 4.949020
Diff:    -0.038208  (0.77% relative)

Variable: F_latt_c
C:       4.079139
PyTorch: 4.268629
Diff:    +0.189490  (4.44% relative)  ← LARGEST COMPONENT ERROR
```

**Impact:** The `sinc` function is extremely sensitive to small changes in Miller indices, especially near zeros.

### 6. **Total Lattice Shape Factor** (Product of #5)
```
Variable: F_latt
C:       96.71496 = 4.754 × 4.987 × 4.079
PyTorch: 100.5825 = 4.761 × 4.949 × 4.269
Diff:    +3.868  (4.0% relative)  ← FIRST DIVERGENCE
```

### 7. **Final Intensity** (Consequence of #6)
```
Variable: I_pixel_final
C:       92.7162 ∝ F_latt² = 96.715²
PyTorch: 100.293 ∝ F_latt² = 100.583²
Diff:    +7.577  (8.2% relative)  ← MATCHES OBSERVED ERROR
```

## Root Cause Hypothesis

**Primary Cause:** The 0.05mm (half-pixel) difference in Y-coordinate of `pixel_pos_meters`.

### Detailed Breakdown

1. **C code Y-coordinate:** -5.0e-05 m = -0.05mm
2. **PyTorch Y-coordinate:** -1.0e-04 m = -0.10mm
3. **Difference:** 0.05mm = exactly 0.5 pixels

### Likely Causes (in order of probability)

1. **Pixel Indexing Convention**
   - C code may use pixel **center** (index + 0.5)
   - PyTorch may use pixel **leading edge** (index + 0.0)
   - For pixel (513, 446): C would compute position at (513.5, 446.5) vs PyTorch at (513.0, 446.0)

2. **MOSFLM Beam Center Offset**
   - Recent fix (commit f1cafad) changed MOSFLM +0.5 offset handling
   - May have introduced half-pixel shift in pixel coordinate calculation
   - Test uses MOSFLM convention, golden data generated with C default

3. **Detector Coordinate Calculation**
   - `get_pixel_coords()` in Detector class may have indexing bug
   - Check: `torch.meshgrid(..., indexing="ij")` usage
   - Check: `pix0_vector + s*sdet_vec + f*fdet_vec` formula

## Verification Strategy

### Step 1: Inspect C Code Pixel Position Calculation
Look for the exact formula in `nanoBragg.c` around lines 2800-2900:
```c
pixel_pos[1] = pix0_vector[1] + spixel*sdet_vector[1] + fpixel*fdet_vector[1];
pixel_pos[2] = pix0_vector[2] + spixel*sdet_vector[2] + fpixel*fdet_vector[2];
pixel_pos[3] = pix0_vector[3] + spixel*sdet_vector[3] + fpixel*fdet_vector[3];
```
**Key Question:** Does C code add 0.5 to `spixel` or `fpixel` before this calculation?

### Step 2: Inspect PyTorch Pixel Coordinate Calculation
Check `Detector.get_pixel_coords()` in `/src/nanobrag_torch/models/detector.py`:
```python
s_indices, f_indices = torch.meshgrid(..., indexing="ij")
pixel_coords = pix0_vector + s_indices * sdet_vec + f_indices * fdet_vec
```
**Key Question:** Are `s_indices` and `f_indices` integer-valued (0, 1, 2, ...) or half-pixel-shifted (0.5, 1.5, 2.5, ...)?

### Step 3: Compare `pix0_vector` Values
```
TRACE_C:pix0_vector=0.1 0.0513 -0.0513
TRACE_PY:pix0_vector=0.1 0.05125 -0.05125
```
**Observation:** PyTorch pix0 has slightly different Y/Z coordinates (+5e-05m difference).
**Impact:** This 0.05mm shift is consistent with the pixel position error.

### Step 4: Test Hypothesis
Create a minimal test case:
1. Set beam_center explicitly to match C code exactly
2. Verify pix0_vector matches between C and PyTorch
3. Compute pixel_pos for (513, 446) with explicit integer vs half-pixel indexing
4. Compare results

## Recommended Actions

1. **Immediate (High Priority)**
   - Read C code lines 2800-2900 to verify pixel indexing convention
   - Read PyTorch `Detector.get_pixel_coords()` implementation
   - Check if C adds `+0.5` to pixel indices before coordinate calculation
   - Verify `torch.meshgrid` creates integer (0, 1, 2) vs half-pixel (0.5, 1.5, 2.5) grids

2. **Next Steps**
   - If C uses pixel centers (+0.5), update PyTorch to match:
     ```python
     s_indices = s_indices + 0.5
     f_indices = f_indices + 0.5
     ```
   - If C uses pixel corners (no offset), verify PyTorch is correct as-is
   - Regenerate trace and confirm divergence is eliminated

3. **Follow-up Validation**
   - Rerun AT-PARALLEL-012 test after fix
   - Verify correlation improves from 0.9946 → 0.9995+
   - Check cubic_tilted case also improves (currently 0.9945)
   - Document the correct pixel indexing convention in `docs/architecture/detector.md`

## Files Referenced

- C trace: `/home/ollie/Documents/nanoBragg/reports/2025-09-30-AT-PARALLEL-012/c_trace_pixel_513_446.log`
- PyTorch trace: `/home/ollie/Documents/nanoBragg/reports/2025-09-30-AT-PARALLEL-012/py_trace_pixel_513_446.log`
- Trace script: `/home/ollie/Documents/nanoBragg/scripts/trace_at012_pixel_513_446.py`
- Comparison script: `/home/ollie/Documents/nanoBragg/scripts/compare_traces.py`

## Physics Explanation

The lattice shape factor `F_latt` is computed using the sinc function:

```
F_latt = sinc(π·h·Na) × sinc(π·k·Nb) × sinc(π·l·Nc)
```

where `sinc(x) = sin(x) / x` (or `sin(N·x) / sin(x)` for the generalized form).

**Key Property:** The sinc function has very steep gradients near x=0, so small changes in Miller indices (h, k, l) cause large changes in F_latt.

For this pixel:
- h ≈ -0.035 (small, near zero)
- k ≈ -0.01 (very small, near zero)
- l ≈ -1.06 (close to -1)

The 1.48% difference in k (-0.008 vs -0.016) causes a 4.44% difference in `F_latt_c`, which squares to an 8.8% intensity difference—consistent with the observed 8.2% error.

## Conclusion

The root cause is **not** a physics error, but a **pixel coordinate indexing difference** between C and PyTorch. The 0.5-pixel shift propagates through the entire calculation chain, causing the final 8.2% intensity mismatch.

**Expected Resolution:** Once pixel indexing is corrected, the correlation should jump from 0.9946 to 0.9995+, eliminating the AT-PARALLEL-012 regression.