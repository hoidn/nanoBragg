# Phase M5b — φ Rotation Parity Design Memo

## Context
- Initiative: CLI-FLAGS-003 Phase M5 (φ rotation realignment) from `plans/active/cli-noise-pix0/plan.md`
- Blocking divergence: `I_before_scaling` remains ~14.6% low in PyTorch after normalization fix (see `reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/metrics.json`)
- Evidence base:
  - PyTorch enhanced per-φ traces (`reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T231211Z/trace_py_scaling_per_phi.{log,json}`)
  - C reference trace (`reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/c_trace_scaling.log`)
  - Hypothesis register (`reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md`)
- Specification references:
  - `specs/spec-a-core.md:204-240` — normative φ / mosaic rotation order and lattice factor definitions
  - `arch.md §2.2` — rotation pipeline design intent (misset → φ → mosaic)
  - CLAUDE Rules #12 & #13 — static misset applied to reciprocal vectors, then real and reciprocal vectors must be recomputed to enforce metric duality
  - `docs/bugs/verified_c_bugs.md:166-204` — C-PARITY-001 dossier (φ=0 carryover bug is C-only)

## Current Observations
- PyTorch `k_frac` spans −0.589→−0.607 across φ ticks, whereas C holds −0.607 at φ₀ and repeats the sequence every 0.09°.
- PyTorch `b_star_y` drifts from 1.04376e−02 to 1.03860e−02 across the sweep; C keeps 1.03860e−02 stable within 1e−6.
- `F_latt` flips sign in PyTorch (positive at φ₀) but remains negative in C, driving the 14.6% deficit in `I_before_scaling`.
- Enhanced traces confirm that PyTorch rotates real vectors correctly but fails to preserve the C-code reciprocal pipeline. The mismatch shows up before sincg: the scattering vector S is identical between traces while `rot_*_star` components deviate by 5e−5.

## C-Code Pipeline (Authoritative Reference)
Key excerpt from `golden_suite_generator/nanoBragg.c:3042-3210`:
```c
for(phi_tic = 0; phi_tic < phisteps; ++phi_tic) {
    phi = phi0 + phistep*phi_tic;
    if (phi != 0.0) {
        rotate_axis(a0, ap, spindle_vector, phi);
        rotate_axis(b0, bp, spindle_vector, phi);
        rotate_axis(c0, cp, spindle_vector, phi);
    }
    for (mos_tic = 0; mos_tic < mosaic_domains; ++mos_tic) {
        if (mosaic_spread > 0.0) {
            rotate_umat(ap, a, &mosaic_umats[mos_tic*9]);
            rotate_umat(bp, b, &mosaic_umats[mos_tic*9]);
            rotate_umat(cp, c, &mosaic_umats[mos_tic*9]);
        } else {
            a = ap; b = bp; c = cp;
        }
        h = dot_product(a, scattering);
        k = dot_product(b, scattering);
        l = dot_product(c, scattering);
        if (integral_form) {
            if (phi != 0.0 || mos_tic > 0) {
                cross_product(a, b, a_cross_b);
                cross_product(b, c, b_cross_c);
                cross_product(c, a, c_cross_a);
                vector_scale(b_cross_c, a_star, 1e20 / V_cell);
                vector_scale(c_cross_a, b_star, 1e20 / V_cell);
                vector_scale(a_cross_b, c_star, 1e20 / V_cell);
            }
        }
        /* sincg + accumulation */
    }
}
```

Important notes:
1. **Base orientation** (`a0`, `b0`, `c0`) is already misset-aware and stored in meters.
2. **Per-φ rotation** uses `rotate_axis` on the base real vectors only; φ=0 must return the unrotated lattice.
3. **Reciprocal vectors** are recomputed from the rotated real vectors (once φ ≠ 0 or mosaic ≠ 0) using the *static* cell volume `V_cell` acquired during initialization (Angstrom³). The `1e20` factor covers meter→Angstrom conversion.
4. **Metric duality** is implicitly restored because the cross-product / volume scaling pipeline mirrors Rule #13.
5. **Carryover bug** arises because ap/bp/cp are captured as `firstprivate` values in OpenMP and not reset when φ=0. Our PyTorch path must **not** reproduce this.

## Diagnosis of the PyTorch Path (`Crystal.get_rotated_real_vectors`)
- Rotates real vectors via `rotate_axis`, but immediately forms reciprocal vectors as `cross(b_phi, c_phi) / self.V`. This omits the explicit duality recomputation cycle required by CLAUDE Rules #12/#13.
- Uses base `self.V` (already in Å³) but never recomputes `V_star_actual = dot(a_phi, cross(b_phi, c_phi))`. As a result, numerical drift accumulates across φ ticks when evaluated in float64.
- Mosaic rotations are applied by multiplying both real and reciprocal vectors with the same rotation matrices instead of re-deriving reciprocals from the rotated real vectors. Although orthonormal rotations should commute, the combination of float32 defaults and the missing duality correction leads to the observed 5e−5 skew in `b_star_y`.
- Per-φ ordering is inverted relative to the C trace because reciprocal vectors are computed before the mosaic/duality pipeline, effectively mirroring the φ sweep.

## Design Requirements for Phase M5c
1. **Vectorized Rotation Matrices**
   - Construct Rodrigues rotation matrices for all φ steps: `R_phi ∈ ℝ^{N_phi×3×3}` using the spindle axis (unitised) and angles `phi_tic` per spec.
   - Broadcast mosaic rotation matrices `U_mos ∈ ℝ^{N_mos×3×3}` (identity when mosaic spread = 0).
   - Compose to obtain `R_total = R_phi @ U_mos` with broadcast to `(N_phi, N_mos, 3, 3)`.

2. **Apply Rotations to Base Vectors**
   - Base real vectors (Angstrom) after misset: `a0 = self.a`, `b0 = self.b`, `c0 = self.c`.
   - Base reciprocal vectors (Å⁻¹) after misset: `a0* = self.a_star`, etc.
   - Rotate real vectors: `a_rot = R_total @ a0`, etc.
   - Rotate reciprocal vectors *temporarily* for use in duality enforcement: `a_star_rot = R_total @ a0*`, etc.

3. **Duality Enforcement (Rule #12 / #13)**
   - Compute actual reciprocal volume per φ/mosaic tile:
     - `V_star_actual = dot(a_star_rot, cross(b_star_rot, c_star_rot))`
     - Safeguard with `clamp_min(1e-18)` to avoid division-by-zero.
   - Derive direct volume: `V_actual = 1 / V_star_actual` (Å³).
   - Rebuild real vectors from rotated reciprocal vectors:
     - `a_real = cross(b_star_rot, c_star_rot) * V_actual`
     - `b_real = cross(c_star_rot, a_star_rot) * V_actual`
     - `c_real = cross(a_star_rot, b_star_rot) * V_actual`
   - Recalculate reciprocal vectors from the refreshed real vectors using `V_actual`:
     - `a_star_final = cross(b_real, c_real) / V_actual`
     - Recompute `V_star_final = dot(a_star_final, cross(b_star_final, c_star_final))` as a consistency check (should equal `1/V_actual`).
   - Result: `a_real`, `b_real`, `c_real` in Å; `a_star_final`, `b_star_final`, `c_star_final` in Å⁻¹ with metric duality enforced per slice.

4. **Preserve Vectorization & Device Neutrality**
   - Avoid Python loops; rely on tensor broadcasting for `(N_phi, N_mos, 3)` shapes.
   - Ensure all temporaries use `dtype=self.dtype` and the dominant device; no `.cpu()` / `.cuda()` calls.
   - Use `torch.linalg.cross` or `torch.cross` with `dim=-1` for batched operations.
   - Guard degenerate volumes using `clamp_min`; raise descriptive errors if `V_actual` underflows beyond tolerance (should not happen for physical inputs).

5. **Interface Contract**
   - `get_rotated_real_vectors` should continue returning tuples `((a,b,c), (a*,b*,c*))` with shapes `(N_phi, N_mos, 3)`.
   - φ carryover caches remain disabled; the fix must not reintroduce shim logic.
   - Keep docstring C reference (Rule #11) but refresh snippet to include the reciprocal recomputation block above.

## Verification Plan (Phase M5d / M5e)
1. **Trace Harness**
   - Rerun `trace_harness.py --emit-rot-stars` and compare against the C trace.
   - Success criterion: `rot_*` vectors, `k_frac`, `F_latt` agree within ≤1e-6 relative tolerance for all φ ticks.
2. **Scaling Comparison**
   - Execute `scripts/validation/compare_scaling_traces.py` with fresh artifact bundle `fix_<timestamp>`.
   - Expect `first_divergence = None` and identical `I_before_scaling`.
3. **Targeted Tests**
   - `pytest -v tests/test_cli_scaling_phi0.py` (CPU mandatory) and CUDA smoke when available.
   - Update `reports/.../lattice_hypotheses.md` closing H4/H5 with post-fix metrics.
4. **Regression Guard**
   - Add per-φ trace regression (CSV or JSON) under `reports/2025-10-cli-flags/phase_l/per_phi/` with SHA manifests.

## Open Questions & Follow-ups
- Confirm whether additional normalization is needed for φ ranges that cross 360° (not encountered in current harness but worth documenting once M5 closes).
- Audit `rotate_axis` numerical stability for extremely small angles; consider fallback to identity when `|phi| < 1e-12` to avoid spurious drift.
- Clean up duplicated evidence paths introduced in commit 65a9dd2 (`reports/2025-10-cli-flags/phase_l/per_phi/reports/...`). Recommend folding into a single hierarchy during Phase M5d ledger sync.

## Next Actions for Implementation (Ralph)
1. Implement the vectorized rotation + duality pipeline described above inside `Crystal.get_rotated_real_vectors` (and batch variant if needed), citing the C snippet.
2. Ensure unit conversions remain Angstrom-based for physics (no implicit meter conversions); validate against the C trace to confirm orientation and magnitude parity.
3. Run the verification plan and update `docs/fix_plan.md` Attempt log with artifact paths and outcomes.

Prepared by galph — 2025-10-08T23:20Z
