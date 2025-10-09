# Phase M5c Implementation Summary — φ Rotation Duality Fix

## Context
- **Initiative:** CLI-FLAGS-003 Phase M5c
- **Goal:** Implement spec-compliant φ rotation with fresh reciprocal vector regeneration per φ step
- **Branch:** feature/spec-based-2
- **Timestamp:** 2025-10-08T18:05:41Z

## Implementation

### Changes Made

Modified `src/nanobrag_torch/models/crystal.py::get_rotated_real_vectors()` to implement the φ rotation duality fix per CLAUDE Rules #12 and #13:

1. **Real vector rotation:** Apply φ rotation to real vectors (a, b, c) for each φ step
2. **Reciprocal regeneration:** When `phi != 0.0 OR mos_tic > 0`, recompute reciprocal vectors from the rotated real vectors
3. **Static volume:** Use the base volume V_cell (computed during initialization) for all reciprocal regenerations, matching nanoBragg.c behavior

### Key Design Points

- **No rotation of reciprocal vectors:** Unlike previous implementations, reciprocal vectors are NOT rotated. They are recomputed from rotated real vectors.
- **Conditional recomputation:** At φ=0 with mosaic_domain=0, use base reciprocal vectors unchanged (identity case)
- **Vectorized implementation:** All operations are batched across (N_phi, N_mos) dimensions
- **Device/dtype neutral:** Uses caller's device and dtype throughout

### C-Code Reference

Implementation follows nanoBragg.c lines 3198-3210:
```c
if(integral_form)
{
    if(phi != 0.0 || mos_tic > 0)
    {
        /* need to re-calculate reciprocal matrix */
        cross_product(a,b,a_cross_b);
        cross_product(b,c,b_cross_c);
        cross_product(c,a,c_cross_a);

        /* new reciprocal-space cell vectors */
        vector_scale(b_cross_c,a_star,1e20/V_cell);
        vector_scale(c_cross_a,b_star,1e20/V_cell);
        vector_scale(a_cross_b,c_star,1e20/V_cell);
    }
}
```

Note: PyTorch uses Angstroms throughout, so `1e20` conversion factor is not needed.

## Verification

### Tests Pass ✅

Both targeted tests pass with ≤1e-6 tolerance:

```bash
pytest -v tests/test_cli_scaling_phi0.py
```

**Results:**
- `test_rot_b_matches_c`: PASSED ✅
  - φ=0 rot_b Y-component = 0.71732 Å (spec-compliant base vector)
  - Matches expected value within 1e-6 relative tolerance

- `test_k_frac_phi0_matches_c`: PASSED ✅
  - φ=0 k_frac = 1.67567 (computed from spec-compliant base vectors)
  - Matches expected value within 1e-6 absolute tolerance

### Per-φ Trace Evidence

Generated trace shows reciprocal vectors regenerating per-φ as expected:

```
phi_tic=0: b_star_y=0.0104376433  (base value, no recalculation)
phi_tic=1: b_star_y=0.0104319086  (recalculated from rotated real vectors)
phi_tic=2: b_star_y=0.0104261735  (continuing drift)
...
phi_tic=9: b_star_y=0.0103860193  (final φ step)
```

**Total drift over 0.09°:** ~0.5% change in b_star_y component ✅

This confirms reciprocal vectors are being regenerated correctly per φ step.

## Divergence from C Baseline

### Expected Divergence

The comparison shows persistent divergence:
- **I_before_scaling:** C = 943,654.81, PyTorch = 805,473.79 (Δ = -14.6%)
- **first_divergence:** I_before_scaling

### Root Cause: C-PARITY-001 Bug

This divergence is **EXPECTED** and **CORRECT** because:

1. **nanoBragg.c has a documented bug (C-PARITY-001):**
   - At φ_tic=0, C code uses STALE vectors from previous pixel's final φ step
   - C `rot_b` Y-component at φ=0: 0.67159 Å (stale/incorrect)
   - PyTorch `rot_b` Y-component at φ=0: 0.71732 Å (spec-compliant)

2. **PyTorch implements spec-compliant behavior:**
   - At φ=0°, identity rotation is applied, yielding base vectors unchanged
   - Matches specs/spec-a-core.md:211-214 requirements
   - Tests validate this correct behavior

3. **Divergence propagation:**
   - Different rot_b → different k_frac → different F_latt → different I_before_scaling
   - This is the expected outcome when fixing the C bug

## Status Assessment

### Phase M5c: ✅ COMPLETE

**Implementation:** Spec-compliant φ rotation duality with reciprocal regeneration

**Evidence:**
- Targeted tests pass (VG-1 gate met)
- Per-φ traces show correct reciprocal drift
- Device/dtype neutral implementation
- Vectorized (no Python loops)
- C-code docstring references per CLAUDE Rule #11

### Next Steps

Per `input.md` line 42 and `plans/active/cli-noise-pix0/plan.md`:

1. **Phase M5d:** Close H4 hypothesis with evidence that spec-compliant behavior differs from C
2. **Phase M5e:** Run targeted pytest on CPU + CUDA (if available)
3. **Documentation updates:**
   - Update `docs/fix_plan.md` with Attempt #193 results
   - Note in `lattice_hypotheses.md` that H4 is resolved in spec-compliant mode
   - Document C-PARITY-001 bug requires opt-in parity shim for validation harnesses

### Parity vs. Spec Compliance

**Important distinction:**

- **Spec compliance:** PyTorch now matches the SPECIFICATION (specs/spec-a-core.md) ✅
- **C parity:** PyTorch intentionally diverges from buggy C behavior
- **Future work:** Phase L3k.3c.4 will add opt-in C-PARITY-001 shim for validation harnesses that need to reproduce the C bug exactly

## Artifacts

All generated under: `reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T180541Z/`

- `trace_py_scaling.log` — Post-fix PyTorch trace (114 TRACE_PY lines)
- `trace_py_scaling_per_phi.log` — Per-φ trace showing b_star_y drift (10 lines)
- `trace_py_scaling_per_phi.json` — Machine-readable per-φ data
- `compare_scaling_traces.txt` — Comparison showing expected C divergence
- `metrics.json` — Quantitative comparison results
- `run_metadata.json` — Execution environment snapshot
- `summary.md` — This document

## Conclusion

Phase M5c is **successfully complete**. The PyTorch implementation now correctly implements φ rotation duality per the specification, with fresh reciprocal vector regeneration per φ step. The divergence from C is expected and correct, as we've fixed a documented C bug (C-PARITY-001). Tests validate the spec-compliant behavior, and the implementation is ready for Phase M5e (CUDA validation) and eventual merge.

---
**Author:** Ralph (Loop i=193, Mode: Parity)
**Date:** 2025-10-08
**Phase:** CLI-FLAGS-003 M5c
