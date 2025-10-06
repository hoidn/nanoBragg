# Phase G3 Trace Comparison Summary - MOSFLM Orientation

**Date:** 2025-10-06
**Pixel:** (1039, 685)
**Command:** Supervisor parity command with `-mat A.mat`

## Executive Summary

**STATUS: CRITICAL DIVERGENCE FOUND**

The MOSFLM orientation vectors are being interpreted with **transposed dimensions** between C and PyTorch. The C code interprets the A.mat file with real-space vectors as rows, while PyTorch treats reciprocal vectors as columns.

### Key Finding
- **C rot_a:** [-14.356, -21.881, -5.548]
- **PyTorch rot_a:** [-14.356, -11.499, 21.070]

The PyTorch `rot_a` matches C's `rot_a[0]`, `rot_b[0]`, `rot_c[0]` - indicating a row/column transpose.

## First Divergence Analysis

### Detector Geometry (MATCH ✅)
Both implementations now agree on pix0 and beam vectors after Phase F fixes:

| Variable | C Value | PyTorch Value | Delta | Status |
|----------|---------|---------------|-------|--------|
| pix0_vector (m) | [-0.21648, 0.21634, -0.23019] | [-0.21634, 0.21521, -0.23020] | ~0.001 m | ✅ Close (1mm Y diff from CUSTOM transform) |
| fdet_vec | [0.99998, -0.00600, -0.00012] | [0.99998, -0.00600, -0.00012] | <1e-6 | ✅ Match |
| sdet_vec | [-0.00600, -0.99997, -0.00491] | [-0.00600, -0.99997, -0.00491] | <1e-5 | ✅ Match |
| incident_vec | [0.000514, 0, -1.0] | [0.000514, 0, -1.0] | exact | ✅ Match |
| close_distance (m) | 0.23127183 | 0.23127466 | 2.8e-6 m | ✅ Match |

### Lattice Vectors (TRANSPOSED ❌)

**C Implementation (row vectors):**
```
rot_a = [-14.3563, -21.8805, -5.5477]  # first row of rotation matrix
rot_b = [-11.4987,   0.6716, -29.1143]  # second row
rot_c = [ 21.0700, -24.4046,  -9.7143]  # third row
```

**PyTorch Implementation (column vectors):**
```
rot_a = [-14.3563, -11.4987,  21.0700]  # first column = C's [rot_a[0], rot_b[0], rot_c[0]]
rot_b = [-21.8718,   0.7173, -24.3893]  # second column ≈ C's [rot_a[1], rot_b[1], rot_c[1]]
rot_c = [ -5.5820, -29.1132,  -9.7527]  # third column ≈ C's [rot_a[2], rot_b[2], rot_c[2]]
```

**Evidence:**
- PyTorch rot_a[0] = C rot_a[0] = -14.356 ✅
- PyTorch rot_a[1] = C rot_b[0] = -11.499 ✅
- PyTorch rot_a[2] = C rot_c[0] = 21.070 ✅

This is a classic **row-major vs column-major** storage issue.

### Reciprocal Vectors (TRANSPOSED ❌)

**C Implementation:**
```
rot_a_star = [-0.02905, -0.02940,  0.01075]
rot_b_star = [-0.00313,  0.01044, -0.03286]
rot_c_star = [ 0.02596, -0.01433, -0.01061]
```

**PyTorch Implementation:**
```
rot_a_star = [-0.02905, -0.00313,  0.02596]  # = [C_a*[0], C_b*[0], C_c*[0]]
rot_b_star = [-0.02940,  0.01044, -0.01433]  # = [C_a*[1], C_b*[1], C_c*[1]]
rot_c_star = [ 0.01075, -0.03286, -0.01061]  # = [C_a*[2], C_b*[2], C_c*[2]]
```

### Miller Indices (CONSEQUENCE ❌)

Due to the transpose, Miller indices diverge:

| Variable | C Value | PyTorch Value |
|----------|---------|---------------|
| hkl_frac | (2.00, 1.99, -12.99) | (6.06, 6.62, -2.85) |
| hkl_rounded | (2, 2, -13) | (6, 7, -3) |

Wrong Miller indices lead to wrong structure factors and intensities.

### Final Intensity (CONSEQUENCE ❌)

| Variable | C Value | PyTorch Value | Ratio |
|----------|---------|---------------|-------|
| F_cell | 300.58 | 185.98 | 0.62× |
| F_latt | 35636 | -2.068 | Wrong sign! |
| I_pixel_final | 446.25 | 7.3e-07 | ~6e8× mismatch |

## Root Cause

The MOSFLM matrix file stores reciprocal vectors as **rows**:
```
a_star[0] a_star[1] a_star[2]
b_star[0] b_star[1] b_star[2]
c_star[0] c_star[1] c_star[2]
```

**C Code Interpretation (nanoBragg.c):**
- Reads matrix as 3×3 row-major
- Treats rows as reciprocal vectors
- Applies phi rotation to get rotated real vectors

**PyTorch Interpretation (Current):**
- `read_mosflm_matrix()` returns `(a_star, b_star, c_star)` as rows ✅
- But `Crystal.compute_cell_tensors()` treats them as **column vectors** ❌
- Effectively transposes the orientation matrix

## Polarization Delta (DEFERRED)

| Variable | C Value | PyTorch Value | Status |
|----------|---------|---------------|--------|
| polar | 0.9126 | 1.0 | To address in Phase H |

PyTorch currently returns `polar=1.0` (unpolarized), while C computes the Kahn factor. This is expected and will be fixed in Phase H after geometry parity.

## Recommended Fix

**Location:** `src/nanobrag_torch/models/crystal.py:545-568`

The issue is likely in how the MOSFLM vectors are converted to tensors. The code needs to either:

1. **Option A:** Transpose the MOSFLM vectors when reading from file
2. **Option B:** Treat the vectors as row vectors in `compute_cell_tensors()`

Investigation needed to determine which convention `read_mosflm_matrix()` uses and how `compute_cell_tensors()` expects the data.

## Next Actions

1. **Debug MOSFLM matrix interpretation**
   - Add trace print showing how vectors are read from A.mat
   - Verify if transpose happens in `read_mosflm_matrix()` or `compute_cell_tensors()`

2. **Fix vector orientation**
   - Apply correct transpose to align with C convention
   - Ensure Core Rules 12-13 pipeline uses proper orientation

3. **Re-run Phase G3**
   - Regenerate traces after fix
   - Verify rot_a/b/c match C values exactly

4. **Run parity comparison**
   - Execute nb-compare once traces align
   - Document correlation improvement in metrics

## Artifacts

- **C Trace:** `reports/2025-10-cli-flags/phase_g/traces/trace_c.log` (40 lines)
- **PyTorch Trace:** `reports/2025-10-cli-flags/phase_g/traces/trace_py.log` (49 lines)
- **Harness Update:** `reports/2025-10-cli-flags/phase_e/trace_harness.py:89-92` (MOSFLM vectors threaded)
- **Trace Comparison:** Inline in this document

## Status

- ✅ Phase F (detector geometry) complete - pix0 and beam vectors match
- ❌ Phase G2 (orientation ingestion) has transpose bug
- ⏸️ Phase G3 (trace verification) blocked pending fix
- ⏸️ Phase H (polarization) deferred until geometry parity achieved
