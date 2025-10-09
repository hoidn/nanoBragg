# Phase M5c Prep — nanoBragg.c Rotation & Duality Reference

## Context
- Initiative: CLI-FLAGS-003 Phase M5c (φ rotation realignment)
- Goal: Provide the exact nanoBragg.c snippets that enforce Rules #12/#13 so Ralph can port them with CLAUDE Rule #11 docstrings when updating `Crystal.get_rotated_real_vectors`.
- Source files consulted: `golden_suite_generator/nanoBragg.c` lines 2053-2278 (static setup) and 3192-3210 (per-φ recompute).
- Specs consulted: `specs/spec-a-core.md:204-240` (misset + φ rotation order), `specs/spec-a-core.md:241-252` (Rule #13 reciprocal regeneration).

## Key Observations
1. **Static misset pipeline (lines 2053-2278)**
   - MOSFLM matrix vectors are wavelength-corrected (`vector_scale(..., 1e-10/lambda0)`).
   - Static misset rotates the reciprocal vectors (`rotate(a_star, ...)`) before any real-space vectors exist.
   - Real vectors `a,b,c` are rebuilt from `b_star × c_star` etc. using the *actual* direct-space volume `V_cell = 1/V_star`.
   - Reciprocal vectors are then regenerated from the recomputed `a,b,c` using the actual volume as the scaling factor (`vector_scale(b_cross_c, a_star, V_star)`). This enforces Rule #13 duality (a·a* = 1 exactly).

2. **Per-φ recompute (lines 3192-3210)**
   - Inside the integral form branch, whenever `phi != 0.0` or a mosaic domain applies, the code recomputes `a_star/b_star/c_star` from the *current* real vectors before evaluating lattice factors.
   - The scale factor `1e20/V_cell` is the Angstrom→meter conversion squared (Angstrom^2) baked into the volume term; PyTorch must preserve this to avoid drift.
   - This recomputation uses the already-rotated real vectors (`a,b,c`), so the rotation ordering is: static misset on reciprocal → derive real vectors → dynamic φ rotation on real vectors → regenerate reciprocal vectors per φ/mosaic tick.

3. **Volume source**
   - `V_cell` is derived from the dot product `a_star · (b_star × c_star)` *after* misset rotation, so any φ tick must reuse the same actual volume; do not fall back to formula volume from cell parameters.

## Guidance for M5c Implementation
- Update `Crystal.get_rotated_real_vectors` (or equivalent pipeline) to: 
  1. Start from cached reciprocal vectors that already contain static misset.
  2. Rebuild real vectors via cross products and `V_cell` computed from those reciprocal vectors.
  3. Apply φ rotation (and mosaic rotation when enabled) to the *real* vectors.
  4. Recompute reciprocal vectors from the rotated real vectors before computing `h,k,l`, matching the `1e20/V_cell` scale factor.
- Maintain vectorized tensor operations across φ ticks and mosaic domains; avoid Python loops.
- Add Rule #11 docstrings quoting the included C snippets with the exact line numbers.
- Device/dtype neutrality: reuse the dominant tensor dtype/device when forming cross products and volumes.

## Next Steps
1. Embed these snippets into the docstring of the new helper that enforces the per-φ duality pipeline.
2. Re-run `scripts/validation/compare_scaling_traces.py` after implementation; expect `first_divergence=None`.
3. Update `reports/.../lattice_hypotheses.md` to close Hypothesis H4 once parity is confirmed.

