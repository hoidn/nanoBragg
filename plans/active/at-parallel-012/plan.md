# Plan: AT-PARALLEL-012 Triclinic Rotation Divergence

**Status:** Active (supervisor-created)
**Priority:** High blocker for AT-PARALLEL-012 parity
**Related fix_plan item:** `[AT-PARALLEL-012]` (docs/fix_plan.md)
**Created:** 2025-09-30 by galph

## Why this plan exists
- AT-PARALLEL-012 triclinic P1 case still fails correlation (≈0.960 < 0.9995) while other metrics (sum_ratio, peak alignment) pass.
- Latest debug loop (Attempt #13, 2025-09-30) identified the **first divergence**: PyTorch misset rotation yields reciprocal vectors differing by 0.5–1.6 % from C (`reports/2025-09-30-AT-012-debug/FIRST_DIVERGENCE.md`).
- This contradicts the earlier “precision-only” hypothesis; the rotation pipeline needs rigorous parity verification.
- Without a coordinated plan, Ralph risks oscillating between verification loops and partial traces, stalling progress.

## Context you MUST read before coding
1. `specs/spec-a-parallel.md` — AT-PARALLEL-012 acceptance criteria.
2. `docs/architecture/crystal.md` — rotation pipeline contract (Core Rules #12 & #13).
3. `docs/architecture/pytorch_design.md` §§3.2–3.4 — lattice tensor computation & rotation order.
4. `docs/development/c_to_pytorch_config_map.md` — mapping for `-misset` / spindle conventions.
5. `docs/debugging/detector_geometry_checklist.md` — guardrails for geometry debugging.
6. C reference: `golden_suite_generator/nanoBragg.c` lines 1911–2117 (misset application + reciprocal regen) and 3581–3654 (`rotate`, `rotate_axis`, `rotate_umat`).
7. Prior debug artifacts: `reports/2025-09-30-AT-012-debug/` (especially `FIRST_DIVERGENCE.md`, `c_run.log`, `py_trace.log`, `generate_py_trace.py`).

## Reproduction checklist (baseline before any edits)
Run from repo root with `NB_C_BIN=./golden_suite_generator/nanoBragg` and `KMP_DUPLICATE_LIB_OK=TRUE`:
```bash
NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_parity_matrix.py -k "AT-PARALLEL-012 and triclinic"
```
Expected failure metrics (current baseline): corr≈0.9605, sum_ratio≈1.00045, max|Δ|≈48.

## Investigation phases

### Phase A — Rotation matrix equivalence (no code changes yet)
- Generate the exact 3×3 rotation matrix C uses for angles (-89.968546°, -31.328953°, 177.753396°) by instrumenting `rotate()` or adding a quick C harness (store under `reports/2025-09-30-AT-012-debug/`).
- In Python, call `angles_to_rotation_matrix` with the same angles (converted to radians) and dump the matrix.
- Compare entries element-wise; confirm the ~1 % deltas cited in Attempt #13 and log the diff into `reports/2025-09-30-AT-012-debug/rotation_matrix_comparison.md`.
- Verify determinant (+1) and orthogonality for both matrices to rule out numerical drift.

### Phase B — Trace alignment for lattice tensors
- Using `generate_py_trace.py`, emit the rotated `a*, b*, c*` vectors after each stage (pre-misset, post-misset, post-recalc) for both C and PyTorch.
- Ensure rotation matrices identified in Phase A feed directly into these vectors (no hidden conversions).
- Document the first component-wise divergence with precise locations (e.g., `crystal.py:975` vs `nanoBragg.c:1954`).

### Phase C — Hypothesis tests (pick highest value first)
1. **Euler convention mismatch:** confirm PyTorch composes rotations as `Rz @ Ry @ Rx` while C applies X→Y→Z sequentially; if mismatch, adjust implementation or reorder multiplications.
2. **Column vs row vector orientation:** verify `rotate_umat` uses the same convention as C (`umat` multiplied on the left). Check if transposing the matrix resolves the diff.
3. **Angle sign/units:** ensure degrees→radians conversion (including negative angles) matches C exactly; inspect for accidental negation or wraparound.
4. **Numeric tolerances:** if matrices match when computed in pure NumPy double-precision, isolate the layer (e.g., caching, dtype conversions) that introduces the delta.
Each falsified hypothesis must be logged in `docs/fix_plan.md` Attempts History (include command and artifact path).

### Phase D — Implement the fix
- Once the divergence source is confirmed, modify the minimal code region (`utils/geometry.py::angles_to_rotation_matrix` or downstream application) to restore parity.
- Update/add targeted unit tests (e.g., add `tests/test_geometry.py::test_angles_to_rotation_matrix_matches_c`) comparing against known matrices from C for representative angle sets.
- Maintain differentiability: avoid `.item()` on tensors tied to gradients.
- If matrix transpose/order is corrected, audit all call sites (misset + detector rotations) for consistent orientation.

### Phase E — Validation
1. Re-run AT-PARALLEL-012 triclinic parity test (command above) — require corr ≥ 0.9995, sum_ratio within [0.98, 1.02], identical max pixel coordinates.
2. Spot-check simpler cases (simple_cubic, tilted detector) to guard against regressions.
3. Run focused unit tests you added plus `pytest tests/test_at_parallel_012.py -v`.
4. If feasible, rerun the parity matrix subset (AT-020) to ensure no secondary regressions.
5. Archive new artifacts under `reports/<date>-AT-012-rotation-fix/` and cross-link in fix_plan Attempt entry.

## Exit criteria
- Rotation matrix parity proven: Python and C matrices match to ≤1e-9 element-wise for the triclinic misset angles (and at least one additional sanity case).
- AT-PARALLEL-012 triclinic test passes with correlation ≥ 0.9995 and aligned peak positions.
- Fix documented in `docs/fix_plan.md` Attempt (root cause, change summary, artifacts) and this plan marked complete (move to `plans/archive/`).
- No regressions in previously passing AT-PARALLEL cases.

## Notes for Ralph
- This plan **requires** using `prompts/debug.md`; do not revert to `prompts/main.md` until AT-012 passes.
- Keep commits scoped: rotation matrix refactor should not touch detector geometry unless evidence forces it.
- If the divergence persists after Phases A–C with matrices matching, escalate to galph with updated evidence before altering thresholds/spec.
