# AT-PARALLEL-012 Spatial Pattern Diagnosis

**Date:** 2025-09-30
**Test:** simple_cubic correlation (Golden vs PyTorch)
**Status:** 0.9946 correlation (target: ≥0.9995, 0.5% gap)

---

## Executive Summary

The spatial analysis reveals **strong evidence of an omega (solid angle) calculation error** in the PyTorch implementation. The bug manifests as:

- **Center pixels:** PyTorch produces +7.07% HIGHER intensity
- **Edge pixels:** PyTorch produces +3.18% HIGHER intensity
- **Net asymmetry:** 3.9% center-edge difference
- **Pattern:** Strong negative radial correlation (-0.6332)

**Root Cause Hypothesis:** Incorrect `close_distance` calculation or r-factor application in the obliquity correction formula:
```
omega = (pixel_size^2 / R^2) * (close_distance / R)
```

---

## Detailed Findings

### 1. Radial Dependence (HIGH CONFIDENCE)

**Observation:**
- Strong negative correlation with distance from center: **r = -0.6332**
- Linear fit: `ratio = -6.05e-05 * distance + 1.057`
- Center (r<100): ratio = 1.0707 (+7.07% error)
- Edge (r>400): ratio = 1.0318 (+3.18% error)

**Interpretation:**
This pattern is **characteristic of solid angle (omega) calculation errors**. As distance from center increases, the obliquity correction should increase (omega decreases with distance), but PyTorch appears to have the wrong slope.

**Evidence Strength:** 🔴 **CRITICAL** - This is the smoking gun

### 2. Angular Dependence (MEDIUM CONFIDENCE)

**Observation:**
- Angular variation (std): 0.022
- Angular range: 0.086 (8.6% variation)
- Quadrant asymmetry: std = 0.0088

**Interpretation:**
The angular dependence suggests either:
1. Detector basis vector error (less likely - vectors are well-tested)
2. Secondary effect from radial omega error interacting with Bragg peaks

**Evidence Strength:** 🟡 **MODERATE** - Likely a secondary effect

### 3. Intensity Dependence (MEDIUM CONFIDENCE)

**Observation:**
- Strong negative correlation with log(intensity): **r = -0.6573**
- Bright pixels (direct beam) have higher ratios
- Dim pixels (weak reflections) have lower ratios

**Interpretation:**
This could indicate:
1. **Primary hypothesis:** The omega error affects bright pixels more (center is brightest)
2. **Alternative:** Normalization error that scales with intensity

However, the radial pattern is more consistent than the intensity pattern, suggesting intensity dependence is a **consequence** of the radial error (bright peaks are near center).

**Evidence Strength:** 🟡 **MODERATE** - Likely consequence of radial error

### 4. Symmetry Analysis

**Quadrant Ratios:**
- Upper-left: 1.0515
- Upper-right: 1.0425
- Lower-left: 1.0425
- Lower-right: 1.0270

**Interpretation:**
Slight quadrant asymmetry (std = 0.0088) suggests the error is not perfectly radially symmetric. This could indicate:
1. Interaction with discrete Bragg peak positions
2. Minor coordinate system error

**Evidence Strength:** 🟢 **LOW** - Minor effect

---

## Visual Evidence

The diagnostic plots (at012_spatial_analysis.png) show:

1. **Ratio Map:** Clear "hot center" pattern - ratios decrease from center to edges
2. **Log Difference:** Symmetric ring pattern confirms radial dependence
3. **Radial Profile:** Monotonic decrease with distance (r = -0.6332)
4. **Angular Profile:** Some variation but not dominant
5. **Intensity Dependence:** Strong correlation but confounded with radial pattern
6. **Ratio Distribution:** Centered at ~1.00 but with long tail toward higher values

---

## Top 3 Hypotheses (Ranked by Evidence)

### Hypothesis 1: Omega Calculation Error (🔴 HIGH PRIORITY)

**Evidence:**
- Radial correlation: -0.6332 (strong)
- Center-edge asymmetry: 3.9%
- Pattern matches omega dependence: `omega ∝ (close_distance/R^3)`

**Bug Locations:**
1. **simulator.py, lines 660-670 (subpixel omega):**
   ```python
   omega_all = (pixel_size_m * pixel_size_m) / (airpath_m_all * airpath_m_all) * close_distance_m / airpath_m_all
   ```

2. **simulator.py, lines 769-780 (pixel-center omega):**
   ```python
   omega_pixel = (pixel_size_m * pixel_size_m) / (airpath_m * airpath_m) * close_distance_m / airpath_m
   ```

3. **detector.py, lines 434-472 (_calculate_pix0_vector r-factor calculation):**
   ```python
   ratio = torch.dot(beam_vector, odet_rotated)
   self.distance_corrected = close_distance / ratio
   self.close_distance = close_distance
   ```

**Specific Issues to Check:**
1. Is `close_distance` being calculated correctly?
2. Is `close_distance_m` vs `distance_m` used consistently?
3. Is the r-factor (`ratio`) being applied correctly?
4. Are there unit conversion errors (mm vs meters)?

**Diagnostic Test:**
```python
# Add logging at center vs edge pixels
center_pixel = (512, 512)
edge_pixel = (512, 800)

print(f"Center omega: {omega_pixel[center_pixel]}")
print(f"Edge omega: {omega_pixel[edge_pixel]}")
print(f"Ratio: {omega_pixel[center_pixel] / omega_pixel[edge_pixel]}")
```

Expected behavior: omega should decrease ~3-4x from center to edge for this geometry.

---

### Hypothesis 2: Polarization Factor Error (🟡 MEDIUM PRIORITY)

**Evidence:**
- Angular variation: 8.6%
- Quadrant asymmetry: 0.88%
- Center-edge difference could be cos(theta) dependence

**Bug Locations:**
1. **simulator.py, lines 685-694 (polarization calculation):**
   ```python
   polar_flat = polarization_factor(self.kahn_factor, incident_flat, diffracted_flat, self.polarization_axis)
   ```

2. **utils/physics.py (polarization_factor function):**
   - Check incident/diffracted beam direction calculation
   - Verify polarization axis handling

**Diagnostic Test:**
```python
# Compare polarization at center vs edges
print(f"Center polar: {polar_all[center_pixel]}")
print(f"Edge polar: {polar_all[edge_pixel]}")
```

Expected behavior: Polarization should vary ~1-2% across detector, not 7%.

---

### Hypothesis 3: Normalization Error (🟢 LOW PRIORITY)

**Evidence:**
- Mean ratio: 1.041 (+4.1% overall)
- But spatial pattern rules out uniform scaling

**Bug Locations:**
- **simulator.py, line 562 (steps calculation):**
  ```python
  steps = source_norm * phi_steps * mosaic_domains * oversample * oversample
  ```

**Why Low Priority:**
If this were a pure normalization error, we'd expect a uniform offset (all pixels ~1.04). The strong spatial pattern indicates this is **not** the primary cause.

---

## Recommended Investigation Path

### Step 1: Verify Omega Calculation (IMMEDIATE)

1. Add detailed logging to `simulator.py`:
   ```python
   # After omega calculation (line ~780)
   if debug:
       center_omega = omega_pixel[512, 512]
       edge_omega = omega_pixel[512, 800]
       print(f"DEBUG: center_omega = {center_omega:.6e}")
       print(f"DEBUG: edge_omega = {edge_omega:.6e}")
       print(f"DEBUG: close_distance_m = {close_distance_m:.6e}")
       print(f"DEBUG: distance_m = {self.distance:.6e}")
   ```

2. Compare with C code omega calculation:
   - C code formula (from nanoBragg.c): `omega = pixel_size^2 / R^2 * close_distance / R`
   - Verify each component matches

3. Check r-factor propagation:
   ```python
   # In detector.py after r-factor calculation
   print(f"DEBUG: r_factor = {self.r_factor:.15g}")
   print(f"DEBUG: distance_corrected = {self.distance_corrected:.15g}")
   print(f"DEBUG: close_distance = {self.close_distance:.15g}")
   ```

### Step 2: Compare with C Trace (if omega is wrong)

If Step 1 reveals omega discrepancy:
1. Recompile C code with omega tracing
2. Compare omega at same pixel positions
3. Identify exactly where the formulas diverge

### Step 3: Fix and Validate

1. Apply fix to omega calculation
2. Re-run test_at_parallel_012
3. Verify correlation improves from 0.9946 → >0.9995

---

## Code Locations Summary

**Primary Suspects (HIGH PRIORITY):**
1. `/home/ollie/Documents/nanoBragg/src/nanobrag_torch/simulator.py`
   - Line 665-670: Subpixel omega calculation
   - Line 769-780: Pixel-center omega calculation
   - Line 765: `close_distance_m` assignment

2. `/home/ollie/Documents/nanoBragg/src/nanobrag_torch/models/detector.py`
   - Line 434-472: `_calculate_pix0_vector()` r-factor calculation
   - Line 468: `self.distance_corrected = close_distance / ratio`
   - Line 472: `self.close_distance = close_distance`

**Secondary Suspects (MEDIUM PRIORITY):**
3. `/home/ollie/Documents/nanoBragg/src/nanobrag_torch/utils/physics.py`
   - `polarization_factor()` function

4. `/home/ollie/Documents/nanoBragg/src/nanobrag_torch/simulator.py`
   - Line 562: Steps calculation (normalization)

---

## Conclusion

The spatial pattern analysis provides **strong evidence for an omega (solid angle) calculation error** as the root cause of the 0.5% correlation gap in AT-PARALLEL-012.

**Key Evidence:**
1. ✅ Strong radial dependence (r = -0.6332)
2. ✅ Center-edge asymmetry (3.9%)
3. ✅ Pattern matches omega formula: `omega ∝ 1/R^3`
4. ✅ Center is too high (+7%), edges are too high (+3%)

**Recommended Action:**
1. Add omega logging at center vs edge pixels
2. Compare with C code omega calculation
3. Fix the close_distance or r-factor calculation
4. Validate with full test suite

**Expected Outcome:**
Fixing the omega calculation should improve correlation from **0.9946 → >0.9995**, closing the 0.5% gap and passing AT-PARALLEL-012.

---

## Artifacts

- **Diagnostic Script:** `/home/ollie/Documents/nanoBragg/scripts/diagnose_at012_spatial_pattern.py`
- **Plots:** `/home/ollie/Documents/nanoBragg/diagnostic_artifacts/at012_spatial/at012_spatial_analysis.png`
- **This Report:** `/home/ollie/Documents/nanoBragg/diagnostic_artifacts/at012_spatial/DIAGNOSIS_SUMMARY.md`

**Next Steps:** Investigate omega calculation with detailed logging, compare to C reference.