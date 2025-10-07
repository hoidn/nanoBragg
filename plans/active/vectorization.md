## Context
- Initiative: PERF-PYTORCH-004 vectorization backlog; supports long-term goal "Parallel parity + performance" from docs/fix_plan.md
- Phase Goal: Deliver a production-ready, fully vectorized tricubic interpolation pipeline (gather + polynomial evaluation) and follow with detector absorption vectorization without regressing physics, gradients, or device neutrality.
- Dependencies: specs/spec-a-core.md §4 (Structure factors), specs/spec-a-parallel.md §2.3 (Interpolation acceptance tests), docs/architecture/pytorch_design.md §§2.2–2.4, docs/architecture/c_code_overview.md (tricubic routines), docs/development/testing_strategy.md §§2–4, docs/development/pytorch_runtime_checklist.md, `nanoBragg.c` lines 2604–3278 (polin3/polin2/polint + detector absorption), `tests/test_at_str_002.py`, `tests/test_at_abs_001.py`, `reports/benchmarks/20250930-165726-compile-cache/` (current performance references). No dedicated tricubic/absorption microbenchmarks exist yet; Phase A will author reusable harnesses under `scripts/benchmarks/` so future loops can rerun baselines without ad-hoc snippets.
- Gap Snapshot (2025-11-09): Phase A remains untouched; no artifacts exist under `reports/2025-10-vectorization/phase_a/`, so Ralph must prioritise A1–A3 baseline capture before any implementation edits. docs/fix_plan.md item VECTOR-TRICUBIC-001 lists these as the gating next actions.

### Phase A — Evidence & Baseline Capture
Goal: Document the current (non-vectorized) behavior, warnings, and performance so we can prove the impact of the refactor.
Prereqs: Editable install (`pip install -e .`), C binary available for parity (when needed), environment variable `KMP_DUPLICATE_LIB_OK=TRUE`.
Exit Criteria: Baseline pytest log, timing snippet results, and notes stored under `reports/2025-10-vectorization/phase_a/` with references in docs/fix_plan.md Attempt history.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Re-run tricubic acceptance tests | [ ] | `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_str_002.py -v` ⇒ save log to `reports/2025-10-vectorization/phase_a/test_at_str_002.log`; confirm nearest-neighbour fallback warning message appears for batched inputs. |
| A2 | Measure current tricubic runtime | [ ] | Author `scripts/benchmarks/tricubic_baseline.py` (device/dtype neutral, honours `KMP_DUPLICATE_LIB_OK=TRUE`) and run `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/tricubic_baseline.py --sizes 256 512 --repeats 5`. Capture CPU timings (and CUDA when available) in `phase_a/tricubic_baseline.md` plus raw JSON/CSV under `phase_a/tricubic_baseline_results.json`. |
| A3 | Record detector absorption baseline | [ ] | Create `scripts/benchmarks/absorption_baseline.py` mirroring A2's interface; execute `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/absorption_baseline.py --sizes 256 512 --repeats 5` alongside `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_abs_001.py -v`. Store logs in `phase_a/absorption_baseline.md` and metrics in `phase_a/absorption_baseline_results.json`. |

### Phase B — Tricubic Vectorization Design
Goal: Lock the tensor-shape design, broadcasting plan, and gradient checks before code changes.
Prereqs: Phase A artifacts uploaded and referenced in docs/fix_plan.md.
Exit Criteria: Design memo (`reports/2025-10-vectorization/phase_b/design_notes.md`) describing target shapes, indexing strategy, gradient expectations, and failure modes; docs/fix_plan.md updated with summary and link.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Derive tensor shapes & broadcasting plan | [ ] | Document how `(S,F)` Miller grids expand to `(S,F,4,4,4)` neighborhoods; include diagrams referencing c_code_overview.md appendix; note device/dtype handling requirements. |
| B2 | Map C polin3 semantics to PyTorch ops | [ ] | Translate nanoBragg.c polynomial evaluation to tensor algebra; identify reuse opportunities (e.g., precomputed vandermonde weights). Capture equations + references in design memo. |
| B3 | Gradient & dtype checklist | [ ] | Cross-check docs/development/pytorch_runtime_checklist.md so the forthcoming implementation keeps gradients (no `.item()`, no `torch.linspace`) and works on CPU/CUDA; list explicit assertions/tests to add in Phase E. |

### Phase C — Implementation: Neighborhood Gather
Goal: Replace scalar neighbor gathering with fully batched advanced indexing inside `Crystal._tricubic_interpolation` while keeping fallbacks for out-of-range queries.
Prereqs: Phase B design finalized; create feature branch per SOP if needed.
Exit Criteria: Vectorized gather merged, unit tests covering neighborhood assembly added, and plan task C1–C3 marked done with artifact references.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Implement batched neighborhood gather | [ ] | Replace Python loops with broadcasting + advanced indexing to build `(S,F,4,4,4)` `sub_Fhkl` tensor; ensure compatibility with arbitrary batch dims (e.g., oversample, mosaic). |
| C2 | Preserve fallback semantics | [ ] | Maintain existing out-of-bounds detection and warning (single emission); verify fallback path still works by forcing OOB indices in a targeted unit test saved under `tests/test_tricubic_vectorized.py`. |
| C3 | Add shape assertions & cache hooks | [ ] | Introduce lightweight assertions to catch unexpected shapes; ensure any caching stays device-aware to avoid CPU allocations when running on CUDA. Document in `reports/2025-10-vectorization/phase_c/implementation_notes.md`. |

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
