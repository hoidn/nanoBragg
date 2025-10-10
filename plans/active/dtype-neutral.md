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

### Status Snapshot (2026-01-10)
- Phase A ✅ complete — Attempt #1 (`reports/2026-01-test-suite-triage/phase_d/20251010T172810Z/dtype-neutral/phase_a/`) captured collect-only env snapshot, determinism failure logs, and minimal reproducer narrowing scope to `Detector.to()` cache handling.
- Phase B ✅ complete — Attempt #2 (`reports/2026-01-test-suite-triage/phase_d/20251010T173558Z/dtype-neutral/phase_b/`) produced static audit artifacts (`analysis.md`, `tap_points.md`, `summary.md`) and isolated missing `dtype=self.dtype` coercion in cache `.to()` calls.

### Phase A — Failure Reproduction & Evidence Capture
Goal: Reproduce dtype mismatch failures with authoritative pytest selectors and capture precise stack traces plus environment metadata for regression tracking.
Prereqs: Editable install, clean workspace, ensure `KMP_DUPLICATE_LIB_OK=TRUE` set.
Exit Criteria: Repro logs + stack traces archived under `reports/2026-01-test-suite-triage/phase_d/<STAMP>/dtype-neutral/phase_a/`, with `summary.md` detailing failure signatures and confirming float32 cache tensors vs float64 inputs.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Snapshot environment + seed baselines | [D] | Attempt #1 (20251010T172810Z) — `env.json` + `collect_only.log` captured via `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q`; documents Python 3.13.5, torch 2.7.1+cu126, CUDA availability. References testing_strategy.md §1.4. |
| A2 | Reproduce AT-PARALLEL-013 dtype failure | [D] | Attempt #1 — `pytest -v tests/test_at_parallel_013.py --maxfail=0 --durations=10` archived under `reports/2026-01-test-suite-triage/phase_d/20251010T172810Z/dtype-neutral/phase_a/at_parallel_013/pytest.log`; shows `detector.py:767` float32 vs float64 mismatch plus Dynamo failure note. |
| A3 | Reproduce AT-PARALLEL-024 dtype failure | [D] | Attempt #1 — `pytest -v tests/test_at_parallel_024.py --maxfail=0 --durations=10` stored in `reports/2026-01-test-suite-triage/phase_d/20251010T172810Z/dtype-neutral/phase_a/at_parallel_024/pytest.log`; captures identical cache mismatch and mosaic rotation dtype drift. |
| A4 | Minimal unit reproducibility | [D] | Attempt #1 — inline script (see `reports/2026-01-test-suite-triage/phase_d/20251010T172810Z/dtype-neutral/phase_a/minimal_repro.log`) toggles detector from float64 → float32 via `Detector.to()` and reproduces `RuntimeError: Float did not match Double`, isolating cache cloning bug. |
| A5 | Summarise findings | [D] | Attempt #1 — `summary.md` (`reports/2026-01-test-suite-triage/phase_d/20251010T172810Z/dtype-neutral/phase_a/summary.md`) synthesises logs, minimal repro, and ties back to prior determinism Attempt #1 evidence for continuity. |

### Phase B — Root-Cause Analysis & Scope Definition
Goal: Map all detector-related dtype touchpoints (caches, geometry tensors, helper factories) and document precise fix scope without editing production code.
Prereqs: Phase A artifacts collected.
Exit Criteria: `analysis.md` + checklist identifying every location where cached tensors or constants may hold float32 values that survive dtype switches; include code references with line numbers.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Static audit of detector caches | [D] | Attempt #2 (20251010T173558Z) — `analysis.md` §1 details `_cached_basis_vectors` / `_cached_pix0_vector` lifecycle and missing `dtype=self.dtype` coercion before `torch.allclose`. |
| B2 | Inventory tensor factories | [D] | Attempt #2 — `analysis.md` §2 inventories detector tensor factories; confirms they already honour caller device/dtype. |
| B3 | Cross-component survey | [D] | Attempt #2 — `all_cached_vars.txt` + summary.md §Scope confirm Detector is the sole dtype-unsafe cache; Simulator/Crystal/Beam unaffected. |
| B4 | Draft tap list | [D] | Attempt #2 — `tap_points.md` captures optional asserts/logging to verify cache dtype parity post-fix (for use only if regressions persist). |
| B5 | Update fix_plan attempt log | [D] | Attempt #2 — `[DTYPE-NEUTRAL-001]` entry in `docs/fix_plan.md` now records artifact path and findings; see Attempt #2 bullet. |

### Phase C — Remediation Blueprint
Goal: Lock down the minimal fix (cache `.to(..., dtype=self.dtype)`) and its validation/doc updates so implementation can proceed without ambiguity.
Prereqs: Phase B analysis reviewed and supervisor sign-off (this loop).
Exit Criteria: Blueprint bundle under `reports/2026-01-test-suite-triage/phase_d/<STAMP>/dtype-neutral/phase_c/` containing `remediation_plan.md`, `tests.md`, `docs_updates.md`, plus fix_plan Attempt #3 entry summarising readiness.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Author remediation_plan.md | [ ] | Document the 4-line diff (add `dtype=self.dtype` to cache retrieval in `detector.py:762-777`), include risk assessment, owner (Ralph), and rollback guidance. Reference Phase B summary for evidence. |
| C2 | Draft tests.md | [ ] | Enumerate authoritative commands: `pytest -v tests/test_at_parallel_013.py tests/test_at_parallel_024.py --maxfail=0` and detector smoke (e.g., `tests/test_detector_geometry.py`). Note expected outcome: RuntimeError removed though seeds may still fail. |
| C3 | Draft docs_updates.md | [ ] | Capture edits to `docs/architecture/detector.md` (cache dtype note) and `docs/development/pytorch_runtime_checklist.md` (§2 example). Include link to testing strategy references. |
| C4 | Log Attempt #3 in fix_plan | [ ] | Update `[DTYPE-NEUTRAL-001]` with Phase C artifact path, blueprint highlights, and readiness message unlocking Phase D delegation. |

### Phase D — Implementation Execution (Delegate to Ralph)
Goal: Provide ordered implementation tasks with clear acceptance criteria to eliminate dtype mismatch.
Prereqs: Phase C blueprint approved.
Exit Criteria: Checklist with discrete implementation steps + review hooks; ready for engineer execution.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Update detector cache handling | [ ] | Code change: ensure cached tensors are materialized with `self.dtype` when stored/retrieved; adjust `torch.allclose` guard to operate on dtype-consistent tensors. |
| D2 | Add regression test | [ ] | Introduce targeted pytest covering dtype swap (e.g., create Detector float32, call `get_pixel_coords`, then switch to float64 and ensure recomputation without crash). |
| D3 | Run determinism selectors | [ ] | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py tests/test_at_parallel_024.py --maxfail=0 --durations=10`. Confirm dtype mismatch resolved (tests may still fail for seed reasons; capture new failure mode). |
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
