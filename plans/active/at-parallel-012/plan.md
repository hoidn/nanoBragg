# Plan: AT-PARALLEL-012 Triclinic Rotation Divergence

## Context
- Initiative: AT-PARALLEL-012 parity recovery
- Phase Goal: Match nanoBragg C misset + rotation pipeline so the triclinic P1 parity harness reaches corr ≥ 0.9995 with aligned peak coordinates.
- Dependencies: `specs/spec-a-parallel.md`, `docs/architecture/crystal.md`, `docs/architecture/pytorch_design.md` §§3.2–3.4, `docs/development/c_to_pytorch_config_map.md`, `docs/debugging/detector_geometry_checklist.md`, `golden_suite_generator/nanoBragg.c` lines 1911–2119 & 3581–3654, `reports/2025-09-30-AT-012-debug/` artifacts.
- Baseline Failure Snapshot: Attempt #13 captured corr=0.9605, sum_ratio≈1.00045, max pixel mismatch (C 368,262 vs Py 223,159) in `reports/2025-09-30-AT-012-debug/FIRST_DIVERGENCE.md`.
- Regression Context: Commits 058986f/7f6c4b2 reordered misset handling and replaced Core Rule #13’s `V_actual` recomputation with formula `V_star`, loosening unit-test tolerances to 3e-4 yet still leaving triclinic parity failing (corr≈0.9658). Commit f0aaea7 incorrectly marked the effort “complete” without new artifacts.
- Prompt Routing: Ralph must work under `prompts/debug.md` until this plan is retired.
- Reproduction Command: `NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_parity_matrix.py -k "AT-PARALLEL-012 and triclinic"`.

### Phase A — Rotation Matrix Parity Diagnostics
Goal: Prove whether PyTorch’s `angles_to_rotation_matrix` matches C for the triclinic misset angles.
Prereqs: Baseline failure artifacts from Attempt #13 archived under `reports/2025-09-30-AT-012-debug/`.
Exit Criteria: C and PyTorch rotation matrices logged with diff summary and determinant/orthogonality checks stored in plan artifacts.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Dump C rotation matrix for triclinic misset | [ ] | Instrument `rotate()` or reuse existing trace harness; save as `rotation_matrix_c.log` under `reports/2025-09-30-AT-012-debug/`. |
| A2 | Dump PyTorch rotation matrix via `angles_to_rotation_matrix` | [ ] | Extend `generate_py_trace.py` (float64, device parity) to log 3×3 matrix into `rotation_matrix_py.log`. |
| A3 | Compare matrices and determinants | [ ] | Produce `rotation_matrix_comparison.md` detailing abs/rel deltas and determinant/orthonormality checks. |

### Phase B — Lattice Tensor Trace Alignment
Goal: Identify the first divergence between C and PyTorch lattice tensors after misset application.
Prereqs: Phase A comparison complete.
Exit Criteria: Trace tables for `a*,b*,c*` and `a,b,c` recorded for both implementations with divergence line numbers captured in fix_plan.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Capture lattice tensor traces pre-/post-misset (C & PyTorch) | [ ] | Extend trace tooling to log reciprocal + real vectors at each stage; place CSV/Markdown under `reports/2025-09-30-AT-012-debug/`. |
| B2 | Update fix_plan with trace divergence references | [ ] | Note exact file:line offsets for the first mismatch and link to trace artifacts in `docs/fix_plan.md` AT-012 attempts. |

### Phase C — Metric Duality Restoration & Hypothesis Tests
Goal: Reinstate Core Rule #13 invariants and validate rotation conventions.
Prereqs: Phase B traces analysed.
Exit Criteria: Metric duality restored to ≤1e-12 tolerance and orientation hypotheses either confirmed or ruled out with logged evidence.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C0 | Restore `V_actual` usage when regenerating reciprocal vectors | [ ] | Revert 058986f/7f6c4b2 change; compute `V_actual = torch.dot(a_vec, b_cross_c).clamp_min(1e-6)` and reuse for reciprocal vectors; rerun `pytest tests/test_crystal_geometry.py::TestCrystalGeometry::test_metric_duality`. |
| C1 | Validate Euler composition order matches C | [ ] | Compare multiplication ordering (X→Y→Z) using traces; document findings in `rotation_matrix_comparison.md`. |
| C2 | Confirm matrix orientation (row vs column) alignment | [ ] | Apply both conventions to traced vectors; ensure PyTorch matches C’s column-vector multiplication; log in phase artifacts. |
| C3 | Check angle sign/degree→radian handling for negative angles | [ ] | Generate quick sweep (± angles) and record results in `rotation_sweep.csv`; link from fix_plan. |

### Phase D — Implementation & Unit Tests
Goal: Implement the minimal code fix informed by diagnostics and reinstate strict tests.
Prereqs: Phase C outcomes demonstrate exact divergence cause.
Exit Criteria: Code updated with C-code references, unit tests enforce 1e-12 tolerances, and metrics documented.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Implement fix in `utils/geometry.py` / crystal misset pipeline | [ ] | Update code while preserving differentiability and C-code docstrings; avoid new tensor factories. |
| D2 | Add focused unit test covering triclinic misset rotation parity | [ ] | E.g., `tests/test_geometry.py::test_triclinic_misset_matches_c` using C trace values. |
| D3 | Reinstate 1e-12 metric duality tolerances | [ ] | Revert temporary 3e-4 relaxation in `tests/test_crystal_geometry.py` once fix lands; attach diff summary to artifacts. |
| D4 | Re-run targeted geometry unit suite | [ ] | `pytest tests/test_units.py::TestCrystalGeometry::test_metric_duality -v`; store output in `reports/.../unit_results.txt`. |

### Phase E — Parity Validation & Closure
Goal: Demonstrate restored AT-012 parity and ensure no regressions elsewhere.
Prereqs: Phase D code/tests passing locally.
Exit Criteria: Triclinic parity metrics meet spec, supporting cases unchanged, plan archived.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| E1 | Re-run parity harness for triclinic case | [ ] | `NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_parity_matrix.py -k "AT-PARALLEL-012 and triclinic"`; require corr ≥0.9995, matching peaks; archive metrics under `reports/<date>-AT-012-rotation-fix/`. |
| E2 | Spot-check simple_cubic + tilted cases | [ ] | `pytest -v tests/test_parity_matrix.py -k "AT-PARALLEL-012 and (simple_cubic or tilted)"`; confirm unchanged metrics. |
| E3 | Update fix_plan with root cause, fix summary, and artifacts | [ ] | Append Attempt entry with reproduction commands and outcome; cite plan completion. |
| E4 | Archive plan or escalate if parity still <0.9995 | [ ] | If failure persists, package Phase A–E artifacts for supervisor review before further code churn. |

## Notes
- Keep diagnostics consolidated under `reports/2025-09-30-AT-012-debug/` (or sibling dated directory) to avoid scattering artifacts.
- Do not alter detector geometry while this plan is active; focus strictly on the crystal rotation pipeline.
- Maintain C-code references per Implementation Rule #11 when editing helpers.
- Once C0 succeeds, immediately reinstate the 1e-12 metric-duality tolerances to enforce Core Rule #13.
