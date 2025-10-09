## Context
- Initiative: PERF-PYTORCH-004 backlog entry [VECTOR-TRICUBIC-001] — eliminate residual Python loops in tricubic interpolation and detector absorption.
- Objective: Preserve the fully batched tricubic + absorption pipeline (Phases A–G) and drive the remaining CUDA parity/benchmark closure (Phase H) so the plan can be archived without reopening gaps.
- Dependencies:
  - specs/spec-a-core.md §4; specs/spec-a-parallel.md §2.3 — interpolation/absorption contract & acceptance tests
  - docs/architecture/pytorch_design.md §1.1, §2.2–2.4 — vectorization strategy & broadcast shapes
  - docs/development/testing_strategy.md §§1.4–2 — device/dtype discipline & authoritative commands
  - docs/development/pytorch_runtime_checklist.md — runtime guardrails for PyTorch edits
  - docs/fix_plan.md §[VECTOR-TRICUBIC-001] — ledger history + open blockers (CUDA evidence)
  - reports/2025-10-vectorization/phase_* — evidence bundles for Phases A–G
- Status Snapshot (2025-12-23 update): Phases A–H complete. PERF-PYTORCH-004 Attempt #36 cleared the device-placement blocker, Attempt #18 captured the CUDA parity + benchmarks under `reports/2025-10-vectorization/phase_h/20251009T092228Z/`, and galph loop i=228 archived the plan after updating docs/fix_plan.md.

### Phase A — Baseline Evidence Capture
Goal: Establish pre-vectorization behaviour, warnings, and timings for tricubic interpolation and detector absorption.
Prereqs: Editable install (`pip install -e .`), `KMP_DUPLICATE_LIB_OK=TRUE`, C binary discoverable for acceptance tests.
Exit Criteria: Baseline pytest logs + benchmark metrics stored under `reports/2025-10-vectorization/phase_a/` and referenced in docs/fix_plan.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Re-run tricubic acceptance tests | [D] | `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_str_002.py -v`; log: `reports/2025-10-vectorization/phase_a/test_at_str_002.log`; Attempt #1. |
| A2 | Measure tricubic runtime baseline | [D] | `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/tricubic_baseline.py --sizes 256 512 --repeats 200 --device cpu/cuda`; metrics under `phase_a/tricubic_baseline*.{md,json}`; Attempt #2. |
| A3 | Record detector absorption baseline | [D] | Same harness as A2 via `scripts/benchmarks/absorption_baseline.py`; artifacts `phase_a/absorption_baseline*.{md,json}`; Attempt #2. |

### Phase B — Tricubic Vectorization Design
Goal: Finalise tensor shapes, CLAUDE Rule #11 citations, and gradient/device checklist before implementation.
Prereqs: Phase A evidence confirmed in fix_plan.
Exit Criteria: Design memo completed with broadcast plan, C-code mapping, and gradient/device checklist.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Derive tensor shapes & broadcast flow | [D] | `reports/2025-10-vectorization/phase_b/design_notes.md` §2 documents `(B,4,4,4)` contract; Attempt #3. |
| B2 | Map C polin* semantics to PyTorch ops | [D] | Same memo §3 quoting `nanoBragg.c:4021-4058`; ensures Rule #11 compliance; Attempt #3. |
| B3 | Record gradient/device guardrails | [D] | Memo §4 aligns with `docs/development/pytorch_runtime_checklist.md`; Attempt #3. |

### Phase C — Neighborhood Gather Implementation
Goal: Batch the 64-neighbour gather while keeping OOB fallback semantics and device/dtype neutrality.
Prereqs: Phase B memo approved; gather tests discoverable.
Exit Criteria: Gather code merged, regression/tests captured on CPU+CUDA, fix_plan updated.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Implement batched neighbourhood gather | [D] | `src/nanobrag_torch/models/crystal.py` commit 12742e5; notes at `phase_c/implementation_notes.md`; Attempt #4/#15. |
| C2 | Author OOB warning regression | [D] | `tests/test_tricubic_vectorized.py::test_oob_warning_single_fire`; log `phase_c/test_tricubic_vectorized.log`; Attempt #6. |
| C3 | Add shape/device assertions + cache audit | [D] | Assertions recorded in `phase_c/implementation_notes.md`; pytest logs `phase_c/test_tricubic_vectorized.log`; Attempt #7. |

### Phase D — Polynomial Evaluation Vectorization
Goal: Replace scalar `polint`/`polin2`/`polin3` with fully batched helpers and validate parity.
Prereqs: Phase C outputs validated; design worksheet ready (`phase_d/polynomial_validation.md`).
Exit Criteria: Vectorized helpers integrated with CPU+CUDA tests, acceptance suite green, documentation captured.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Finalise polynomial validation worksheet | [D] | `phase_d/polynomial_validation.md` sections 1–15; Attempt #10. |
| D2 | Implement batched polint/polin2/polin3 | [D] | `src/nanobrag_torch/utils/physics.py` Rule #11 docstrings; implementation notes `phase_d/implementation_notes.md`; Attempt #11. |
| D3 | Run targeted polynomial suite (CPU) | [D] | `pytest tests/test_tricubic_vectorized.py::TestTricubicPoly -v`; log `phase_d/pytest_cpu_pass.log`; Attempt #11. |
| D4 | Execute CPU+CUDA sweeps + AT-STR-002 | [D] | Logs `phase_d/pytest_d4_{cpu,cuda,acceptance}.log`; gradcheck verified; Attempt #12. |

### Phase E — Integration, Parity, and Performance Validation
Goal: Confirm the full vectorized tricubic pipeline passes regression/performance gates on CPU & CUDA.
Prereqs: Phases C/D complete with tests passing.
Exit Criteria: Regression tests, performance benchmarks, and parity documentation archived.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| E1 | Run vectorized regression & acceptance suites | [D] | `pytest tests/test_tricubic_vectorized.py -v` (CPU/CUDA) + `pytest tests/test_at_str_002.py -v`; logs under `phase_e/pytest_{cpu,cuda}.log`; summary §2; Attempt #13. |
| E2 | Capture performance microbenchmarks | [D] | `scripts/benchmarks/tricubic_baseline.py --device cpu/cuda --repeats 200`; results `phase_e/perf/20251009T034421Z/`; Attempt #13. |
| E3 | Document parity & runtime checklist | [D] | `phase_e/summary.md` consolidates metrics & compliance; Attempt #13. |

### Phase F — Detector Absorption Vectorization Validation
Goal: Validate and document the already vectorized detector absorption path, extending tests/benchmarks.
Prereqs: Phase E complete; absorption baseline captured.
Exit Criteria: CPU validation, performance metrics, and documentation; CUDA rerun deferred to Phase H.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| F1 | Draft absorption design & tensor layout | [D] | `phase_f/design_notes.md` summarises `(thicksteps,S,F)` broadcast; Attempt #14. |
| F2 | Extend tests + add C reference | [D] | `tests/test_at_abs_001.py` parametrised CPU/CUDA; docstring cites `nanoBragg.c:2975-2983`; validation bundle `phase_f/validation/20251222T000000Z/summary.md`; Attempt #15. |
| F3 | Benchmark CPU absorption path | [D] | `scripts/benchmarks/absorption_baseline.py --device cpu --repeats 200`; metrics `phase_f/perf/20251009T050859Z/`; Attempt #16. |
| F4 | Consolidate Phase F summary | [D] | `phase_f/summary.md` captures CPU results + CUDA blocker delegation; Attempt #16. |

### Phase G — Documentation & Ledger Closure
Goal: Update permanent docs and ledgers to reflect vectorization work and delegate CUDA follow-up.
Prereqs: Phases A–F artifacts verified.
Exit Criteria: Architecture/runtime docs updated, pytest collect-only proof recorded, fix_plan/input alignment complete.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| G1 | Update architecture & runtime docs | [D] | `docs/architecture/pytorch_design.md` §1.1 + `docs/development/pytorch_runtime_checklist.md` vectorization bullet; bundle `phase_g/20251009T055116Z/summary.md`; Attempt #17. |
| G2 | Refresh plan snapshot & fix_plan ledger | [D] | Plan + fix_plan adjustments logged during galph loop i=214; evidence in `phase_g/20251009T055116Z/commands.txt`; Attempt #17 follow-up. |

### Phase H — CUDA Follow-Up & Plan Archival
Goal: Execute GPU validation now that device placement is fixed, then archive the plan.
Prereqs: ✅ Satisfied — PERF-PYTORCH-004 Attempt #36 (commit 34f319f) moved Detector tensors onto the simulator device; source weighting parity completed in Attempt #6.
Exit Criteria: CUDA tests/benchmarks captured, fix_plan updated with Attempt #18, plan moved to archive.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| H1 | Clear device-placement blocker | [D] | ✅ Completed via PERF-PYTORCH-004 Attempt #36 (commit 34f319f). `Simulator.__init__` now calls `detector.to(device=self.device, dtype=self.dtype)`, eliminating CUDA device mismatch. Logged in `docs/fix_plan.md` Attempt #36. |
| H2 | Rerun CUDA tests & benchmarks | [D] | ✅ Completed by Ralph (Attempt #18). Artifacts: `reports/2025-10-vectorization/phase_h/20251009T092228Z/` (CUDA pytest logs, benchmarks, env metadata). Results within ±1.3% of Phase E tricubic baselines; absorption +5–6 % vs Phase A. |
| H3 | Close ledger & archive plan | [D] | ✅ Completed by galph loop i=228 — fix_plan status flipped to `done`, plan migrated to `plans/archive/vectorization.md`, closure note recorded here. |
