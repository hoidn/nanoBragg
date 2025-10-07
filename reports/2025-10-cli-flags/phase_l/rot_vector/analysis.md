# Rotation Vector Analysis — Phase L3f/L3g

**Date:** 2025-10-07
**Context:** CLI-FLAGS-003 Phase L3f/L3g rotation-vector audit to explain residual k_frac drift at φ=0

## Summary

Captured side-by-side rotation vectors from C (`c_trace_scaling.log`) and PyTorch (`trace_py_rot_vector.log`) for pixel (685, 1039) at φ=0. Analysis reveals significant differences in **real-space** rotation vectors (Angstrom scale) while **reciprocal-space** vectors show excellent agreement (~10^-9 Angstrom^-1).

## Key Findings

### Reciprocal Vectors (Excellent Agreement)
- `rot_a_star_A_inv`: Δ ≈ 2-4e-9 Angstrom^-1 (within numerical precision)
- `rot_b_star_A_inv`: Δ ≈ 7e-11 to 5e-9 Angstrom^-1 (excellent)
- `rot_c_star_A_inv`: Δ ≈ 4e-10 to 4e-9 Angstrom^-1 (excellent)

**Result:** Reciprocal vectors match C to ~9 decimal places — this is near-perfect agreement.

### Real-Space Vectors (Significant Drift)
- `rot_a_angstroms`: Δy = +8.740e-03 Å, Δz = -3.436e-02 Å
- `rot_b_angstroms`: Δy = +4.573e-02 Å, Δz = +1.089e-03 Å
- `rot_c_angstroms`: Δy = +1.529e-02 Å, Δz = -3.832e-02 Å

**Result:** Real-space vectors show O(10^-2) Angstrom differences, primarily in Y and Z components.

## Magnitude Analysis

| Vector | C Magnitude (Å) | PyTorch Magnitude (Å) | Relative Error |
| --- | --- | --- | --- |
| rot_a | 26.906 | 26.938 | 0.12% |
| rot_b | 31.442 | 31.443 | 0.00% |
| rot_c | 33.498 | 33.528 | 0.09% |

The magnitude differences are small (<0.12%), suggesting the issue is primarily **directional** rather than scale.

## Hypothesis: Cause of Drift

Given that:
1. Reciprocal vectors match to ~9 decimal places
2. Real-space vectors show O(10^-2 Å) drift in Y/Z components
3. The drift is directional (Y/Z) rather than isotropic

**Primary Hypothesis:** The divergence occurs in the **real-space reconstitution** from reciprocal vectors.

### Suspected Code Paths

1. **Reciprocal → Real Conversion** (`Crystal.py:~400-450`)
   - C: `nanoBragg.c:3006-3098` (reciprocal_to_real conversion)
   - PyTorch: `Crystal.get_real_from_reciprocal()` or similar
   - **Hypothesis:** Potential difference in cross-product order, volume calculation, or normalization

2. **Spindle Axis Application** (`Crystal.py:~1000-1050`)
   - C: `nanoBragg.c:~2800-2900` (phi rotation around spindle axis)
   - PyTorch: `Crystal.get_rotated_real_vectors()`
   - **Hypothesis:** Spindle axis normalization or rotation matrix construction may differ

3. **Metric Duality Recalculation** (Rule #13 in CLAUDE.md)
   - C performs circular recalculation: reciprocal → real → reciprocal (using actual volume)
   - PyTorch: Check if `V_actual = a · (b × c)` is used vs formula volume
   - **Hypothesis:** If PyTorch uses formula volume instead of actual volume, small errors accumulate

## Recommended Next Actions (Phase L3g)

### Immediate Probes

1. **Volume Comparison**
   - Add `TRACE_PY: cell_volume_formula <val>`
   - Add `TRACE_PY: cell_volume_actual <val>`
   - Compare with C's logged volume to identify which is used

2. **Cross-Product Order Audit**
   - Verify `a = (b* × c*) × V` vs `a = V × (b* × c*)` order
   - Check sign conventions in reciprocal-to-real conversion

3. **Spindle Axis Normalization**
   - Log `||spindle_axis||` in both C and PyTorch
   - Verify axis is properly normalized before rotation matrix construction

### Implementation Priority

Since reciprocal vectors are correct but real vectors diverge:
1. Focus on `Crystal.get_real_from_reciprocal()` implementation
2. Verify Rule #13 circular recalculation is followed
3. Check metric duality test (`test_metric_duality`) passes with current parameters

## Alignment with Spec

From `CLAUDE.md` Rule #13:
> The complete sequence is:
> 1. Build initial reciprocal vectors using the default orientation convention
> 2. Calculate real vectors from reciprocal: `a = (b* × c*) × V`
> 3. **Recalculate reciprocal vectors from real**: `a* = (b × c) / V_actual`
> 4. **Use actual volume**: `V_actual = a · (b × c)` instead of the formula volume

**Action Required:** Verify PyTorch follows this exact sequence and uses `V_actual` from the reconstituted real vectors, not the formula volume.

## Exit Criteria for Phase L3g

1. Volume values (formula vs actual) logged and compared
2. Cross-product order verified in real-space reconstitution
3. Spindle axis normalization verified
4. If drift remains >5e-4 in real-space components after corrections, escalate to supervisor

## References

- C trace: `reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log`
- PyTorch trace: `reports/2025-10-cli-flags/phase_l/rot_vector/trace_py_rot_vector.log`
- Comparison table: `reports/2025-10-cli-flags/phase_l/rot_vector/rot_vector_comparison.md`
- Plan: `plans/active/cli-noise-pix0/plan.md` Phase L3f/L3g
- Spec: `CLAUDE.md` Rules #12, #13
- C code: `nanoBragg.c:3006-3098` (reciprocal/real conversion)
