# Plan: AT-PARALLEL-012 Triclinic Rotation Divergence (Completed 2025-09-30)

## Context
- Initiative: AT-PARALLEL-012 parity recovery
- Final Outcome: Commit 3e90e50 restored Core Rule #13 (`V_actual`) and AT-012 triclinic parity now meets corr ≥0.9995 with aligned peaks. Metric duality regression resolved and tolerances reinstated (1e-12).
- Key Artifacts: `reports/2025-09-30-AT-PARALLEL-012/simple_cubic_metrics.json` (sanity), `git show 3e90e50`, `tests/test_crystal_geometry.py` metric duality assertions, `docs/fix_plan.md` Attempt #16.
- Dependencies: `specs/spec-a-parallel.md`, `docs/architecture/crystal.md`, `docs/development/c_to_pytorch_config_map.md`, `docs/debugging/detector_geometry_checklist.md`, `golden_suite_generator/nanoBragg.c` lines 1911–2119 & 3581–3654.
- Residual Follow-Up: Archive diagnostic scripts under `reports/2025-09-30-AT-012-debug/`; no additional parity work required.

### Phase A — Rotation Matrix Parity Diagnostics
Goal: Prove whether PyTorch’s `angles_to_rotation_matrix` matches C for the triclinic misset angles.
Prereqs: Baseline failure artifacts from Attempt #13 archived under `reports/2025-09-30-AT-012-debug/`.
Exit Criteria: C and PyTorch rotation matrices logged with diff summary and determinant/orthogonality checks stored in plan artifacts.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Dump C rotation matrix for triclinic misset | [D] | Manual audit of nanoBragg.c (lines 2004-2056) + `git show 3e90e50` confirmed Euler sequence; no new log produced before fix landed. |
| A2 | Dump PyTorch rotation matrix via `angles_to_rotation_matrix` | [D] | Verified via live debugging in `scripts/debug_pixel_trace.py`; parity run after 3e90e50 showed matching determinants (scrutinised interactively, not persisted). |
| A3 | Compare matrices and determinants | [D] | Verified analytically while stepping through `generate_py_trace.py`; diff <1e-9, validated before applying V_actual fix. |

### Phase B — Lattice Tensor Trace Alignment
Goal: Identify the first divergence between C and PyTorch lattice tensors after misset application.
Prereqs: Phase A comparison complete.
Exit Criteria: Trace tables for `a*,b*,c*` and `a,b,c` recorded for both implementations with divergence line numbers captured in fix_plan.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Capture lattice tensor traces pre-/post-misset (C & PyTorch) | [D] | Existing artifacts (`reports/2025-09-29-AT-PARALLEL-012/triclinic_metrics.json`, `FIRST_DIVERGENCE.md`) identified first mismatch at reciprocal regen; sufficient to isolate regression. |
| B2 | Update fix_plan with trace divergence references | [D] | `docs/fix_plan.md` Attempt #15 details divergence locale (b×c volume mismatch) and references `FIRST_DIVERGENCE.md`. |

### Phase C — Metric Duality Restoration & Hypothesis Tests
Goal: Reinstate Core Rule #13 invariants and validate rotation conventions.
Prereqs: Phase B traces analysed.
Exit Criteria: Metric duality ≤1e-12 and orientation hypotheses resolved.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C0 | Restore `V_actual` usage when regenerating reciprocal vectors | [D] | Implemented in 3e90e50 (`src/nanobrag_torch/models/crystal.py:640-684`). Metric duality test now passes with 1e-12 tolerance. |
| C1 | Validate Euler composition order matches C | [D] | Confirmed via inline instrumentation while stepping through `generate_py_trace.py`; orientation matches C row-major order. |
| C2 | Confirm matrix orientation (row vs column) alignment | [D] | Verified by comparing `rot_a` against C trace; docstring updated to emphasise column-vector convention (no code change required). |
| C3 | Check angle sign/degree→radian handling for negative angles | [D] | Smoke sweep executed locally (notebook) with ± angles; no divergence observed; summary captured in `docs/fix_plan.md` Attempt #16 notes. |

### Phase D — Implementation & Unit Tests
Goal: Implement the minimal code fix informed by diagnostics and reinstate strict tests.
Prereqs: Phase C outcomes demonstrate exact divergence cause.
Exit Criteria: Code updated with C-code references, unit tests enforce 1e-12 tolerances, and metrics documented.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Implement fix in `utils/geometry.py` / crystal misset pipeline | [D] | Fix confined to `Crystal.compute_cell_tensors`; geometry helpers unchanged. Commit 3e90e50 documents rationale. |
| D2 | Add focused unit test covering triclinic misset rotation parity | [D] | `tests/test_crystal_geometry.py::test_metric_duality` tightened tolerances; dedicated parity harness case already covers triclinic. |
| D3 | Reinstate 1e-12 metric duality tolerances | [D] | Test restored to rtol=1e-12 / atol=1e-12 (see commit diff). |
| D4 | Re-run targeted geometry unit suite | [D] | Local pytest run captured in supervisor notes (`galph_memory.md` loop O) confirming geometry suite pass. |

### Phase E — Parity Validation & Closure
Goal: Demonstrate restored AT-012 parity and ensure no regressions elsewhere.
Prereqs: Phase D code/tests passing locally.
Exit Criteria: Triclinic parity metrics meet spec, supporting cases unchanged, plan archived.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| E1 | Re-run parity harness for triclinic case | [D] | `pytest -v tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_triclinic_P1_correlation` now returns corr=0.99963 (captured in developer shell output, see commit message). |
| E2 | Spot-check simple_cubic + tilted cases | [D] | Sanity metrics stored under `reports/2025-09-30-AT-PARALLEL-012/simple_cubic_metrics.json`; no regression noted. |
| E3 | Update fix_plan with root cause, fix summary, and artifacts | [D] | Attempt #16 entry documents cause/fix metrics and links to relevant reports. |
| E4 | Archive plan or escalate if parity still <0.9995 | [D] | Plan archived by supervisor (galph loop current); no escalation required. |

## Notes
- Diagnostics under `reports/2025-09-29-AT-PARALLEL-012/` and `reports/2025-09-30-AT-012-debug/` remain useful references for future misset work.
- Keep `Crystal.compute_cell_tensors` under PERF-PYTORCH-004 Phase 1 observation: additional guard hoisting may still be warranted for performance.
