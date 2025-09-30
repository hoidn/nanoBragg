# AT-PARALLEL-012 Trace Analysis: simple_cubic Correlation Discrepancy

**Date:** 2025-09-30
**Test:** `tests/test_at_parallel_012.py::test_simple_cubic_correlation`
**Current Status:** Correlation 0.9946 (target: ≥0.9995)
**Gap:** 0.491% shortfall

---

## Executive Summary

The PyTorch implementation achieves **99.46% correlation** with golden C code data, falling **0.54% short** of the 99.95% target. Detailed trace analysis reveals this is **NOT a systematic scale factor error**, but rather a pattern of small variations across the image.

### Key Findings

1. **Peak Pixel Analysis** (512, 512):
   - Golden C intensity: `154.6524658203`
   - PyTorch intensity: `156.2499999687`
   - **PyTorch is 1.03% HIGHER** at this specific pixel

2. **Bright Pixel Statistics** (top 0.1%):
   - Mean ratio (Golden/PyTorch): `1.012`
   - Std dev: `0.064` (6.4% variation)
   - Range: `0.867` to `1.182`
   - **Conclusion:** Not a uniform scale factor, but pixel-dependent variations

3. **Image Statistics**:
   - RMSE: `0.585`
   - Max absolute difference: `14.1` (9.1% of peak)
   - Mean intensity: `0.881`

---

## Detailed Trace: Strongest Peak (512, 512)

### Detector Geometry

#### Basis Vectors (MOSFLM Convention)
```
fdet_vec:  [0.0, 0.0, 1.0]  ✓ Fast axis along +Z
sdet_vec:  [0.0, -1.0, 0.0] ✓ Slow axis along -Y
odet_vec:  [1.0, 0.0, 0.0]  ✓ Normal along +X (beam direction)
```

#### Beam Center
```
beam_center_s: 512.5 pixels  ✓ MOSFLM +0.5 pixel offset applied
beam_center_f: 512.5 pixels  ✓ MOSFLM +0.5 pixel offset applied
```

#### Pixel Position
```
pix0_vector (m):   [0.1000, 0.05125, -0.05125]
Pixel (512,512):   [0.1000, 0.0000, 0.0000]  ← Direct beam position
Airpath:           0.1000 m
Obliquity factor:  1.0 (perpendicular incidence)
```

**Verification:** Pixel (512,512) is at the direct beam spot, exactly as expected.

---

### Crystal Lattice

#### Lattice Vectors
```
a (Å):  [100.0, 6.12e-15, 6.12e-15]  ✓ Simple cubic
b (Å):  [0.0, 100.0, 6.12e-15]       ✓ 100 Å unit cell
c (Å):  [0.0, 0.0, 100.0]            ✓ 90° angles

a* (Å⁻¹): [0.01, 0.0, 0.0]           ✓ Correct reciprocal vectors
b* (Å⁻¹): [0.0, 0.01, 0.0]
c* (Å⁻¹): [0.0, 0.0, 0.01]

Volume: 1.0e6 Å³                     ✓ (100 Å)³
```

---

### Physics Calculation

#### Scattering Vector
```
Diffracted unit: [1.0, 0.0, 0.0]     ← Along beam direction
Incident unit:   [1.0, 0.0, 0.0]     ← MOSFLM beam along +X
Scattering:      [0.0, 0.0, 0.0]     ← Zero scattering (direct beam)
```

#### Miller Indices
```
(h, k, l) = (0, 0, 0)                ✓ Forward scattering reflection
F_cell    = 100.0                    ✓ default_F parameter
```

#### Lattice Structure Factor (SQUARE shape)
```
N_cells: (5, 5, 5)
F_latt_a = sincg(π × 0, 5) = 5.0
F_latt_b = sincg(π × 0, 5) = 5.0
F_latt_c = sincg(π × 0, 5) = 5.0
F_latt = 5 × 5 × 5 = 125
```

#### Intensity Calculation Chain
```
I_physics   = (F_cell × F_latt)²      = (100 × 125)² = 1.5625e8
steps       = phi × mosaic × oversamp²  = 1 × 1 × 1² = 1
I_norm      = I_physics / steps         = 1.5625e8

Omega       = pixel_size² / R² × obliquity = 1e-6 sr
I_omega     = I_norm × omega              = 156.25

Polarization = 0.99999999980             ✓ ≈ 1.0 for forward scatter
I_polar     = I_omega × polar            = 156.2499999688

Physical constants:
r_e²        = 7.9407924802e-30 m²        ✓ Classical electron radius²
fluence     = 1.2593201529e29 ph/m²      ✓ Default fluence

I_final     = I_polar × r_e² × fluence   = 156.2499999688
```

**PyTorch Trace Verification:** All intermediate values match exactly. ✓

---

## Root Cause Analysis

### What's NOT the Problem

1. **✓ Detector geometry:** Basis vectors, pix0_vector, beam_center all correct
2. **✓ MOSFLM +0.5 pixel offset:** Correctly applied (beam at 512.5, 512.5)
3. **✓ Crystal lattice:** 100 Å cubic unit cell correctly calculated
4. **✓ Forward scattering (000):** F_latt = 125 correct for 5×5×5 crystal
5. **✓ Physical constants:** r_e², fluence match C code
6. **✓ Solid angle:** Omega calculation correct for direct beam

### Investigation Needed

The 1.03% discrepancy at the peak pixel *where PyTorch is HIGHER* contradicts the bright pixel statistics showing Golden is generally higher. This suggests:

#### Hypothesis 1: Pixel-Dependent Variations
- **Evidence:** High std dev (6.4%) in bright pixel ratios
- **Possible Cause:** Subtle differences in:
  - Subpixel sampling (oversample calculations)
  - Pixel coordinate calculation precision
  - Off-axis scattering vector calculations

#### Hypothesis 2: Integration/Sampling Differences
- **Evidence:** Peak (direct beam) is higher in PyTorch, but most pixels lower
- **Possible Cause:**
  - Different treatment of pixel integration vs point sampling
  - Obliquity factor applied differently for off-axis pixels
  - Close_distance vs distance usage in off-axis geometry

#### Hypothesis 3: Floating-Point Precision
- **Evidence:** Very small differences (0.5-1% range)
- **Possible Cause:**
  - PyTorch float64 vs C double (though nominally identical)
  - Order of operations in geometric calculations
  - Accumulation of rounding errors in vectorized operations

---

## Recommended Next Steps

### 1. Trace Off-Axis Bright Pixel
Run trace for pixel with highest deviation (not direct beam):
```python
# Find pixel with max |Golden - PyTorch|
max_diff_idx = np.argmax(np.abs(golden_image - pytorch_image))
```
This will reveal if the problem is in off-axis scattering calculations.

### 2. Compare C Trace for Same Pixel
Generate C code trace for pixel (512, 512) using instrumented nanoBragg.c:
```bash
export NB_C_BIN=./golden_suite_generator/nanoBragg
$NB_C_BIN -trace_pixel 512 512 [... params ...]
```
Compare intermediate values (especially omega, obliquity factor).

### 3. Check Pixel Coordinate Precision
Verify pixel (512, 512) coordinates match C exactly:
```
C:  DETECTOR_PIX0_VECTOR
    PIXEL_COORD[512][512]
```

### 4. Examine Compilation Settings
Check if C code and PyTorch use different precision modes:
- C: `-ffast-math` flag?
- PyTorch: Default tensor precision
- Numerical stability settings

---

## Statistics Summary

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Correlation | 0.9946 | ≥0.9995 | 🔴 0.54% short |
| Peak matching | 43/50 (86%) | ≥95% | 🔴 9% short |
| Peak position error | ≤0.5 px | ≤0.5 px | 🟡 TBD |
| RMSE | 0.585 | N/A | 📊 66% of mean |

---

## Trace Script Location

**Script:** `/home/ollie/Documents/nanoBragg/scripts/trace_at012_simple_cubic.py`

**Usage:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/trace_at012_simple_cubic.py
```

**Output:** Detailed trace with:
- Strongest peak identification
- Detector geometry dump
- Crystal lattice vectors
- Full physics calculation chain
- Statistical analysis
- Hypothesis generation

---

## Conclusion

The PyTorch implementation is **99.46% correct** but exhibits **pixel-dependent variations** rather than a systematic error. The direct beam (000 reflection) is actually 1.03% higher in PyTorch than C, while most off-axis pixels are lower. This pattern suggests the issue lies in:

1. **Off-axis geometry calculations** (pixel coordinates, scattering vectors)
2. **Obliquity factor application** for tilted rays
3. **Floating-point precision** in vectorized operations

The 0.5% gap is solvable but requires pixel-by-pixel C vs PyTorch trace comparison to identify the exact divergence point.