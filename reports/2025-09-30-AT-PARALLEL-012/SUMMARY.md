# AT-PARALLEL-012 Trace Analysis Summary
**Date:** 2025-09-30
**Status:** First divergence identified
**Correlation:** 0.9946 (target: 0.9995+)

## Executive Summary

Parallel C and PyTorch traces for simple_cubic pixel (513, 446) successfully identified the **first divergence point** in the calculation chain. The root cause is a **0.5-pixel coordinate offset** that propagates through the entire physics calculation, resulting in an 8.2% intensity error at strong peaks.

## Key Findings

### 1. First Divergence: Pixel Position
**Variable:** `pixel_pos_meters`
**C value:** `[0.1, -5.0e-05, -0.00665]` m
**PyTorch value:** `[0.1, -1.0e-04, -0.0066]` m
**Difference:** `[0.0, -5.0e-05, +5.0e-05]` m = `[0.0, -0.05, +0.05]` mm

**Magnitude:** Exactly **0.5 pixels** (pixel_size = 0.1mm)

### 2. Error Propagation Chain

The 0.5-pixel offset creates a cascade:

```
pixel_pos (0.5px error)
    ↓
diffracted_vec (3.3e-05 rel error)
    ↓
scattering_vec (1.5% rel error)
    ↓
hkl_frac (1.5% rel error)
    ↓
F_latt_components (0.15%-4.4% rel error)
    ↓
F_latt (3.85% error) ← FIRST MEASURED DIVERGENCE
    ↓
I_pixel_final (8.2% error) ← MATCHES OBSERVED
```

### 3. Root Cause Hypothesis

**Pixel Indexing Convention Mismatch:**
- C code likely uses **pixel centers**: `(i + 0.5, j + 0.5)`
- PyTorch uses **pixel leading edges**: `(i, j)`
- Result: 0.5-pixel systematic offset in all pixel coordinates

### 4. pix0_vector Discrepancy

```
C:       pix0_vector = [0.1, 0.0513, -0.0513]
PyTorch: pix0_vector = [0.1, 0.05125, -0.05125]
Diff:                  [0.0, -0.00005, +0.00005]  (exactly 0.05mm = 0.5px)
```

This confirms the pixel center vs edge hypothesis.

## Trace Files Generated

All files located in `/home/ollie/Documents/nanoBragg/reports/2025-09-30-AT-PARALLEL-012/`:

1. **`c_trace_pixel_513_446.log`** - C code trace for pixel (513, 446)
   - Generated via: `./golden_suite_generator/nanoBragg -trace_pixel 513 446 ...`
   - 54 lines of TRACE_C output

2. **`py_trace_pixel_513_446.log`** - PyTorch trace for pixel (513, 446)
   - Generated via: `scripts/trace_at012_pixel_513_446.py`
   - 36 lines of TRACE_PY output

3. **`divergence_analysis.md`** - Detailed analysis of divergence chain
   - Line-by-line comparison
   - Physics explanation
   - Recommended actions

4. **`SUMMARY.md`** (this file) - Executive summary

## Comparison Results

Ran `scripts/compare_traces.py` to identify first divergence:

```
Variable                       C Value                             PyTorch Value                       Match
========================================================================================================================
pixel_pos_meters               0.1 -5e-05 -0.00665                 0.1 -0.0001 -0.0066                 ✗ (50% rel)
diffracted_vec                 0.997796 -0.000499 -0.0664          0.997829 -0.000998 -0.0659          ✗ (3.3e-05)
scattering_vec_A_inv           -3.55e6 -805k -107M                 -3.50e6 -1.61M -106M                ✗ (1.5%)
hkl_frac                       -0.0355 -0.00805 -1.070             -0.0350 -0.0161 -1.062              ✗ (1.5%)
hkl_rounded                    0 0 -1                              0 0 -1                              ✓
F_latt_a                       4.754                               4.761                               ✗ (0.15%)
F_latt_b                       4.987                               4.949                               ✗ (0.77%)
F_latt_c                       4.079                               4.269                               ✗ (4.4%)
F_latt                         96.71                               100.58                              ✗ (3.85%) ← FIRST
I_pixel_final                  92.72                               100.29                              ✗ (8.2%)
```

## Recommended Next Steps

### Immediate Actions (Priority: Critical)

1. **Verify C code pixel indexing convention**
   - Read `nanoBragg.c` lines 2800-2900 for pixel position calculation
   - Check if C adds +0.5 to spixel/fpixel before computing coordinates
   - Document convention in `docs/architecture/detector.md`

2. **Inspect PyTorch `Detector.get_pixel_coords()`**
   - Location: `/src/nanobrag_torch/models/detector.py`
   - Check if meshgrid creates integer (0, 1, 2) or half-pixel (0.5, 1.5, 2.5) grids
   - Verify pixel coordinate formula matches C exactly

3. **Test hypothesis with minimal example**
   ```python
   # Create test detector with explicit pixel indexing
   s_indices = torch.arange(1024)  # Integer: 0, 1, 2, ...
   s_indices_halfpx = s_indices + 0.5  # Half-pixel: 0.5, 1.5, 2.5, ...

   # Compute pixel_pos for (513, 446) both ways
   # Compare with C trace value
   ```

4. **Apply fix and validate**
   - If C uses half-pixel, update PyTorch:
     ```python
     s_indices, f_indices = torch.meshgrid(...)
     s_indices = s_indices + 0.5  # Add half-pixel offset
     f_indices = f_indices + 0.5
     ```
   - Regenerate traces and confirm divergence eliminated
   - Rerun AT-PARALLEL-012 test suite
   - Target: correlation 0.9946 → 0.9995+

### Follow-up Actions

5. **Update documentation**
   - Document pixel indexing convention in detector.md
   - Add note about C vs PyTorch coordinate systems
   - Update testing_strategy.md with trace debugging workflow

6. **Validate other test cases**
   - Rerun cubic_tilted (currently 0.9945)
   - Check triclinic_P1 (currently 0.8352, has separate precision issue)
   - Verify no regressions in AT-001 through AT-011

## Tools Created

1. **`scripts/trace_at012_pixel_513_446.py`**
   - Generates PyTorch trace for specific pixel
   - Matches C trace format for easy comparison
   - Includes all intermediate values (geometry, scattering, Miller indices, intensities)

2. **`scripts/compare_traces.py`**
   - Side-by-side comparison of C and PyTorch traces
   - Identifies first divergence automatically
   - Provides hypothesis based on diverging variable

## References

- **Test:** `/tests/test_at_parallel_012.py::test_simple_cubic_correlation`
- **Golden data:** `/tests/golden_data/simple_cubic.bin`
- **Fix plan:** `/docs/fix_plan.md` (AT-PARALLEL-012-REGRESSION section)
- **C code:** `/golden_suite_generator/nanoBragg.c` (lines 2800-2900 for pixel loop)
- **PyTorch detector:** `/src/nanobrag_torch/models/detector.py`

## Conclusion

**Status:** ✅ First divergence identified
**Root cause:** Pixel coordinate indexing (center vs edge) mismatch
**Impact:** 0.5-pixel offset → 8.2% intensity error at peaks
**Expected fix time:** 1-2 hours (verify convention + apply correction)
**Expected outcome:** Correlation 0.9946 → 0.9995+ after fix

The parallel trace debugging approach successfully isolated the exact line where C and PyTorch calculations diverge, enabling targeted debugging instead of trial-and-error hypothesis testing.