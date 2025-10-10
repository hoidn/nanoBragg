## Context
- Initiative: DTYPE-NEUTRAL-001 — enforce dtype neutrality across detector geometry and caching so float64 test paths (e.g., determinism suite) run without dtype mismatches.
- Phase Goal: Produce a phased remediation blueprint (evidence → root-cause audit → fix implementation → validation) that eliminates float32/float64 clashes in `Detector` and dependent geometry caches, restoring determinism test execution.
- Dependencies:
  - `docs/development/testing_strategy.md` §1.4 (Device & Dtype Discipline) — authoritative guardrail for test commands and smoke expectations.
  - `docs/development/pytorch_runtime_checklist.md` §2 — runtime checklist for device/dtype neutrality.
  - `docs/architecture/detector.md` §§7–8 — detector caching and geometry invariants (includes `torch.allclose` cache checks).
  - `arch.md` §§2, 7.2 — detector layout and cached basis vector policy; confirms dtype-neutral expectations for geometry tensors.
  - `plans/active/determinism.md` — determinism plan currently blocked until dtype issues resolved; keep dependency noted in fix_plan.
  - `reports/2026-01-test-suite-triage/phase_d/20251010T171010Z/determinism/phase_a/summary.md` — Attempt #1 evidence showing RuntimeError from float32 vs float64 `torch.allclose` in `Detector.get_pixel_coords`.

### Phase A — Failure Reproduction & Evidence Capture
Goal: Reproduce dtype mismatch failures with authoritative pytest selectors and capture precise stack traces plus environment metadata for regression tracking.
Prereqs: Editable install, clean workspace, ensure `KMP_DUPLICATE_LIB_OK=TRUE` set.
Exit Criteria: Repro logs + stack traces archived under `reports/2026-01-test-suite-triage/phase_d/<STAMP>/dtype-neutral/phase_a/`, with `summary.md` detailing failure signatures and confirming float32 cache tensors vs float64 inputs.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Snapshot environment + seed baselines | [ ] | Run `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q`; capture Python/torch/cuda versions and current default dtype in `env.json`. Reference testing_strategy.md §1.4. |
| A2 | Reproduce AT-PARALLEL-013 dtype failure | [ ] | Command: `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py::TestAT_PARALLEL_013_Determinism::test_pytorch_determinism_same_seed`. Store `pytest.log` + full traceback showing `detector.py:767` dtype mismatch. |
| A3 | Reproduce AT-PARALLEL-024 dtype failure | [ ] | Command: `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_024.py::TestAT_PARALLEL_024_MissetDeterminism::test_pytorch_determinism`. Confirm identical RuntimeError, record in `pytest.log`. |
| A4 | Minimal unit reproducibility | [ ] | Craft short script or targeted pytest node (e.g., `tests/test_detector_geometry.py::TestDetectorPixelCache::test_dtype_switch_invalidation`) that switches Detector to float64 and triggers cache reuse; log stack trace + note current absence/addition of such test. |
| A5 | Summarise findings | [ ] | Author `summary.md` citing exact error message, tensors/dtypes involved, and link to prior Attempt #1 artifacts for continuity. |

### Phase B — Root-Cause Analysis & Scope Definition
Goal: Map all detector-related dtype touchpoints (caches, geometry tensors, helper factories) and document precise fix scope without editing production code.
Prereqs: Phase A artifacts collected.
Exit Criteria: `analysis.md` + checklist identifying every location where cached tensors or constants may hold float32 values that survive dtype switches; include code references with line numbers.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Static audit of detector caches | [ ] | Inspect `Detector.get_pixel_coords`, `_compute_planar_pixel_coords`, and cache initialization. Document how `_cached_basis_vectors` and `_cached_pix0_vector` are stored and reused. Highlight lack of dtype coercion in comparisons. |
| B2 | Inventory tensor factories | [ ] | Trace creation of detector basis vectors (`setup_basis_vectors`, `_apply_rotations`), pixel grids (`torch.arange`, `meshgrid`), and constants (`beam_direction`, `min_ratio`). Note each factory ensuring device/dtype alignment. |
| B3 | Cross-component survey | [ ] | Review `Crystal`, `Beam`, and simulator caches for similar dtype coupling (use grep for `torch.allclose` and `_cached_*`). Record any additional hotspots that could share fix infrastructure. |
| B4 | Draft tap list | [ ] | Propose instrumentation taps (if needed) to confirm dtype transitions after fix (e.g., log dtype of cached tensors pre/post `to()`). Store under `tap_points.md`. |
| B5 | Update fix_plan attempt log | [ ] | Append Attempt entry for `[DTYPE-NEUTRAL-001]` in `docs/fix_plan.md` summarizing findings and artifact path `reports/.../phase_b/<STAMP>/summary.md`. |

### Phase C — Remediation Blueprint
Goal: Design the implementation approach and acceptance coverage without changing code; ensure determinism plan can depend on this fix.
Prereqs: Phase B analysis complete.
Exit Criteria: `remediation_plan.md` detailing code changes, tests, and documentation updates; `tests.md` enumerating required pytest selectors (existing + new) covering dtype neutrality; `docs_updates.md` listing docs to refresh.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Author remediation plan | [ ] | Outline modifications: (1) coercing cached tensors to `self.dtype` before comparison, (2) storing cache metadata (device/dtype) to trigger invalidation, (3) ensuring `_pixel_coords_cache` respects requested dtype, (4) downstream updates (crystal caches if applicable). Include code line references. |
| C2 | Define regression coverage | [ ] | Specify targeted tests: determinism selectors, detector geometry dtype toggles, any new unit test to assert cache reinitializes when dtype changes. Include CPU+CUDA expectations (if CUDA available). |
| C3 | Document doc/test touchpoints | [ ] | List updates needed for `docs/development/testing_strategy.md` (if new commands), `docs/architecture/detector.md` (cache dtype note), and runtime checklist. |
| C4 | Update dependency graph | [ ] | Note in `remediation_plan.md` how this fix unblocks `[DETERMINISM-001]` Phase A rerun; add gating note for supervisor input. |

### Phase D — Implementation Execution (Delegate to Ralph)
Goal: Provide ordered implementation tasks with clear acceptance criteria to eliminate dtype mismatch.
Prereqs: Phase C blueprint approved.
Exit Criteria: Checklist with discrete implementation steps + review hooks; ready for engineer execution.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Update detector cache handling | [ ] | Code change: ensure cached tensors are materialized with `self.dtype` when stored/retrieved; adjust `torch.allclose` guard to operate on dtype-consistent tensors. |
| D2 | Add regression test | [ ] | Introduce targeted pytest covering dtype swap (e.g., create Detector float32, call `get_pixel_coords`, then switch to float64 and ensure recomputation without crash). |
| D3 | Run determinism selectors | [ ] | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py::TestAT_PARALLEL_013_Determinism::test_pytorch_determinism_same_seed tests/test_at_parallel_024.py::TestAT_PARALLEL_024_MissetDeterminism::test_pytorch_determinism`. Confirm dtype mismatch resolved (tests may still fail for seed reasons; capture new failure mode). |
| D4 | GPU smoke (if available) | [ ] | Execute `pytest -v -m gpu_smoke` or equivalent to ensure dtype conversions respect CUDA tensors. |

### Phase E — Validation & Documentation Closeout
Goal: Confirm dtype neutrality fix is stable and update documentation.
Prereqs: Implementation complete, targeted tests passing.
Exit Criteria: Validation report + docs updates committed; fix_plan updated with final attempt entry and dependency release for determinism plan.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| E1 | Compile validation report | [ ] | `reports/.../phase_e/<STAMP>/validation.md` summarizing test outcomes (CPU/CUDA), remaining determinism issues (if any), and performance impact assessment. |
| E2 | Update docs & checklists | [ ] | Apply doc changes enumerated in Phase C3; ensure runtime checklist explicitly references cache dtype handling. |
| E3 | Refresh fix_plan & galph memory | [ ] | Mark `[DTYPE-NEUTRAL-001]` status and attempts; note that `[DETERMINISM-001]` dependency cleared. |

### Metrics & Artifacts
- Artifact root: `reports/2026-01-test-suite-triage/phase_d/<STAMP>/dtype-neutral/` (phase subfolders `phase_a` … `phase_e`).
- Capture commands in `commands.txt`; logs as `pytest.log`; stack traces in `trace/` when necessary.
- Metrics to record: dtype of cached tensors before/after fix, runtime of determinism tests pre/post fix, CPU vs CUDA parity outcomes.

### Risks & Mitigations
- **False negatives:** Determinism tests may still fail for seed issues; ensure logs distinguish dtype fix success from remaining failures.
- **Cache invalidation regressions:** Introducing dtype-aware invalidation might trigger recomputation overhead; include benchmarks if runtime spikes >5%.
- **Protected assets:** Confirm no refactors rename assets listed in `docs/index.md` (e.g., `loop.sh`).

### References
- `tests/test_at_parallel_013.py`
- `tests/test_at_parallel_024.py`
- `tests/test_detector_geometry.py`
- `src/nanobrag_torch/models/detector.py`
- `docs/development/testing_strategy.md`
- `docs/development/pytorch_runtime_checklist.md`
- `docs/architecture/detector.md`
- `reports/2026-01-test-suite-triage/phase_d/20251010T171010Z/determinism/phase_a/*`
