# Plan: AT-PARALLEL-012 Triclinic Rotation Divergence

## Context
- Initiative: AT-PARALLEL-012 parity recovery
- Phase Goal: Match nanoBragg C misset + rotation pipeline so the triclinic P1 parity harness reaches corr ≥ 0.9995 with aligned peak coordinates.
- Dependencies: `specs/spec-a-parallel.md`, `docs/architecture/crystal.md`, `docs/architecture/pytorch_design.md` §§3.2–3.4, `docs/development/c_to_pytorch_config_map.md`, `docs/debugging/detector_geometry_checklist.md`, `golden_suite_generator/nanoBragg.c` lines 1911–2117 & 3581–3654, `reports/2025-09-30-AT-012-debug/` artifacts.
- Baseline Failure Snapshot: Attempt #13 captured corr=0.9605, sum_ratio≈1.00045, max pixel mismatch (C 368,262 vs Py 223,159) in `reports/2025-09-30-AT-012-debug/FIRST_DIVERGENCE.md`.
- WIP Risk: Commit 058986f reordered misset handling but also replaced the Core Rule #13 volume recalculation (`V_actual`) with formula `V_star`; this regresses metric duality and must be corrected before further diagnostics.
- Reproduction Command: `NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_parity_matrix.py -k "AT-PARALLEL-012 and triclinic"`.
- Prompt Routing: Ralph must work under `prompts/debug.md` until this checklist is complete.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A0 | Baseline failure + first divergence captured (Attempt #13) | [D] | Artifacts already in `reports/2025-09-30-AT-012-debug/`; reference this log in future attempts instead of re-running verification loops. |
| A1 | Dump C rotation matrix for triclinic misset angles | [ ] | Instrument `rotate()` or build a one-off harness under `reports/2025-09-30-AT-012-debug/rotation_matrix_c.log`; reuse existing trace instrumentation per SOP. |
| A2 | Dump PyTorch rotation matrix with `angles_to_rotation_matrix` for the same angles | [ ] | Use a small script (can extend `generate_py_trace.py`) to log the 3×3 matrix at double precision; ensure device/dtype parity. |
| A3 | Record element-wise diff + determinants in `rotation_matrix_comparison.md` | [ ] | Compute absolute/relative deltas and determinants, confirm both matrices remain orthonormal; store alongside traces. |
| B1 | Align lattice tensor traces (pre-/post-misset, post-recalc) C vs PyTorch | [ ] | Extend trace tooling to dump `a*,b*,c*` and `a,b,c` vectors at each stage; tabulate first component where Py diverges. |
| B2 | Document divergence line references in fix_plan Attempts History | [ ] | After B1, update `docs/fix_plan.md` (AT-012 Attempt #14+) with exact file:line references and artifact paths. |
| C0 | Restore metric duality by using `V_actual` when regenerating reciprocal vectors | [ ] | Undo the 058986f regression: compute `V_actual = torch.dot(a_vec, b_cross_c)` and use it (with ε clamp) so `a·a*`, `b·b*`, `c·c*` equal 1 within 1e-12; verify `tests/test_units.py::test_metric_duality` locally. |
| C1 | Validate Euler composition order matches C (`rotate` sequence) | [ ] | Confirm PyTorch multiplies rotation matrices with the same X→Y→Z semantics; if not, adjust `angles_to_rotation_matrix` and document findings in artifacts. |
| C2 | Check column vs row vector orientation in `rotate_umat` usage | [ ] | Ensure matrices act on column vectors like C; test by transposing candidate matrices and comparing against C trace outputs. |
| C3 | Confirm angle sign and degree→radian conversions for negative angles | [ ] | Build a quick table comparing `angles_to_rotation_matrix` vs C for sign-flipped inputs; store CSV/log for reference. |
| D1 | Implement minimal code fix to eliminate rotation matrix deltas | [ ] | Modify `utils/geometry.py` and/or misset pipeline to match C outputs without violating differentiability; include required C-code docstrings. |
| D2 | Add targeted unit test covering triclinic misset rotation parity | [ ] | E.g., create `tests/test_geometry.py::test_triclinic_misset_matches_c` using hard-coded C matrices (double precision). |
| D3 | Re-run cell tensor metric duality checks after fix | [ ] | Execute `pytest tests/test_units.py::TestCrystalGeometry::test_metric_duality -v`; ensure ≤1e-12 max deviation and update artifacts if tolerances adjust. |
| E1 | Re-run parity harness for AT-PARALLEL-012 triclinic case | [ ] | Command above; require corr ≥0.9995, sum_ratio in [0.98,1.02], identical peak pixels; archive metrics in `reports/<date>-AT-012-rotation-fix/metrics.json`. |
| E2 | Spot-check simple_cubic + tilted detector cases for regressions | [ ] | `pytest -v tests/test_parity_matrix.py -k "AT-PARALLEL-012 and simple_cubic"` plus AT-024 smoke; confirm metrics unchanged. |
| E3 | Update `docs/fix_plan.md` with root cause + fix, then archive plan | [ ] | Append Attempt entry with summary, reproduction commands, and metrics; move this file to `plans/archive/` once complete. |
| E4 | Escalate to galph if parity still <0.9995 after D-stage changes | [ ] | Provide rotation matrix logs + parity metrics so supervisor can reassess before any threshold adjustments. |

## Notes
- Keep all diagnostics under `reports/2025-09-30-AT-012-debug/` or a dated sibling (no scatter under repo root).
- Do not modify detector geometry while this plan is active; focus strictly on the crystal rotation pipeline.
- Maintain C-code references per Implementation Rule #11 when touching geometry helpers.
