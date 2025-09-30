# FIRST DIVERGENCE: Diffracted Direction Y/Z Swap

## AT-PARALLEL-006 Pixel (64,128) Trace Analysis

**Date:** 2025-09-29
**Test Case:** AT-PARALLEL-006 dist-50mm-lambda-1.0
**Pixel:** (slow=64, fast=128) in (S,F) indexing
**C Pixel Indices:** spixel=64, fpixel=128

---

## Critical Finding

### Diffracted Direction Vector (Lab Frame)

| Component | C Value | PyTorch Value | Match |
|-----------|---------|---------------|-------|
| X | 0.991781438880871 | 0.991781438880871 | ✓ EXACT |
| **Y** | **0.000991781438880865** | **0.127939805615632** | ❌ **SWAPPED WITH Z** |
| **Z** | **-0.127939805615632** | **-0.000991781438880865** | ❌ **SWAPPED WITH Y** |

**Magnitude:** Both are unit vectors (magnitude = 1.0)

---

## Upstream: Pixel Position (Lab Frame, Meters)

The pixel position ALSO shows Y/Z swap:

| Component | C Value | PyTorch Value | Match |
|-----------|---------|---------------|-------|
| X | 0.05 | 0.05 | ✓ EXACT |
| **Y** | **4.99999999999997e-05** | **0.00645** | ❌ **SWAPPED WITH Z** |
| **Z** | **-0.00645** | **-4.99999999999997e-05** | ❌ **SWAPPED WITH Y** |

**This is the root cause!** The pixel coordinate calculation has Y and Z swapped.

---

## Downstream: Polarization Factor

Despite the Y/Z swap in the diffracted direction, the polarization factor is nearly identical due to numerical precision:

| Value | C | PyTorch | Difference |
|-------|---|---------|------------|
| Polarization Factor | 0.991815211254306 | 0.991815211057580 | 1.97e-10 (0.00000002%) |

This tiny difference is NOT the cause of the AT-PARALLEL-006 correlation failure. The polarization calculation itself is correct!

---

## Why This Causes the Cross Pattern

### Geometry Analysis

For pixel (64,128) with detector size 256×256 and beam center at (128,128):
- **Offset from center:** ΔS = 64-128 = -64 pixels, ΔF = 128-128 = 0 pixels
- **Expected position:** Large displacement along SLOW axis, zero along FAST axis
- **C position (Y,Z):** (0.00005m, -0.00645m) → Small Y, Large Z (correct for S-axis displacement)
- **Py position (Y,Z):** (0.00645m, -0.00005m) → Large Y, Small Z (WRONG! F-axis displacement)

### Error Pattern Explanation

The Y↔Z swap causes:
1. **Center (128,128)**: Y≈0, Z≈0 → swap doesn't matter → ratio≈1.000 ✓
2. **Horizontal axis (S=128, F varies)**: Should have Y varying, Z small. Swap causes wrong geometry → ratio≈0.992 or 1.008 ❌
3. **Vertical axis (S varies, F=128)**: Should have Y small, Z varying. Swap causes wrong geometry → ratio≈0.992 or 1.008 ❌
4. **Diagonal corners**: Y≈Z (symmetric) → swap has minimal effect → ratio≈1.000 ✓

This **EXACTLY** matches the observed error pattern from Attempt #6!

---

## Bug Location

The bug is in **pixel coordinate generation**, NOT in polarization calculation.

### Suspected Location: Detector.get_pixel_lab_coords_meters()

The detector coordinate calculation likely has one of these bugs:
1. **F/S basis vectors swapped**: `fdet_vector` and `sdet_vector` are swapped
2. **Axis mapping error**: MOSFLM convention mapping (Fbeam←Ybeam, Sbeam←Xbeam) is incorrectly applied
3. **pix0_vector calculation**: Beam center offset calculation has Y/Z swap

### Reference: C-Code Pixel Coordinate Calculation

From `nanoBragg.c` lines 2871-2873:
```c
pixel_pos[1] = Fdet*fdet_vector[1]+Sdet*sdet_vector[1]+Odet*odet_vector[1]+pix0_vector[1];
pixel_pos[2] = Fdet*fdet_vector[2]+Sdet*sdet_vector[2]+Odet*odet_vector[2]+pix0_vector[2];
pixel_pos[3] = Fdet*fdet_vector[3]+Sdet*sdet_vector[3]+Odet*odet_vector[3]+pix0_vector[3];
```

Where:
- `pixel_pos[1]` = X component
- `pixel_pos[2]` = Y component
- `pixel_pos[3]` = Z component
- `fdet_vector` = fast axis basis (should be [0, 0, 1] for MOSFLM after rotations)
- `sdet_vector` = slow axis basis (should be [0, -1, 0] for MOSFLM after rotations)
- `pix0_vector` = detector origin (beam spot position)

---

## Action Items

1. **Print C basis vectors**: Add trace output for `fdet_vector`, `sdet_vector`, `pix0_vector` in C code for pixel (64,128)
2. **Print Py basis vectors**: Add trace output for equivalent vectors in PyTorch detector
3. **Compare line-by-line**: Identify which vector has Y/Z components swapped
4. **Fix the bug**: Correct the coordinate system in detector.py
5. **Rerun AT-PARALLEL-006**: Verify correlation improves to >0.9995

---

## Expected Fix Impact

Once the Y/Z swap is corrected:
- **AT-PARALLEL-006**: All 3 runs should PASS (corr ≥ 0.9995)
- **AT-PARALLEL-002**: Should remain PASSING (or improve if affected)
- **Polarization calculation**: No change needed (already correct!)

---

## Trace File Locations

- **C trace**: `/home/ollie/Documents/nanoBragg/reports/2025-09-29-debug-traces-006/c_trace_pixel_64_128.log`
- **PyTorch trace**: `/home/ollie/Documents/nanoBragg/reports/2025-09-29-debug-traces-006/py_full_output.log`
- **Comparison summary**: `/home/ollie/Documents/nanoBragg/reports/2025-09-29-debug-traces-006/comparison_summary.md`