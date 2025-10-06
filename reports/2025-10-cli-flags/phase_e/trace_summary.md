# Phase E Trace Comparison Summary

**Date:** 2025-10-05
**Commit:** ae11d23
**Target Pixel:** (slow=1039, fast=685)
**Objective:** Identify first divergence between C and PyTorch traces for CLI-FLAGS-003 supervisor command

## Executive Summary

**First Divergence:** Line 1 (pix0_vector)
**Root Cause:** PyTorch uses raw user input for pix0_vector without applying CUSTOM convention transformation
**Impact:** Cascading geometry errors leading to wrong diffraction pattern (correlation ≈ 0)

## Trace Generation Commands

### C Trace
```bash
./golden_suite_generator/nanoBragg -mat A.mat -floatfile img.bin -hkl scaled.hkl \
  -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 \
  -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 \
  -distance 231.274660 -lambda 0.976800 -pixel 0.172 \
  -detpixels_x 2463 -detpixels_y 2527 \
  -odet_vector -0.000088 0.004914 -0.999988 \
  -sdet_vector -0.005998 -0.999970 -0.004913 \
  -fdet_vector 0.999982 -0.005998 -0.000118 \
  -pix0_vector_mm -216.336293 215.205512 -230.200866 \
  -beam_vector 0.00051387949 0.0 -0.99999986 \
  -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 \
  -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 \
  -dump_pixel 1039 685 2>&1 | tee reports/2025-10-cli-flags/phase_e/c_trace_beam.log
```

### PyTorch Trace
```bash
env KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python \
  reports/2025-10-cli-flags/phase_e/trace_harness.py 2>&1 | \
  tee reports/2025-10-cli-flags/phase_e/pytorch_trace_beam.log
```

## First Divergence Analysis

### Line 1: pix0_vector_meters

**C Value:**
```
-0.216475836204836  0.216343050492215  -0.230192414300537
```

**PyTorch Value:**
```
-0.216336293  0.215205512  -0.230200866
```

**Deltas:**
- X: -0.000139543 m (0.14 mm) ✓ small
- Y: +0.001137538 m (1.14 mm) ❌ **CRITICAL**
- Z: +0.000008452 m (0.008 mm) ✓ small

**Impact:**
- Y-axis error of 1.14 mm explains observed 1535-pixel horizontal displacement
- Pixel size = 0.172 mm/pixel
- Expected displacement: 1.14 mm / 0.172 mm/pixel ≈ 6.6 pixels
- Actual displacement: 1535 pixels (implies additional rotation/basis issue)

### Cascade Analysis

| Variable | C Value | PyTorch Value | Match? |
|----------|---------|---------------|--------|
| pix0_vector (m) | -0.2165, 0.2163, -0.2302 | -0.2163, 0.2152, -0.2302 | ❌ |
| pixel_pos (m) | -0.0996, 0.0368, -0.2311 | -0.0995, 0.0357, -0.2311 | ❌ |
| diffracted_vec | -0.3918, 0.1449, -0.9086 | -0.3916, 0.1405, -0.9094 | ❌ |
| scattering_vec (Å⁻¹) | -4.016e9, 1.483e9, 9.359e8 | -4.014e9, 1.439e9, 9.279e8 | ❌ |
| rot_a (Å) | -14.36, -21.88, -5.55 | 25.63, -9.11, 6.50 | ❌ |
| hkl_frac | 2.00, 1.99, -12.99 | -10.99, 5.44, 2.90 | ❌ |
| hkl_rounded | (2, 2, -13) | (-11, 5, 3) | ❌ |
| F_cell | 300.58 | 42.98 | ❌ |
| I_pixel_final | 446.25 | 4.5e-6 | ❌ |

**Conclusion:** Single pix0_vector error propagates through entire calculation chain, resulting in:
- Wrong reflection identified: (2,2,-13) vs (-11,5,3)
- Wrong structure factor: 300.58 vs 42.98
- Intensity error of ~10⁸× magnitude (446 vs 4.5e-6)

## Crystal Lattice Vectors Divergence

**CRITICAL FINDING:** C and PyTorch have completely different crystal lattice vectors!

### C Crystal Vectors (Angstroms)
```
rot_a: -14.3563, -21.8805, -5.5477
rot_b: -11.4987,   0.6716, -29.1143
rot_c:  21.0700, -24.4046,  -9.7143
```

### PyTorch Crystal Vectors (Angstroms)
```
rot_a:  25.6320,  -9.1079,   6.5048
rot_b:   0.0000,  31.0230,  10.5498
rot_c:   0.0000,   0.0000,  31.2066
```

**Observations:**
1. PyTorch vectors form an **upper triangular matrix** (b.x=0, c.x=0, c.y=0)
2. C vectors are **fully populated** (general triclinic orientation)
3. This suggests PyTorch is using a **default/canonical orientation** instead of the matrix file orientation
4. The `-mat A.mat` file is likely not being loaded or applied correctly in PyTorch

**Hypothesis:** The A.mat matrix file specifies a specific crystal orientation that C applies correctly, but PyTorch either:
- Doesn't load A.mat at all
- Loads it but doesn't apply the orientation transformation
- Applies it incorrectly with an identity or default transformation

This is a **separate bug** from the pix0_vector issue and may actually be the **primary root cause**.

## Additional Observations

### Incident Beam Direction
Both implementations match exactly:
```
C:       0.000513879 0 -0.999999867963924
PyTorch: 0.00051387949 0 -0.99999986
```
✓ beam_vector is correctly applied (contradicts Attempt #6 hypothesis)

### Detector Basis Vectors
Both implementations match exactly:
```
fdet: 0.999982 -0.005998 -0.000118
sdet: -0.005998 -0.99997 -0.004913
```
✓ CUSTOM detector vectors correctly applied

### Polarization Factor
Significant difference:
```
C:       0.912575818665327
PyTorch: 1.000000000000000
```
❌ PyTorch not calculating polarization correctly (using default 1.0)

## Root Causes Identified

### Primary Issues (Blocking)

1. **Crystal Lattice Orientation Mismatch** (NEW - Most Critical)
   - PyTorch uses canonical/default crystal orientation
   - C uses orientation from A.mat file
   - This causes completely wrong reflections and intensities
   - Location: Crystal initialization or matrix loading code
   - Fix: Verify A.mat loading and ensure orientation matrix is applied to lattice vectors

2. **pix0_vector CUSTOM Convention Transform Missing**
   - PyTorch: Uses raw input `-pix0_vector_mm -216.336293 215.205512 -230.200866` → `-0.216336293, 0.215205512, -0.230200866`
   - C: Transforms input via CUSTOM convention → `-0.216475836, 0.216343050, -0.230192414`
   - Y-component error: 1.14 mm
   - Location: `detector.py:391-407` pix0 override path
   - Fix: Apply CUSTOM convention transformation after override assignment

### Secondary Issues

3. **Polarization Factor Calculation**
   - PyTorch defaults to 1.0 instead of calculating Kahn polarization
   - Should compute based on scattering geometry and beam polarization
   - Location: Physics calculation in simulator

## Next Actions

1. **URGENT:** Investigate A.mat loading in PyTorch
   - Verify file is being read
   - Verify orientation matrix is extracted correctly
   - Verify orientation is applied to lattice vectors
   - Compare with C code matrix loading logic (see TRACE output lines 11-51)

2. Port CUSTOM pix0 transformation from C code (lines ~1730-1860)
   - Identify transformation formula
   - Apply to pix0_override_m in detector.py
   - Preserve differentiability

3. Fix polarization calculation
   - Implement Kahn polarization factor
   - Wire through simulator physics

4. Re-run Phase E traces after fixes to verify alignment

## Artifacts

- C trace: `reports/2025-10-cli-flags/phase_e/c_trace_beam.log` (40 TRACE_C lines + metadata)
- PyTorch trace: `reports/2025-10-cli-flags/phase_e/pytorch_trace_beam.log` (42 TRACE_PY lines)
- Diff: `reports/2025-10-cli-flags/phase_e/trace_diff_beam.txt` (unified diff)
- Summary: This file

## References

- Plan: `plans/active/cli-noise-pix0/plan.md` Phase E
- Fix Plan: `docs/fix_plan.md` CLI-FLAGS-003 Attempt #8 (pending)
- Debugging SOP: `docs/debugging/debugging.md` §2.1 Parallel Trace Comparison
- C Instrumentation: `reports/2025-10-cli-flags/phase_e/instrumentation_notes.md`
- PyTorch Harness: `reports/2025-10-cli-flags/phase_e/trace_harness.py`
