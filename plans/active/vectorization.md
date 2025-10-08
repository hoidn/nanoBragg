## Context
- Initiative: PERF-PYTORCH-004 vectorization backlog supporting docs/fix_plan.md entry [VECTOR-TRICUBIC-001].
- Phase Goal: Deliver a production-ready batched tricubic interpolation pipeline (gather + polynomial evaluation) and subsequently vectorize detector absorption without regressing parity, gradients, or device/dtype neutrality.
- Dependencies:
  - specs/spec-a-core.md §4 (structure-factor sampling contract)
  - specs/spec-a-parallel.md §2.3 (tricubic acceptance tests + tolerances)
  - docs/architecture/pytorch_design.md §§2.2–2.4 (vectorization strategy, broadcast shapes)
  - docs/development/testing_strategy.md §§1.4–2 (test cadence, authoritative commands)
  - docs/development/pytorch_runtime_checklist.md (device/vectorization guardrails)
  - `nanoBragg.c` lines 2604–3278 (polin3/polin2/polint) & 3375–3450 (detector absorption loop)
  - Existing artifacts under `reports/2025-10-vectorization/phase_*/`
- Status Snapshot (2025-11-27): Phases A–C complete with gather vectorization merged (commit 12742e5). Phase D1 worksheet captured under `reports/2025-10-vectorization/phase_d/polynomial_validation.md`; polynomial helpers remain scalar (D2–D4 pending) and detector absorption is still looped. Phase D is the active gate before parity/perf validation (Phase E) and absorption work (Phase F).
- Execution Notes: Store new evidence under `reports/2025-10-vectorization/phase_<letter>/` directories; every implementation task must quote the matching C snippet per CLAUDE Rule #11. Maintain CPU+CUDA parity and include `pytest --collect-only` proof before targeted runs.

### Phase A — Evidence & Baseline Capture
Goal: Record baseline behaviour/warnings/timings for tricubic interpolation and detector absorption prior to vectorization.
Prereqs: Editable install (`pip install -e .`), C binary available if parity comparisons are needed, `KMP_DUPLICATE_LIB_OK=TRUE` set.
Exit Criteria: Baseline pytest logs + benchmark metrics archived and referenced in fix_plan.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Re-run tricubic acceptance tests | [D] | ✅ Attempt #1 (2025-10-06). Artifacts: `reports/2025-10-vectorization/phase_a/test_at_str_002.log`, `.collect.log`, `test_at_abs_001.log`, `env.json`. |
| A2 | Measure current tricubic runtime | [D] | ✅ Attempt #2 (2025-10-07). Harness: `scripts/benchmarks/tricubic_baseline.py`; metrics in `phase_a/tricubic_baseline.md` & `tricubic_baseline_results.json`. |
| A3 | Record detector absorption baseline | [D] | ✅ Attempt #2 (2025-10-07). Harness: `scripts/benchmarks/absorption_baseline.py`; metrics in `phase_a/absorption_baseline.md` & `absorption_baseline_results.json`. |

### Phase B — Tricubic Vectorization Design
Goal: Finalise tensor-shape, broadcasting, and differentiability design ahead of implementation.
Prereqs: Phase A evidence captured and logged.
Exit Criteria: Completed design memo plus grad/device checklist; fix_plan updated with references.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Derive tensor shapes & broadcasting plan | [D] | ✅ Attempt #3 (2025-10-07). See `reports/2025-10-vectorization/phase_b/design_notes.md` §2. |
| B2 | Map C polin3 semantics to PyTorch ops | [D] | ✅ Attempt #3. Design notes §3 cites `nanoBragg.c:4021-4058`. |
| B3 | Gradient & dtype checklist | [D] | ✅ Attempt #3. Design notes §4 aligns with `pytorch_runtime_checklist.md`. |

### Phase C — Neighborhood Gather Implementation
Goal: Replace scalar neighbour gathering with vectorised indexing in `Crystal._tricubic_interpolation` while retaining OOB fallbacks and graph connectivity.
Prereqs: Phase B design complete; tests discoverable.
Exit Criteria: Batched gather merged, unit/regression tests passing on CPU+CUDA, plan/fix_plan updated with evidence.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Implement batched neighbourhood gather | [D] | ✅ Attempt #15 (2025-10-07). Implementation notes: `reports/2025-10-vectorization/phase_c/implementation_notes.md`; code in `src/nanobrag_torch/models/crystal.py` (commit 12742e5). |
| C2 | Add gather-specific test suite | [D] | ✅ Attempt #15. `tests/test_tricubic_vectorized.py` + logs (`phase_c/test_tricubic_vectorized.log`, `gather_notes.md`). Includes CPU+CUDA device cases. |
| C3 | Regression + gradient/device smoke | [D] | ✅ Attempt #16 (2025-10-08). Artifacts: `phase_c/gradient_smoke.log`, `runtime_probe.json`, `status_snapshot.txt`; targeted pytest selectors recorded. |

### Phase D — Polynomial Evaluation Vectorization (Active Gate)
Goal: Batch the 1D/2D/3D polynomial interpolation helpers (`polint`, `polin2`, `polin3`) so batched gathers avoid nearest-neighbour fallback.
Prereqs: Phase C output confirmed; `design_notes.md` §3 ready; create `reports/2025-10-vectorization/phase_d/` directory.
Exit Criteria: Vectorised polynomial helpers integrated, CPU+CUDA tests passing, documentation + metrics captured.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Draft polynomial validation worksheet | [D] | ✅ Attempt #8 (2025-10-07). Worksheet lives at `reports/2025-10-vectorization/phase_d/polynomial_validation.md` with tensor-shape specs, C references (`nanoBragg.c:4150-4187`), gradcheck plan, and tap-point notes. |
| D2 | Implement batched `polint`/`polin2`/`polin3` | [D] | ✅ Attempt #10 (2025-10-07) landed `polint_vectorized`/`polin2_vectorized`/`polin3_vectorized` in `src/nanobrag_torch/utils/physics.py` (commit f796861). CLAUDE Rule #11 docstrings cite `nanoBragg.c:4150-4187`; gradients/device/dtype neutrality validated in `reports/2025-10-vectorization/phase_d/pytest_cpu_pass.log` with supplementary notes in `polynomial_validation.md`. `_tricubic_interpolation` now calls the batched helper (no fallback warning). |
| D3 | Add polynomial regression tests | [D] | ✅ Attempt #9 (2025-10-07). Extended `tests/test_tricubic_vectorized.py` with `TestTricubicPoly` (11 tests: scalar equivalence, gradient flow, device/dtype parametrisation, batch shape preservation). All marked `xfail(strict=True)`. Artifacts: `phase_d/collect.log` (11 tests), `phase_d/pytest_cpu.log` (11 xfailed), `phase_d/implementation_notes.md`. |
| D4 | Execute targeted pytest sweep | [D] | ✅ Attempt #11 (2025-10-07). CPU: 11/11 passed (2.37s), CUDA: 11/11 passed (2.36s), AT-STR-002: 3/3 passed (2.13s). Artifacts: `phase_d/pytest_d4_{cpu,cuda,acceptance}.log`, `collect_d4.log`. Metrics appended to `polynomial_validation.md` with device metadata (CUDA 12.8, PyTorch 2.8.0+cu128). |

### Phase E — Integration, Parity, and Performance Validation
Goal: Confirm the full tricubic interpolation path stays vectorised, maintains parity, and improves performance per PERF-PYTORCH-004 objectives.
Prereqs: Phase D tasks D1–D4 complete; nearest-neighbour fallback eliminated for batched queries.
Exit Criteria: Parity metrics (tests + nb-compare/ROI) pass, microbenchmarks show expected speedup, documentation + fix_plan updated.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| E1 | Verify acceptance & regression tests | [ ] | Re-run `tests/test_at_str_002.py`, `tests/test_tricubic_vectorized.py`, and any affected gradient suites. Capture CPU/CUDA logs under `phase_e/pytest_cpu.log` & `phase_e/pytest_cuda.log`. Ensure `pytest --collect-only` evidence stored (`phase_e/collect.log`). |
| E2 | Run microbenchmarks post-vectorization | [ ] | Execute `scripts/benchmarks/tricubic_baseline.py` with `--outdir reports/2025-10-vectorization/phase_e/perf` (before/after metrics). Summarise deltas in `phase_e/perf_summary.md` and update `benchmark_results.json`. |
| E3 | Document parity/perf summary | [ ] | Produce `phase_e/summary.md` noting corr/Δ metrics vs scalar path, reference nb-compare outputs if used, and record gradient/device neutrality confirmation. Update docs/fix_plan attempt with metrics + artifact links. |

### Phase F — Detector Absorption Vectorization
Goal: Batch detector absorption loops over `detector_thicksteps` and oversample dimensions, reusing the tricubic vectorization patterns while keeping physics parity.
Prereqs: Phase E exit criteria satisfied; confirm current absorption baseline artifacts (Phase A3) on hand.
Exit Criteria: Vectorised absorption in production path, tests/benchmarks passing, documentation updated.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| F1 | Author absorption vectorization design | [ ] | Draft `phase_f/design_notes.md` (tensor layout, broadcasting, device/dtype considerations). Cite `nanoBragg.c:3375-3450` and detector spec docs. |
| F2 | Implement batched absorption | [ ] | Update `_apply_detector_absorption` (or equivalent) to operate on broadcast tensors (slow×fast×thicksteps). Add C reference docstrings and ensure differentiability. |
| F3 | Add regression + perf tests | [ ] | Extend `tests/test_at_abs_001.py` with device parametrisation; add targeted benchmarks via `scripts/benchmarks/absorption_baseline.py --outdir .../phase_f/perf`. Capture CPU/CUDA logs. |
| F4 | Summarise results + update fix_plan | [ ] | Document outcomes in `phase_f/summary.md`, note parity evidence (nb-compare if applicable), and update docs/fix_plan attempt history. |

### Phase G — Documentation & Handoff
Goal: Ensure all vectorization changes are documented, reproducible, and integrated with performance guidance.
Prereqs: Phases D–F exit criteria met.
Exit Criteria: Architecture/runtime docs updated; fix_plan closed; supervisor input ready for performance initiative follow-ups.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| G1 | Update docs & checklists | [ ] | Refresh `docs/development/pytorch_runtime_checklist.md` (if needed), `docs/architecture/pytorch_design.md`, and add lessons learned note. Record changes in docs/fix_plan. |
| G2 | Final attempt log & closure | [ ] | Log concluding Attempt in docs/fix_plan.md, summarise metrics, and mark [VECTOR-TRICUBIC-001] as done. Coordinate with PERF-PYTORCH-004 benchmarks for follow-up perf tasks. |
