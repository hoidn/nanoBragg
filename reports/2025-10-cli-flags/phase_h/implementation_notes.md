# Phase H3 Implementation Notes

**Date:** 2025-10-05
**Focus:** Lattice factor mismatch diagnosis

## Validated Components ✅

1. **Incident Beam Vector:** Perfect match after H2 fix (commit 8c1583d)
2. **Reciprocal Vectors:** rot_a_star, rot_b_star, rot_c_star identical to C (Phase G3)
3. **Orientation Matrix:** MOSFLM A* ingestion correct (Phase G2)

## Outstanding Issues 🔴

### Issue 1: F_latt Component Sign and Magnitude
- C produces positive values ~25-40
- PyTorch produces mix of signs, magnitude ~2-10
- Product differs by 568× (35636 vs 62.7)

### Issue 2: Miller Indices Fractional Precision
- h: Δ≈0.097 (exceeds 1e-3 threshold)
- k: Δ≈0.024 (exceeds 1e-3 threshold)
- l: Δ≈0.120 (exceeds 1e-3 threshold)

## Hypotheses (Priority Order)

### Hypothesis 1: sincg Argument Order (HIGH CONFIDENCE)
**Evidence:**
- sincg(π·h, Na) vs sincg(h·π, Na) produces different results
- nanoBragg.c:3063-3178 uses specific argument pattern
- PyTorch may have π in wrong position

**Test:** Review `src/nanobrag_torch/models/crystal.py` get_structure_factor() sincg calls

### Hypothesis 2: Na/Nb/Nc Scaling Missing (MEDIUM CONFIDENCE)
**Evidence:**
- F_latt components scale with cell counts
- Magnitude difference ~10× could indicate missing Na/Nb/Nc factor
- C multiplies sincg result by cell counts

**Test:** Check if PyTorch multiplies sincg output by Na/Nb/Nc

### Hypothesis 3: Fractional Miller Calculation (LOW CONFIDENCE)
**Evidence:**
- hkl_frac differs by ~0.1
- Could cascade from pix0 difference
- Less likely given reciprocal vectors match

**Test:** Verify h = q·a* calculation directly

## Diagnostic Calculations

### Manual sincg Verification
Using C values from trace:
```
h_frac = 2.001203
k_frac = 1.992798
l_frac = -12.990767
Na = Nb = Nc = 5

F_latt_a = sincg(π × 2.001203, 5) = ?
F_latt_b = sincg(π × 1.992798, 5) = ?
F_latt_c = sincg(π × -12.990767, 5) = ?
```

Expected from C: 35.889, 38.632, 25.702
Need to compute these with Python sincg to isolate the bug.

## Follow-Up Actions

1. **Read nanoBragg.c lattice calculation** (lines 3063-3178)
   - Extract exact sincg argument pattern
   - Note any Na/Nb/Nc multiplication

2. **Review PyTorch sincg usage**
   - Check `src/nanobrag_torch/models/crystal.py`
   - Verify argument order in get_structure_factor()

3. **Add targeted test**
   - Feed exact C hkl_frac values to PyTorch sincg
   - Compare output to C F_latt components
   - Isolates sincg vs Miller index issues

4. **Fix and validate**
   - Apply correction to sincg usage
   - Rerun trace harness
   - Verify F_latt matches within 0.5% (Phase H exit criteria)

## Code References

- PyTorch sincg: `src/nanobrag_torch/utils/physics.py`
- PyTorch lattice calc: `src/nanobrag_torch/models/crystal.py` (get_structure_factor)
- C reference: `nanoBragg.c:3063-3178`
- Trace harness: `reports/2025-10-cli-flags/phase_h/trace_harness.py`
