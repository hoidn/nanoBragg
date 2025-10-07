## Context
- Initiative: PERF-PYTORCH-004 vectorization backlog; supports long-term goal "Parallel parity + performance" from docs/fix_plan.md.
- Phase Goal: Deliver a production-ready, fully vectorized tricubic interpolation pipeline (gather + polynomial evaluation) and follow with detector absorption vectorization without regressing physics, gradients, or device neutrality.
- Dependencies: specs/spec-a-core.md §4 (Structure factors), specs/spec-a-parallel.md §2.3 (Interpolation acceptance tests), docs/architecture/pytorch_design.md §§2.2–2.4, docs/architecture/c_code_overview.md (tricubic routines), docs/development/testing_strategy.md §§2–4, docs/development/pytorch_runtime_checklist.md, `nanoBragg.c` lines 2604–3278 (polin3/polin2/polint + detector absorption), `tests/test_at_str_002.py`, `tests/test_at_abs_001.py`, `reports/benchmarks/20250930-165726-compile-cache/` (current performance references). No dedicated tricubic/absorption microbenchmarks exist yet; Phase A will author reusable harnesses under `scripts/benchmarks/` so future loops can rerun baselines without ad-hoc snippets.
- Gap Snapshot (2025-11-21 refresh): Phase C1 (batched gather) and C2 (OOB fallback validation) are COMPLETE with artifacts under `reports/2025-10-vectorization/phase_c/`. Outstanding blocker before engaging Phase D polynomial work is C3 (shape assertions + device/device-aware caching) so the gather path cannot regress silently.
- Supervisory note (2025-11-21): Guard C3 deliverables with explicit evidence: update `phase_c/implementation_notes.md` with the new assertion/caching strategy, capture the targeted pytest log, and record the tensor-shape/caching checklist below before advancing to Phase D.

### Phase A — Evidence & Baseline Capture
Goal: Document the current (non-vectorized) behavior, warnings, and performance so we can prove the impact of the refactor.
Prereqs: Editable install (`pip install -e .`), C binary available for parity (when needed), environment variable `KMP_DUPLICATE_LIB_OK=TRUE`.
Exit Criteria: Baseline pytest log, timing snippet results, and notes stored under `reports/2025-10-vectorization/phase_a/` with references in docs/fix_plan.md Attempt history.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Re-run tricubic acceptance tests | [D] | ✅ Completed 2025-10-06 (`reports/2025-10-vectorization/phase_a/test_at_str_002.log`, `.collect.log`, `test_at_abs_001.log`, `env.json`). Re-run only if dependencies change or new warnings appear. |
| A2 | Measure current tricubic runtime | [D] | ✅ Completed 2025-10-07 (`scripts/benchmarks/tricubic_baseline.py` created; CPU & CUDA baselines captured in `phase_a/tricubic_baseline.md` and `phase_a/tricubic_baseline_results.json`). Key finding: scalar-only implementation @ ~1.4 ms/call (CPU), ~5.5 ms/call (CUDA). |
| A3 | Record detector absorption baseline | [D] | ✅ Completed 2025-10-07 (`scripts/benchmarks/absorption_baseline.py` created; CPU & CUDA baselines captured in `phase_a/absorption_baseline.md` and `phase_a/absorption_baseline_results.json`). GPU shows 5.4× speedup for 512² detector. |

### Phase B — Tricubic Vectorization Design
Goal: Lock the tensor-shape design, broadcasting plan, and gradient checks before code changes.
Prereqs: Phase A artifacts uploaded and referenced in docs/fix_plan.md.
Exit Criteria: Design memo (`reports/2025-10-vectorization/phase_b/design_notes.md`) describing target shapes, indexing strategy, gradient expectations, and failure modes; docs/fix_plan.md updated with summary and link.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Derive tensor shapes & broadcasting plan | [D] | ✅ Attempt #3 (2025-10-07) captured the `(B,4,4,4)` gather layout plus memory envelope; see `design_notes.md` §2 with diagrams + OOB masking guidance. |
| B2 | Map C polin3 semantics to PyTorch ops | [D] | ✅ Attempt #3 recorded Lagrange polynomial translation and reuse strategy (design_notes §3, referencing `nanoBragg.c` lines 4021-4058). |
| B3 | Gradient & dtype checklist | [D] | ✅ Attempt #3 consolidated differentiability/device rules (design_notes §4) aligning with `pytorch_runtime_checklist.md`; reuse table when authoring Phase E regression tests. |

### Phase C — Implementation: Neighborhood Gather
Goal: Replace scalar neighbor gathering with fully batched advanced indexing inside `Crystal._tricubic_interpolation` while keeping fallbacks for out-of-range queries.
Prereqs: Phase B design finalized; create feature branch per SOP if needed.
Exit Criteria: Vectorized gather merged, unit tests covering neighborhood assembly added, and plan task C1–C3 marked done with artifact references.
Implementation notes: capture all Phase C artifacts under `reports/2025-10-vectorization/phase_c/` (see table for filenames). Confirm every new test collects via `pytest --collect-only` before running the selector.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Implement batched neighborhood gather | [D] | ✅ Completed 2025-10-17 (Attempt #5). Batched gather infrastructure validated; all tests passing. Artifacts: `reports/2025-10-vectorization/phase_c/{gather_notes.md, collect_log.txt, test_*.log, diff_snapshot.json, runtime_probe.json}`. Scalar path (B=1) uses existing polin3; batched path (B>1) falls back to nearest-neighbor pending Phase D. |
| C2 | Preserve fallback semantics | [D] | ✅ Completed 2025-10-07 (Attempt #1). Authored `test_oob_warning_single_fire` capturing stdout to verify single-warning behavior; test asserts `_interpolation_warning_shown` flag state, `interpolate` disable, and `default_F` fallback on OOB queries. All tricubic tests pass (8/8). Artifacts: `reports/2025-10-vectorization/phase_c/{test_tricubic_vectorized.log, status_snapshot.txt}`; test code at `tests/test_tricubic_vectorized.py:199-314`. |
| C3 | Add shape assertions & cache hooks | [D] | ✅ Completed 2025-10-07 (Attempt #6). Shape assertions added for `(B, 4, 4, 4)` neighborhoods and output shapes; device consistency checks ensure tensors stay on input device. No explicit caching present in tricubic path. All targeted tests passing (5 gather + 1 acceptance). Artifacts: `reports/2025-10-vectorization/phase_c/{test_tricubic_vectorized.log, test_at_str_002_phi.log, implementation_notes.md}`. Code refs: `crystal.py:414-427` (shape/device assertions), `crystal.py:440-447` (scalar output assertions), `crystal.py:461-462` (batched fallback assertions). |

#### Phase C3 Verification Checklist
| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C3.1 | Assertion coverage | [D] | ✅ Completed. Added `assert sub_Fhkl.shape == (B, 4, 4, 4)`, `assert h_indices.shape == (B, 4)` (k,l similar), plus output assertions `F_cell.numel() == 1` (scalar) and `result.shape == original_shape` (both paths). Code refs: `crystal.py:414-420, 440-447, 461-462`. Documented in `implementation_notes.md` Phase C3 section. |
| C3.2 | Device-aware caching audit | [D] | ✅ Completed. No caching exists in `_tricubic_interpolation`. Added device checks: `assert sub_Fhkl.device == h.device`, `assert h_indices.device == h.device`. Verified device propagation: offsets use `device=self.device`, grids inherit from inputs, `.to(dtype=)` preserves device. Code ref: `crystal.py:422-427`. Audit documented in `implementation_notes.md` §2. |
| C3.3 | Targeted pytest evidence | [D] | ✅ Completed. Ran `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py -k "gather" -v` (5/5 passed) and `pytest tests/test_at_str_002.py::test_tricubic_interpolation_enabled -v` (1/1 passed). Logs stored: `reports/2025-10-vectorization/phase_c/test_tricubic_vectorized.log` and `test_at_str_002_phi.log`. Total 6/6 tests passed; CPU + CUDA paths validated. |

### Phase D — Implementation: Polynomial Evaluation
Goal: Vectorize `polint`, `polin2`, and `polin3` so they consume batches from Phase C without Python loops.
Prereqs: Phase C merged or staged with passing tests.
Exit Criteria: All polynomial helpers accept batched tensors, no Python loops over pixels remain, and helper-level unit tests exist.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Vectorize `polint` | [ ] | Rewrite using tensor broadcasting; support trailing batch dims and ensure numerical stability matches C (consider Kahan-style compensation if necessary). Add regression test in `tests/test_tricubic_vectorized.py::test_polint_vectorized_matches_scalar`. |
| D2 | Vectorize `polin2`/`polin3` | [ ] | Stack vectorized `polint` results instead of looping; maintain compatibility with scalar callers (if any). Capture proof-of-equivalence logs in `reports/2025-10-vectorization/phase_d/polynomial_validation.md`. |
| D3 | Audit differentiability | [ ] | Run `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_gradients.py::TestCrystal::test_tricubic_gradient -v` (add test if absent) to confirm gradients survive the refactor. |

### Phase E — Validation & Performance Assessment
Goal: Prove the new vectorized path matches legacy outputs, keeps gradients, and improves runtime on representative detector sizes.
Prereqs: Phases C/D complete; baseline artifacts from Phase A available for comparison.
Exit Criteria: Validation summary in `reports/2025-10-vectorization/phase_e/summary.md` including parity metrics, perf deltas, and gradient results; docs/fix_plan.md attempts updated.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| E1 | Regression tests sweep | [ ] | `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_str_002.py tests/test_tricubic_vectorized.py -v` (CPU + CUDA when available). Log outputs under `phase_e/pytest.log`. |
| E2 | Performance benchmark | [ ] | Reuse the Phase A harnesses (`tricubic_baseline.py`, `absorption_baseline.py`) in "baseline" vs "vectorized" modes; run CPU & CUDA sweeps with identical seeds and persist outputs to `phase_e/perf_results.json`. |
| E3 | Parity against C reference | [ ] | Use `nb-compare --resample --outdir reports/2025-10-vectorization/phase_e/nb_compare -- -default_F ...` (match AT-STR-002 config) to ensure intensities align within tolerance. Summarize metrics in `phase_e/summary.md`. |

### Phase F — Detector Absorption Vectorization
Goal: Apply the same vectorization discipline to `_apply_detector_absorption`, eliminating Python loops over `thicksteps` while preserving physics.
Prereqs: Phase E validated so tricubic changes are stable; absorption baseline from Phase A available.
Exit Criteria: Vectorized absorption path merged, tests updated, and performance improvements documented similar to tricubic work.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| F1 | Refresh design notes | [ ] | Append absorption section to `design_notes.md` describing tensor shapes (`(T,S,F)`), numerical stability considerations, and potential reuse of exponential precomputation. |
| F2 | Implement vectorized absorption | [ ] | Modify `_apply_detector_absorption` to broadcast layer indices and parallax tensors as described; maintain differentiability and device neutrality. Record implementation notes in `phase_f/implementation.md`. |
| F3 | Validate & benchmark | [ ] | `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_abs_001.py -v` plus microbenchmark update; capture results under `phase_f/summary.md` comparing against Phase A data. |

### Phase G — Documentation & Closure
Goal: Ensure documentation, plans, and fix_plan reflect the new vectorized behavior and that artifacts are archived.
Prereqs: Phases A–F complete.
Exit Criteria: Plan archived or marked complete, docs updated, and fix_plan entry closed.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| G1 | Update documentation | [ ] | Revise `docs/architecture/pytorch_design.md` (vectorization subsections) and `docs/development/pytorch_runtime_checklist.md` with the new expectations; note script locations in `docs/development/testing_strategy.md`. |
| G2 | Close planning artifacts | [ ] | Move key reports to `reports/archive/` (retain relative paths), update docs/fix_plan.md Attempts with final metrics, and archive this plan per SOP. |
