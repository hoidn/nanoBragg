# AT-PARALLEL-012: Off-Axis Peak Analysis Report

**Date:** 2025-09-30
**Test:** simple_cubic correlation (0.9946 vs target 0.9995)
**Goal:** Identify suitable pixel for parallel C/PyTorch trace comparison

## Executive Summary

Analysis of the top 5 off-axis peaks reveals a **critical asymmetry** between direct beam and off-axis pixels:

- **Direct beam (512, 512):** PyTorch is +1.03% HIGHER than C
- **Off-axis peaks:** PyTorch averages -0.07% LOWER than C (range: -1.00% to +1.01%)
- **Recommended trace pixel:** (248, 248) - strong signal, far off-axis, representative error

This pattern suggests **different bugs in different code paths** rather than a simple scale factor.

---

## Top 5 Off-Axis Peaks

| Rank | Pixel (s,f) | Distance | Golden C     | PyTorch      | Ratio (Py/C) | Error % |
|------|-------------|----------|--------------|--------------|--------------|---------|
| 1    | (451, 512)  | 61.0     | 1.422162e+02 | 1.407878e+02 | 0.989956     | -1.0044 |
| 2    | (512, 451)  | 61.0     | 1.422162e+02 | 1.407878e+02 | 0.989956     | -1.0044 |
| 3    | (512, 574)  | 62.0     | 1.422162e+02 | 1.436569e+02 | 1.010130     | +1.0130 |
| 4    | (574, 512)  | 62.0     | 1.422162e+02 | 1.436569e+02 | 1.010130     | +1.0130 |
| 5    | (248, 248)  | 373.4    | 1.155194e+02 | 1.151121e+02 | 0.996475     | -0.3525 |

**Key Statistics:**
- Mean ratio: 0.999329 (off-axis PyTorch 0.07% lower on average)
- Std dev: 0.009134 (0.91% variation)
- Range: 0.020174 (2.02% span from min to max)

---

## Critical Observation: Asymmetric Errors

### Direct Beam vs Off-Axis

```
Direct Beam (512, 512):  Py/C = 1.0103 (+1.03%)
Off-Axis Mean:           Py/C = 0.9993 (-0.07%)
Difference:              1.10% asymmetry
```

**This asymmetry rules out simple scale factor bugs** like:
- ✗ Wrong fluence constant
- ✗ Wrong r_e² value
- ✗ Missing normalization factor

**Likely culprits are position-dependent:**
- Pixel coordinate calculation (pix0_vector, beam_center offset)
- Solid angle (omega) calculation
- Obliquity factor
- Scattering vector geometry

### Spatial Pattern Analysis

The top 4 off-axis peaks form a **symmetric cross pattern** around the direct beam:
- (451, 512) and (574, 512) → horizontal axis ±61-62 pixels
- (512, 451) and (512, 574) → vertical axis ±61-62 pixels

**Symmetry property:** Peaks at equal distances have nearly identical ratios:
- Horizontal: 0.989956 (left) vs 1.010130 (right) → 2.02% asymmetry
- Vertical: 0.989956 (top) vs 1.010130 (bottom) → 2.02% asymmetry

This **±1% asymmetry at ±60 pixels** suggests coordinate-dependent errors in:
- Detector basis vectors (fdet_vec, sdet_vec)
- Pixel position calculation
- MOSFLM +0.5 pixel offset application

---

## Recommended Pixel for Trace: (248, 248)

### Selection Criteria

| Criterion              | Value                   | Justification                           |
|------------------------|-------------------------|-----------------------------------------|
| Signal strength        | 1.155194e+02 photons    | Strong enough for precise comparison    |
| Off-axis distance      | 373.4 pixels            | Far from direct beam region             |
| Error magnitude        | -0.35%                  | Close to mean (-0.07%), not anomalous   |
| Ratio (Py/C)           | 0.996475                | Representative of off-axis behavior     |
| Rank                   | #5                      | Still in top 5 strongest peaks          |

### Advantages

1. **Far off-axis (373 pixels):** Any coordinate/geometry bugs will be amplified
2. **Diagonal position:** Tests both s and f coordinate calculations simultaneously
3. **Moderate error:** Not at the extreme of the ±1% range, so likely representative
4. **Strong signal:** High enough intensity for precise C trace extraction

---

## Pattern Interpretation

### 1. Uniform Off-Axis Error (✓)

The standard deviation of off-axis ratios (0.91%) is relatively small compared to the mean deviation from 1.0. This suggests:

- ✓ Most off-axis pixels share a **common systematic error**
- ✓ The ~2% range (0.99 to 1.01) may be due to **coordinate-dependent variations**

**Implications:**
- The bug is not random noise
- Focus trace comparison on geometry/coordinate calculations

### 2. Different From Direct Beam (⚠)

The 1.1% difference between direct beam (+1.03%) and off-axis mean (-0.07%) indicates:

- ⚠ **Different code paths** for on-axis vs off-axis calculations
- ⚠ **Position-dependent error** in pixel coordinate or scattering vector computation

**Implications:**
- Cannot fix with a single global scale factor
- Must trace through geometry calculations step-by-step

---

## Next Steps for Parallel Trace Debugging

### 1. Instrument C Code for Pixel (248, 248)

Add trace printf statements to `golden_suite_generator/nanoBragg.c`:

```c
// In the pixel loop (around line 8000-10000)
if (spixel == 248 && fpixel == 248) {
    printf("TRACE_C: pixel (248,248)\n");
    printf("TRACE_C: pixel_pos_meters %.15g %.15g %.15g\n", pixel_X, pixel_Y, pixel_Z);
    printf("TRACE_C: R_distance_meters %.15g\n", distance);
    printf("TRACE_C: omega_pixel_sr %.15g\n", omega_pixel);
    printf("TRACE_C: close_distance_meters %.15g\n", close_distance);
    printf("TRACE_C: obliquity_factor %.15g\n", close_distance/distance);
    printf("TRACE_C: diffracted_vec %.15g %.15g %.15g\n", diffracted[0], diffracted[1], diffracted[2]);
    printf("TRACE_C: incident_vec %.15g %.15g %.15g\n", incident[0], incident[1], incident[2]);
    printf("TRACE_C: lambda_meters %.15g\n", lambda);
    printf("TRACE_C: scattering_vec_A_inv %.15g %.15g %.15g\n", scattering[0], scattering[1], scattering[2]);
    printf("TRACE_C: hkl_frac %.15g %.15g %.15g\n", h, k, l);
    printf("TRACE_C: hkl_rounded %d %d %d\n", h0, k0, l0);
    printf("TRACE_C: F_latt %.15g\n", F_latt);
    printf("TRACE_C: F_cell %.15g\n", F_cell);
    printf("TRACE_C: I_before_scaling %.15g\n", I);
    printf("TRACE_C: polar %.15g\n", polarization_factor);
    printf("TRACE_C: I_pixel_final %.15g\n", I * r_e_sqr * fluence * omega_pixel * polarization_factor);
}
```

### 2. Recompile and Run

```bash
make -C golden_suite_generator
NB_C_BIN=./golden_suite_generator/nanoBragg pytest tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_simple_cubic_correlation -v -s 2>&1 | tee c_trace_248_248_raw.log
grep "TRACE_C:" c_trace_248_248_raw.log > c_trace_pixel_248_248.log
```

### 3. Generate PyTorch Trace

Adapt `scripts/trace_at012_pixel_513_446.py` for pixel (248, 248):

```bash
# Edit script to target pixel (248, 248)
KMP_DUPLICATE_LIB_OK=TRUE python scripts/trace_at012_pixel_248_248.py
```

### 4. Line-by-Line Comparison

```bash
# Compare traces side by side
diff -y c_trace_pixel_248_248.log py_trace_pixel_248_248.log | head -50
```

Look for the **first line where values diverge** beyond floating-point precision.

---

## Hypothesis Generation

### Primary Suspects (Ranked by Likelihood)

1. **Pixel coordinate calculation (HIGH)**
   - MOSFLM +0.5 pixel offset applied incorrectly
   - pix0_vector calculation error
   - Detector basis vector (fdet_vec, sdet_vec) construction

2. **Solid angle (omega) calculation (MEDIUM)**
   - Obliquity factor: `close_distance / R`
   - Point pixel vs finite pixel area handling
   - Distance calculation: `R = sqrt(pixel_X² + pixel_Y² + pixel_Z²)`

3. **Scattering vector geometry (MEDIUM)**
   - Diffracted unit vector: `pixel_vec / |pixel_vec|`
   - Scattering vector: `(diffracted - incident) / λ`
   - Miller index rounding or calculation

4. **Direct beam special case (LOW)**
   - C code may have special handling for on-axis pixels
   - Different omega or obliquity calculation near center

### Secondary Suspects

5. **Polarization factor (LOW)**
   - Position-dependent if using actual 3D vectors
   - Should be symmetric, but worth checking

6. **F_latt calculation (VERY LOW)**
   - Should be purely crystallographic, not position-dependent
   - But worth verifying sinc function implementation

---

## Expected Trace Findings

Based on the error pattern, we expect the trace comparison to reveal:

1. **Detector geometry match:** Initial fdet_vec, sdet_vec, pix0_vector should be identical
2. **Pixel position MISMATCH:** pixel_pos_meters will likely differ slightly (~0.1-1% error)
3. **Cascading errors:** All downstream calculations (R, omega, diffracted_vec, S_vec, h/k/l) will diverge
4. **F_latt/F_cell match:** Crystallographic terms should be identical if Miller indices match

**Critical question:** Does the pixel position error manifest immediately (in pix0_vector or beam_center offset), or does it accumulate during coordinate transformation?

---

## Appendix: Full Peak Data

```
Overall correlation: 0.9946 (target: 0.9995, shortfall: 0.49%)

Direct beam (512, 512):
  Golden C:  1.546525e+02
  PyTorch:   1.562500e+02
  Ratio:     1.010330 (+1.0330%)

Top 5 off-axis peaks (excluding ±10 pixels from center):
  Rank 1: (451, 512) dist=61.0   Golden=1.422e+02 PyTorch=1.408e+02 Ratio=0.9900 (-1.00%)
  Rank 2: (512, 451) dist=61.0   Golden=1.422e+02 PyTorch=1.408e+02 Ratio=0.9900 (-1.00%)
  Rank 3: (512, 574) dist=62.0   Golden=1.422e+02 PyTorch=1.437e+02 Ratio=1.0101 (+1.01%)
  Rank 4: (574, 512) dist=62.0   Golden=1.422e+02 PyTorch=1.437e+02 Ratio=1.0101 (+1.01%)
  Rank 5: (248, 248) dist=373.4  Golden=1.155e+02 PyTorch=1.151e+02 Ratio=0.9965 (-0.35%)
```

---

## Conclusion

The off-axis peak analysis has revealed a **non-trivial error pattern** that cannot be explained by a simple scale factor. The **1.1% asymmetry** between direct beam (+1.03%) and off-axis mean (-0.07%) points to **position-dependent geometry calculations** as the root cause.

**Pixel (248, 248)** is the optimal choice for parallel trace debugging because it:
- Has strong signal for precise measurement
- Is far off-axis to amplify coordinate errors
- Shows representative off-axis behavior (-0.35% error)
- Tests diagonal coordinates (both s and f axes)

The next phase of debugging should focus on **step-by-step comparison** of geometry calculations (pixel position, solid angle, scattering vector) to identify where PyTorch deviates from C.