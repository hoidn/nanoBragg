## Context
- Initiative: CLI-FLAGS-003 / Absorption correctness — ensure detector absorption respects subpixel sampling semantics.
- Phase Goal: Restore `-oversample_thick` behaviour so absorption is evaluated per subpixel, matching C nanoBragg and spec `specs/spec-a-core.md` §4 (Sampling).
- Dependencies: specs/spec-a-core.md §4.2 (Oversampling flags), docs/architecture/pytorch_design.md §2.4 (Absorption pipeline), docs/development/testing_strategy.md §2 (Tier 1 tests), reports/2025-10-vectorization/phase_a/absorption_baseline.md (current performance snapshot), nanoBragg.c lines 3008-3098 (`parallax_subpixel` loops).
- Current gap snapshot (2025-11-17): `Simulator._apply_detector_absorption` (src/nanobrag_torch/simulator.py:1067-1084) always receives pixel-center coordinates; even with `oversample_thick=True` the parallax geometry is not recomputed per subpixel, so results equal the coarse path and violate AT-ABS-001 semantics.

## Phase A — Evidence & Specification Alignment
Goal: Prove the regression and capture the authoritative contract before making changes.
Prereqs: Editable install, C binary available, baseline artifacts from Phase A of vectorization plan.
Exit Criteria: Reproductions showing mismatch versus spec/C, documented hypothesis, and fix_plan attempt created.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Reproduce AT-ABS-001 with oversample_thick | [ ] | Run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_abs_001.py::TestAbsorption::test_subpixel_absorption -v` (CPU/CUDA when available) and log evidence under `reports/2025-11-oversample-thick/phase_a/pytest.log`. Note intensity deltas relative to expectation. |
| A2 | Collect C reference parity | [ ] | Execute nanoBragg with and without `-oversample_thick` on the matched configuration, store outputs under `reports/2025-11-oversample-thick/phase_a/c_reference/`. Confirm C shows measurable change while PyTorch does not. |
| A3 | Document spec/arch contract | [ ] | Summarise relevant clauses from `specs/spec-a-core.md` and `docs/architecture/pytorch_design.md` in `reports/2025-11-oversample-thick/phase_a/contract.md`, highlighting required per-subpixel geometry handling. |

## Phase B — Design Update
Goal: Decide how subpixel coordinates flow into absorption without breaking vectorization/device neutrality.
Prereqs: Phase A artifacts available, consensus on affected modules.
Exit Criteria: Written design covering tensor shapes, performance considerations, and test updates.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Map required tensor inputs | [ ] | Describe how `subpixel_coords_all` should be reshaped/broadcast for `_apply_detector_absorption` (store in `reports/.../phase_b/design_notes.md`). |
| B2 | Assess performance impact | [ ] | Use existing benchmarks to estimate cost of per-subpixel absorption; capture expected slowdowns and mitigation ideas. |
| B3 | Define test strategy | [ ] | Plan additional regression tests (e.g., new assertions for oversample_thick path) and note any guard conditions (CPU/CUDA). |

## Phase C — Implementation
Goal: Implement geometry-correct absorption while keeping vectorization and differentiability intact.
Prereqs: Design approved, branch ready.
Exit Criteria: Code updated with C-code references, tests written, artifacts captured.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Pass subpixel coordinates into absorption | [ ] | Update `Simulator.run` to supply per-subpixel geometry (or aggregated tensors) to `_apply_detector_absorption`. Preserve vectorized operations. |
| C2 | Extend `_apply_detector_absorption` | [ ] | Adjust the helper to consume batched subpixel inputs and compute capture fractions accordingly; reference nanoBragg.c lines 3060-3085 in docstring per Rule #11. |
| C3 | Add regression test | [ ] | Extend `tests/test_at_abs_001.py` (or create new test) verifying oversample_thick output differs from coarse path for oblique pixels and matches C within tolerance. |

## Phase D — Validation & Documentation
Goal: Demonstrate parity, update docs, and close ledger items.
Prereqs: Phase C merged or staged with passing tests.
Exit Criteria: Metrics archived, docs updated, fix_plan entry closed.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Run parity suite | [ ] | `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_abs_001.py -v` (CPU/CUDA) plus targeted C vs PyTorch comparison stored under `reports/.../phase_d/parity/`. |
| D2 | Update documentation | [ ] | Refresh `docs/architecture/pytorch_design.md` absorption section and `docs/development/testing_strategy.md` to note the corrected oversample_thick semantics. |
| D3 | Close plan | [ ] | Summarise outcomes in docs/fix_plan.md attempt history and mark this plan ready for archive. |
