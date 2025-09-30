# AT-PARALLEL-012 First Divergence Analysis

**Date:** 2025-09-29
**Loop:** Attempt #10 (debugging loop following Attempt #9)
**Status:** PARTIAL - First divergence identified; fix caused regression

## First Divergence: Volume Calculation Mismatch

### C Code Behavior (nanoBragg.c:2065-2115)
```c
// Step 1: Calculate V_star from reciprocal vectors
V_star = dot_product(a_star, b_star_cross_c_star);  // = 2.08117e-06

// Step 2: Calculate V_cell from formula
V_cell = 1.0 / V_star;  // = 481811

// Step 3: Generate real vectors from reciprocal
a = (b_star × c_star) × V_cell;  // Uses formula volume

// Step 4: Recalculate reciprocal vectors
a_star = (b × c) × V_star;  // STILL uses formula volume (NOT 1/V_actual)
```

**Key Insight:** The C code does NOT recalculate `V_star` from the actual volume `a·(b×c)`. It uses the original formula-derived `V_star` throughout.

### PyTorch Behavior (crystal.py:567-582, Attempt #9 baseline)
```python
# Step 1: Calculate real vectors from reciprocal (using formula V)
a_vec = b_star_cross_c_star * V

# Step 2: Recalculate volume from ACTUAL vectors
V_actual = torch.dot(a_vec, b_cross_c)  # ← DIVERGENCE: uses actual, not formula
V_star_actual = 1.0 / V_actual

# Step 3: Recalculate reciprocal vectors
a_star = b_cross_c * V_star_actual  # Uses actual volume
```

**Key Difference:** PyTorch uses `V_actual` (from real vectors), C uses formula `V_star`.

### Numerical Impact

| Metric | C (formula) | PyTorch (actual) | Difference |
|--------|-------------|------------------|------------|
| Volume | 481811 ų | 484449 ų | +0.55% |
| Pixel (368,262) intensity | 138.216 | 136.208 | -1.45% |

### Attempted Fix & Result

**Fix:** Changed PyTorch to use formula volume like C code.

**Result:** ❌ **REGRESSION**
- Correlation: 0.9605 → 0.5868 (dropped 39%)
- Volume: 484449 → 481811 ų ✅ (correct)
- Real vectors: Changed significantly
- Pixel intensity: 136.208 → 115.571 (-16%)

**Conclusion:** Simply matching the volume breaks something else in the calculation chain. The reciprocal vector recalculation affects downstream Miller index calculations, which are extremely sensitive.

## Hypothesis: The Real Issue

The 0.55% volume difference would cause a proportional ~0.55% intensity error, not a 4% correlation drop. The correlation issue is likely due to:

1. **Reciprocal vector precision cascade**: Small changes in reciprocal vectors from volume mismatch propagate through Miller index calculations, affecting which reflections contribute to each pixel.

2. **F_latt calculation sensitivity**: The lattice shape factor `F_latt = sinc(h)/sinc(h/Na)` is extremely sensitive to small changes in `h,k,l`. A 0.02% change in reciprocal vectors (observed in C trace) can shift F_latt significantly for off-integer Miller indices.

3. **Subpixel accumulation**: With oversample=2 (4 subpixels), small differences in each subpixel's calculation compound.

## Next Steps

1. **DO NOT** simply change the volume calculation. This breaks other invariants.

2. **Instead:** Investigate why the C code's circular recalculation (reciprocal → real → reciprocal) produces slightly different vectors, and whether PyTorch's current implementation actually matches the C OUTPUT vectors (not just the process).

3. **Trace comparison needed:** Generate detailed traces showing:
   - Initial reciprocal vectors (after misset)
   - Real vectors calculated from reciprocal
   - **Final** reciprocal vectors after recalculation
   - Compare these FINAL vectors between C and PyTorch
   - Check if Miller indices `h,k,l` match for the same pixel

4. **Consider:** The C code may have a numerical precision issue that we shouldn't replicate. Check if other passing tests (cubic, simple cases) are affected by the current volume calculation.

## Artifacts

- C trace: `reports/2025-09-29-debug-traces-012/c_trace_pixel_368_262.log`
- PyTorch trace: `scripts/trace_pytorch_at012_simple.py`
- Comparison: `reports/2025-09-29-debug-traces-012/comparison_summary.txt`

## Rollback

Code reverted to Attempt #9 baseline. Do NOT commit the attempted fix.