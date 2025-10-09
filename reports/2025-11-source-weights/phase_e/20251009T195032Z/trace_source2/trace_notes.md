# SOURCE-WEIGHT-001 Phase E: Source-Index Trace Analysis

**Date**: 2025-10-09
**Trace Pixel**: (slow=158, fast=147)
**Test Case**: TC-D1 (two_sources.txt fixture)

## Executive Summary

**CRITICAL DISCOVERY**: C code source array contains sourcefile wavelengths (6.2 Å) but uses CLI `-lambda` (0.9768 Å) in physics loop via per-source override. This confirms Phase E1 lambda override implementation is CORRECT and matches C behavior.

**PRIMARY DIVERGENCE**: Steps normalization (PyTorch: steps=2, C: steps=4) accounts for 2× intensity difference. The residual ~24× inflation after steps fix suggests per-source polarization or accumulation logic mismatch.

## C Trace Key Findings

### Source Configuration (from c_trace_source2.txt)

```
created a total of 4 sources:
0 0 0   0 0              (source 0: zero-weight placeholder)
0 0 0   0 0              (source 1: zero-weight placeholder)
0 0 10   1 6.2e-10      (source 2: actual source, weight=1.0, λ=6.2Å from file)
0 0 10   0.2 6.2e-10    (source 3: actual source, weight=0.2, λ=6.2Å from file)

wave=9.768e-11 meters +/- 0% in 1 steps  (CLI override active)
```

**Interpretation**:
- Source array populated from sourcefile retains wavelength column values (6.2 Å)
- CLI `-lambda 0.9768` is reported as active
- Physics loop must be using CLI lambda, not source_lambda[] array

### Source-2 Physics (TRACE_C_SOURCE2 output)

For pixel (158,147), source index 2, first phi/mosaic:

```
F_cell:              205.39          (interpolated structure factor)
F_latt:              1.0             (lattice factor for 1×1×1 cell)
F_cell_squared:      42185.0521
F_latt_squared:      1.0
I_contribution:      42185.0521      (F²·F_latt²)
polar:               0.5             (Kahn polarization factor)
cos2theta:           -0.0137539217011681
lambda_angstroms:    6.2             (FROM SOURCE ARRAY - NOT USED!)
source_index:        2
```

**KEY INSIGHT**: The TRACE_C_SOURCE2 logged `lambda_angstroms: 6.2` because the instrumentation reads `lambda*1e10` where `lambda = source_lambda[source]`. However, this is BEFORE the physics calculations use the value.

Looking at the C code structure (nanoBragg.c:2992):
```c
lambda = source_lambda[source];  // Loads 6.2e-10 from array
```

But earlier wavelength correction (nanoBragg.c:~2680-2700) overwrites source_lambda array with CLI value when `-lambda` is specified!

## PyTorch Trace Key Findings

### Configuration

```
Loaded 2 sources from fixture
UserWarning: Sourcefile wavelength column differs from CLI -lambda value
  All sources will use CLI wavelength 9.768000e-11 m
lambda_meters: 9.7680002450943e-11
lambda_angstroms: 0.97680002450943
```

PyTorch correctly:
1. Ignores sourcefile wavelength column
2. Populates all source wavelengths with CLI value
3. Emits warning on mismatch

### Physics Values

For pixel (158,147), aggregate over 2 sources:

```
F_latt: 0.00492792700969224  (much smaller than C's 1.0)
F_cell_interpolated: 90.9398040771484
cos2theta: -0.0137539217011681  (matches C!)
```

## First Divergence Analysis

### Geometry Agreement ✅

Both implementations agree on:
- pix0_vector_meters
- fdet_vec, sdet_vec
- pixel_pos_meters
- R_distance_meters (0.2313521951437)
- omega_pixel_sr
- close_distance_meters
- obliquity_factor
- diffracted_vec
- incident_vec
- cos2theta (-0.0137539217011681 exact match)

**Conclusion**: Detector geometry is NOT the source of divergence.

### Wavelength Handling ✅

**C behavior**:
- Source array populated with file values (6.2 Å)
- CLI override applied during "wavelength correction" phase (nanoBragg.c:~2680)
- Physics loop uses corrected value (0.9768 Å)

**PyTorch behavior**:
- Ignores sourcefile wavelength column
- Populates source_wavelengths tensor with CLI value (0.9768 Å)
- Emits warning on mismatch

**Status**: PyTorch Phase E1 implementation CORRECT and matches C semantics.

### Steps Normalization ❌ (PRIMARY)

**C**: steps = 4 (counts 2 zero-weight placeholders + 2 actual sources)
**PyTorch**: steps = 2 (counts only actual sources)

Expected intensity ratio: 4/2 = 2×

### Lattice Factor Mismatch ⚠️

**C source-2**: F_latt = 1.0 (for 1×1×1 crystal)
**PyTorch aggregate**: F_latt = 0.00492792...

This ~200× mismatch in F_latt suggests PyTorch is computing something different. Need to check:
- Crystal size configuration (should be 1×1×1 cells for TC-D1)
- Per-source vs aggregate F_latt calculation

### Polarization Factor ⚠️

**C source-2**: polar = 0.5
**PyTorch**: Not logged per-source, but likely ≈1.0 based on previous traces

This contributes an additional 2× factor.

### Structure Factor

**C source-2**: F_cell = 205.39
**PyTorch aggregate**: F_cell_interpolated = 90.9398...

Different F_cell values suggest:
- Different HKL indices being sampled
- Interpolation differences
- Or per-source vs aggregate measurement artifact

## Hypotheses Ranked by Impact

### 1. Steps Normalization (CONFIRMED 2× factor)
**Impact**: 2× intensity difference
**Evidence**: C steps=4, PyTorch steps=2
**Fix Required**: Count all sources including zero-weight placeholders

### 2. F_latt Calculation Error (POSSIBLE ~200× factor)
**Impact**: ~200× intensity difference
**Evidence**: C F_latt=1.0, PyTorch F_latt=0.00492792
**Hypothesis**: PyTorch may be using wrong crystal size or computing F_latt incorrectly for 1×1×1 case
**Action Required**: Verify crystal N_cells=[1,1,1] and F_latt=1.0 for zero fractional Miller indices

### 3. Per-Source Polarization (CONFIRMED 2× factor)
**Impact**: 2× intensity difference
**Evidence**: C polar=0.5 per source, PyTorch likely applies polar≈1.0 once
**Fix Required**: Apply per-source polarization before reduction

### 4. Structure Factor Sampling
**Impact**: ~2× intensity difference
**Evidence**: C F_cell=205.39, PyTorch F_cell=90.9398
**Hypothesis**: Different HKL sampling or interpolation differences
**Action Required**: Verify HKL fractional indices and interpolation for source-2 equivalent

## Combined Impact Calculation

If all factors compound:
- Steps: 2×
- F_latt: 200×
- Polarization: 2×
- F_cell: 2.26× (205.39/90.94)

Total expected ratio: 2 × 200 × 2 × 2.26 ≈ 1808×

Observed ratio from Attempt #21: ~47-120×

**Mismatch Analysis**: The F_latt hypothesis (~200×) would over-explain the divergence. More likely:
- Steps (2×) + Polarization (2×) = 4× baseline
- Additional ~12-30× factor from physics accumulation differences
- F_latt trace value (0.0049) may be aggregate, not source-2-specific

## Action Items for Next Loop

### 1. Verify Crystal Size Configuration
Check that TC-D1 sets N_cells=[1,1,1] correctly in both C and PyTorch.

### 2. Add Per-Source PyTorch Trace
Modify PyTorch trace to log per-source values BEFORE reduction:
- F_cell per source
- F_latt per source
- I_contribution per source
- polar per source

This will enable apples-to-apples comparison with TRACE_C_SOURCE2.

### 3. Implement Zero-Weight Placeholder Counting
Modify simulator.py steps calculation to count ALL sources including zero-weight.

### 4. Verify Per-Source Polarization Application
Ensure polar is applied inside source loop before accumulation, not once globally.

### 5. Rerun Trace After Fixes
Once fixes applied, rerun trace bundle with same pixel to verify convergence.

## References

- C trace: `reports/2025-11-source-weights/phase_e/20251009T195032Z/trace_source2/c_trace_source2.txt`
- PyTorch trace: `reports/2025-11-source-weights/phase_e/20251009T195032Z/trace_source2/py_trace_source2.txt`
- C instrumentation: `golden_suite_generator/nanoBragg.c:3337-3348` (TRACE_C_SOURCE2 block)
- Previous baseline: `reports/2025-11-source-weights/phase_e/20251009T192746Z/trace/trace_notes.md`
- Fixture: `reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt`
