# Plan: AT-PARALLEL-021 Crystal Phi Rotation Debug

**Status:** Archived 2025-09-30 (completed; parity passing)
**Priority:** Critical blocker for AT-PARALLEL-021/022/020
**Related fix_plan item:** `[AT-PARALLEL-021-PARITY]` (docs/fix_plan.md)
**Created:** 2025-09-30

## Why this plan exists
- Parity harness metrics (`reports/2025-09-30-AT-PARALLEL-021/*.json`) show catastrophic single-step failures (corr≈0.48, sum_ratio≈0.71) and borderline multi-step failures (corr≈0.98, sum_ratio≈1.12).
- AT-PARALLEL-022 shares the identical signature, so fixing phi rotation should unblock the combined rotation test as well.
- AT-PARALLEL-020 comprehensive case likely accumulates the same bug once the phi stack, mosaic, and detector rotations interact.
- Spec references: `specs/spec-a-parallel.md` (AT-021 / AT-022 sections), Core Rules 12 & 13 (rotation pipeline + reciprocal recalculation), detector conventions in `docs/architecture/detector.md`.

## Objectives
1. Identify the **first divergence** for the single-step phi case (phisteps=1) via trace comparison.
2. Correct the phi rotation pipeline so that both single-step and multi-step cases satisfy spec thresholds (corr≥0.99, sum_ratio∈[0.9,1.1], max|Δ|<500).
3. Re-verify AT-PARALLEL-022 after the fix (it should pass without additional changes).
4. Document the fix and update `docs/fix_plan.md` Attempts History.

## Files & docs to review before touching code
- `src/nanobrag_torch/models/crystal.py` — `get_rotated_real_vectors`, `_generate_mosaic_rotations`, `_apply_static_orientation`.
- `src/nanobrag_torch/simulator.py` — rotation usage around lines ~430-580.
- C reference: `golden_suite_generator/nanoBragg` (look around lines 3000-3110 for phi/mosaic loops).
- Specs and design docs: `specs/spec-a-parallel.md` (AT-021/022), `docs/architecture/pytorch_design.md` (rotation memo), `docs/development/c_to_pytorch_config_map.md` (phi / spindle mapping), `docs/development/pytorch_runtime_checklist.md` (tensor/device guardrails).

## Reproduction checklist (run from repo root)
1. Ensure environment variables: `export NB_C_BIN=./golden_suite_generator/nanoBragg` (or fallback `./nanoBragg`), `export NB_RUN_PARALLEL=1`, prefix parity runs with `KMP_DUPLICATE_LIB_OK=TRUE`.
2. Canonical failing command (single-step first):
   ```bash
   KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=$NB_C_BIN \
   pytest tests/test_parity_matrix.py -k "AT-PARALLEL-021 and single_step_phi" -v
   ```
3. Collect metrics json & diff heatmap from `reports/2025-09-30-AT-PARALLEL-021/` as baseline; do **not** overwrite until fix succeeds.
4. Add debug loop entry in `docs/fix_plan.md` before proceeding (Status → `in_progress`).

## Investigation phases

### Phase A — Geometry sanity checks (no code changes)
- Confirm `phi_steps==1` path sets midpoint correctly:
  - Compare PyTorch phi angle to C trace (should be `phi_start + osc_range/2`).
  - Verify spindle axis default (`(0,0,1)` per spec) and dtype/device.
- Validate compliance with Core Rules 12 & 13:
  - Static misset rotates reciprocal vectors first; real vectors recomputed from rotated reciprocal; reciprocal recalculated from real using actual volume.
  - Confirm cached vectors used in phi rotation include misset results (inspect `self.a`, `self.a_star`, etc.).
- Inspect `Crystal.get_rotated_real_vectors` to ensure mosaic rotations are applied after phi rotation and return shapes `(N_phi, N_mos, 3)`.

### Phase B — Trace alignment
- Generate C trace for representative pixel:
  - Use `scripts/debug_pixel_trace.py --case at-parallel-021-single-step` (if helper exists) or run C binary with `-printout` for pixel near beam center.
  - Capture output under `reports/debug/<stamp>-AT-021/` (create new folder).
- Generate PyTorch trace with identical parameters using `scripts/debug_pixel_trace.py --impl pytorch ...` (ensure `KMP_DUPLICATE_LIB_OK=TRUE`).
- Compare values in order: phi angle, rotated lattice vectors (a,b,c and reciprocal variants), normalized scattering vector, Miller indices, F_cell / F_latt, steps normalization.
- Identify first divergence; log in `docs/fix_plan.md` Attempts History and `plans/active/at-parallel-021/investigation_log.md` (create if useful).

### Phase C — Root cause hypotheses
Common suspects to test (in order):
1. **Phi angle generation**: off-by-one step size, lacking 0.5 offset, rad/deg mismatch.
2. **Spindle axis orientation**: axis not normalized, wrong handedness, misset interaction.
3. **Rotation order**: applying mosaic before phi or reusing static vectors incorrectly.
4. **Normalization**: missing `steps` factor or double counting for multi-step path.
5. **State caching**: `self._geometry_cache` not used → recomputation inconsistent between phi and mosaic paths.

Each hypothesis should be validated/falsified via targeted trace/printf instrumentation (reuse existing debug helpers, avoid manual re-derivations per Instrumentation Rule).

### Phase D — Fix implementation outline (once divergence confirmed)
- Make minimal change in the relevant module (`Crystal` for rotation math, `Simulator` if normalization bug).
- Preserve differentiability (no `.item()` on tensors that need gradients).
- Update or add targeted unit tests if feasible (e.g., check rotated vector identity for phi=45°).
- Document fix in `docs/fix_plan.md` (Attempts History → Metrics + First Divergence + change summary).

## Validation gates (after code changes)
1. Re-run AT-021 parity cases (single and multi-step) — require corr≥0.99 and sum_ratio within [0.9,1.1].
2. Re-run AT-022 parity cases to confirm combined rotations now pass (no additional fixes expected).
3. Spot-check AT-020 comprehensive case; record updated metrics (corr, sum ratio) for traceability.
4. Run focused unit tests touching rotation (`pytest tests/test_crystal_rotation.py` if available) plus targeted subset from acceptance suite.
5. Full `pytest tests/test_parity_matrix.py -v` only after targeted passes.

## Reporting & follow-up
- Update `docs/fix_plan.md` `[AT-PARALLEL-021-PARITY]` entry with new Attempt, metrics, artifacts, and mark `Status: done` only when both AT-021 and AT-022 parity cases pass.
- Add summary to `plans/active/at-parallel-021/investigation_log.md` (if created) detailing root cause and fix.
- Notify supervisor (galph) if unexpected secondary issues appear (e.g., mosaic regressions).

## Exit criteria
- Both parity cases for AT-021 and AT-022 meet thresholds.
- Metrics artifacts stored under `reports/<date>-AT-PARALLEL-021/` and cross-referenced from fix_plan.
- No regressions in existing passing AT cases (002,006,007,023,026, etc.).
- Plan can be archived (move directory to `plans/history/` if desired) once exit criteria met.
