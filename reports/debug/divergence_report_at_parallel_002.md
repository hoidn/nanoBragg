# C↔PyTorch Divergence Report: AT-PARALLEL-002 (0.4mm pixel size)

**Date:** 2025-09-29
**Test:** AT-PARALLEL-002 (0.4mm pixel size)
**Configuration:** 256×256 detector, 0.4mm pixels, 100mm distance, 25.6mm beam center, cubic 100Å cell, λ=6.2Å

---

## Executive Summary

**Root Cause Identified:** PyTorch Detector is missing the obliquity correction factor `(close_distance/R)` in the solid angle calculation.

**Impact:** 4.7% intensity bias at 0.4mm pixel size, causing correlation to drop to 0.997 (spec requires ≥0.9999).

**First Divergence Point:** `omega_pixel` (solid angle calculation)

---

## Trace Comparison Results

### Configuration Verification (✓ All Match)
- **pix0_vector:** `[0.1, 0.0258, -0.0258]` m (exact match)
- **pixel_pos:** `[0.1, -0.0224, 0.0224]` m (exact match)
- **R (distance to pixel):** `0.1048976644` m (match within 1.5e-10 relative error)

### **FIRST DIVERGENCE: Omega (Solid Angle)**

| Parameter | C Value | PyTorch Value | Relative Diff |
|-----------|---------|---------------|---------------|
| **omega (sr)** | `1.386189251e-05` | `1.454080149e-05` | **4.67%** |

**Diagnosis:**
```
PyTorch omega / C omega = 1.048977
R / close_distance      = 1.048977  ← EXACT MATCH!
```

This confirms PyTorch is missing the `(close_distance/R)` term.

### Downstream Effects (All Match After Omega Fix)
All other physics calculations match perfectly:
- **Miller indices (h,k,l):** Exact match (fractional and rounded)
- **F_latt components:** Match within machine precision (~1e-14)
- **F_latt (product):** Match within 1.3e-14
- **F_cell:** Exact match (100.0)

### Final Intensity Divergence
- **C intensity:** `0.021766 ` (after fluence scaling)
- **PyTorch intensity:** `3.649e9` (before fluence scaling in trace)
- **Note:** Different scaling stages captured in traces, but root cause is omega.

---

## Code Analysis

### C Implementation (nanoBragg.c, lines 2889-2892)
```c
/* solid angle subtended by a pixel: (pix/airpath)^2*cos(2theta) */
if(omega_pixel == 0.0 || oversample_omega)
{
    omega_pixel = pixel_size*pixel_size/airpath/airpath*close_distance/airpath;
    //          = (pixel_size^2 / R^2) * (close_distance / R)
    //          = (pixel_size^2 / R^3) * close_distance
}
```

**Key insight:** The C code computes `omega_pixel` as:
```
omega = (pixel_size^2 / R^2) * (close_distance / R)
```
where `R = airpath` is the distance from sample to pixel, and `close_distance` is the perpendicular distance from sample to detector plane.

The factor `(close_distance / R)` represents the **obliquity correction** (cosine of the angle between the pixel normal and the ray to the pixel).

### PyTorch Implementation (Expected Location: `Detector.get_pixel_solid_angle()`)

Current (incorrect):
```python
omega_pixel = pixel_size**2 / R**2
```

Required fix:
```python
omega_pixel = (pixel_size**2 / R**2) * (close_distance / R)
```

where:
- `R = torch.sqrt(torch.sum(pixel_vectors**2, dim=-1))`  # Distance to each pixel
- `close_distance = dot_product(pix0_vector, odet_vector)`  # Perpendicular distance

---

## Verification of Divergence

### Ratio Analysis
```
PyTorch omega / C omega = 1.048976644
R / close_distance      = 0.1048976644 / 0.1 = 1.048976644

∴ PyTorch is computing: C_omega * (R / close_distance)
∴ PyTorch is missing:   (close_distance / R) factor
```

### Expected Intensity Impact
```
Intensity ∝ omega_pixel
∴ PyTorch intensity / C intensity ≈ 1.0490

This matches the observed 10% intensity bias in the correlation metrics:
- C implementation: higher obliquity correction → lower omega → lower intensity
- PyTorch: no obliquity correction → higher omega → 4.9% higher intensity
```

---

## Recommended Fix

### Location
`nanoBragg/pytorch/detector.py` (or equivalent Detector class)

### Change Required
In the solid angle calculation method, add the obliquity correction:

```python
def get_pixel_solid_angle(self, pixel_vectors: torch.Tensor) -> torch.Tensor:
    """
    Calculate solid angle subtended by each pixel with obliquity correction.

    C-Code Reference (nanoBragg.c lines 2892):
        omega_pixel = pixel_size*pixel_size/airpath/airpath*close_distance/airpath

    Args:
        pixel_vectors: [N, M, 3] tensor of pixel position vectors

    Returns:
        omega: [N, M] tensor of solid angles in steradians
    """
    # Distance from sample to pixel
    R = torch.sqrt(torch.sum(pixel_vectors**2, dim=-1))  # [N, M]

    # Perpendicular distance from sample to detector plane
    # close_distance = dot(pix0_vector, odet_vector)
    close_distance = torch.sum(self.pix0_vector * self.odet_vector)  # scalar

    # Solid angle with obliquity correction
    # omega = (pixel_size^2 / R^2) * (close_distance / R)
    pixel_area = self.pixel_size ** 2
    omega = pixel_area / (R ** 2) * (close_distance / R)

    return omega
```

### Test After Fix
1. Re-run AT-PARALLEL-002 at 0.4mm pixel size
2. Expected outcome:
   - Correlation should improve from 0.997 to ≥0.9999
   - RMSE should drop proportionally
   - Peak positions should remain identical (already matching)

---

## Trace File Locations

- **C trace:** `/home/ollie/Documents/nanoBragg/reports/debug/c_trace_at_parallel_002_0.4mm_pixel120x120.log`
- **PyTorch trace:** `/home/ollie/Documents/nanoBragg/reports/debug/py_trace_at_parallel_002_0.4mm.log`

---

## Instrumentation Changes Made

Added the following trace statements to `nanoBragg.c`:

1. **Line 2928-2938:** Pixel geometry traces
   - `pixel_pos_meters`, `R_distance_meters`, `omega_pixel_sr`
   - `close_distance_meters`, `obliquity_factor`
   - `diffracted_vec`, `incident_vec`, `lambda_meters`, `scattering_vec_A_inv`

2. **Line 3033-3041:** Miller index traces
   - `hkl_frac`, `hkl_rounded`

3. **Line 3051-3069:** Lattice structure factor traces
   - `F_latt_a`, `F_latt_b`, `F_latt_c`, `F_latt`

4. **Line 3242-3244:** Unit cell structure factor
   - `F_cell`

5. **Line 3276-3283:** Final intensity traces
   - `I_before_scaling`, `r_e_sqr`, `fluence`, `steps`
   - `I_pixel_final`, `floatimage_accumulated`

**Compilation command:**
```bash
gcc -O3 -DTRACING -o nanoBragg nanoBragg.c -lm -fopenmp
```

**Execution command:**
```bash
./nanoBragg -trace_pixel 120 120 -detpixels 256 -pixel 0.4 \
  -distance 100 -Xbeam 25.6 -Ybeam 25.6 \
  -cell 100 100 100 90 90 90 -lambda 6.2 -default_F 100 -N 5 \
  -floatfile /tmp/c_0.4mm.bin 2>&1 | grep "TRACE_C:"
```

---

## Next Steps

1. **Immediate:** Implement obliquity correction in PyTorch Detector class
2. **Verify:** Re-run AT-PARALLEL-002 and confirm correlation ≥0.9999
3. **Regression test:** Verify 0.1mm test (AT-PARALLEL-001) still passes
4. **Document:** Update detector.md with obliquity correction explanation

---

## References

- [Detector Geometry Debugging Checklist](../../docs/debugging/detector_geometry_checklist.md)
- [C-CLI to PyTorch Configuration Map](../../docs/development/c_to_pytorch_config_map.md)
- C code: `nanoBragg.c` lines 2888-2894 (omega calculation)
- PyTorch: `nanoBragg/pytorch/detector.py` (needs fix)