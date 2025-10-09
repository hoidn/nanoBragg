## Context
- Initiative: PERF-PYTORCH-004 vectorization backlog supporting docs/fix_plan.md entry [VECTOR-TRICUBIC-001].
- Phase Goal: Deliver a production-ready batched tricubic interpolation pipeline (gather + polynomial evaluation) and subsequently vectorize detector absorption without regressing parity, gradients, or device/dtype neutrality.
- Dependencies:
  - specs/spec-a-core.md §4 (structure-factor sampling contract)
  - specs/spec-a-parallel.md §2.3 (tricubic acceptance tests + tolerances)
  - docs/architecture/pytorch_design.md §§2.2-2.4 (vectorization strategy, broadcast shapes)
  - docs/development/testing_strategy.md §§1.4-2 (test cadence, authoritative commands)
  - docs/development/pytorch_runtime_checklist.md (device/vectorization guardrails)
  - `nanoBragg.c` lines 2604-3278 (polin3/polin2/polint) & 3375-3450 (detector absorption loop)
  - Existing artifacts under `reports/2025-10-vectorization/phase_*/`
- Status Snapshot (2025-12-22): Phases A–F4 complete — tricubic gather/polynomial vectorization (commits 12742e5, f796861) validated in `reports/2025-10-vectorization/phase_e/summary.md`; detector absorption verification + CPU perf logged in `reports/2025-10-vectorization/phase_f/summary.md`. CUDA perf/absorption tests remain blocked by the device-placement defect (docs/fix_plan Attempt #14) and are tracked under PERF-PYTORCH-004. Outstanding work: Phase G documentation + ledger closure to retire [VECTOR-TRICUBIC-001].
- Execution Notes: Store new evidence under `reports/2025-10-vectorization/phase_<letter>/` directories; every implementation task must quote the matching C snippet per CLAUDE Rule #11. Maintain CPU+CUDA parity and include `pytest --collect-only` proof before targeted runs.

### Phase A - Evidence & Baseline Capture
Goal: Record baseline behaviour/warnings/timings for tricubic interpolation and detector absorption prior to vectorization.
Prereqs: Editable install (`pip install -e .`), C binary available if parity comparisons are needed, `KMP_DUPLICATE_LIB_OK=TRUE` set.
Exit Criteria: Baseline pytest logs + benchmark metrics archived and referenced in fix_plan.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Re-run tricubic acceptance tests | [D] | ✅ Attempt #1 (2025-10-06). Artifacts: `reports/2025-10-vectorization/phase_a/test_at_str_002.log`, `.collect.log`, `test_at_abs_001.log`, `env.json`. |
| A2 | Measure current tricubic runtime | [D] | ✅ Attempt #2 (2025-10-07). Harness: `scripts/benchmarks/tricubic_baseline.py`; metrics in `phase_a/tricubic_baseline.md` & `tricubic_baseline_results.json`. |
| A3 | Record detector absorption baseline | [D] | ✅ Attempt #2 (2025-10-07). Harness: `scripts/benchmarks/absorption_baseline.py`; metrics in `phase_a/absorption_baseline.md` & `absorption_baseline_results.json`. |

### Phase B - Tricubic Vectorization Design
Goal: Finalise tensor-shape, broadcasting, and differentiability design ahead of implementation.
Prereqs: Phase A evidence captured and logged.
Exit Criteria: Completed design memo plus grad/device checklist; fix_plan updated with references.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Derive tensor shapes & broadcasting plan | [D] | ✅ Attempt #3 (2025-10-07). See `reports/2025-10-vectorization/phase_b/design_notes.md` §2. |
| B2 | Map C polin3 semantics to PyTorch ops | [D] | ✅ Attempt #3. Design notes §3 cites `nanoBragg.c:4021-4058`. |
| B3 | Gradient & dtype checklist | [D] | ✅ Attempt #3. Design notes §4 aligns with `pytorch_runtime_checklist.md`. |

### Phase C - Neighborhood Gather Implementation
Goal: Replace scalar neighbour gathering with vectorised indexing in `Crystal._tricubic_interpolation` while retaining OOB fallbacks and graph connectivity.
Prereqs: Phase B design complete; tests discoverable.
Exit Criteria: Batched gather merged, unit/regression tests passing on CPU+CUDA, plan/fix_plan updated with evidence.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Implement batched neighbourhood gather | [D] | ✅ Attempt #15 (2025-10-07). Implementation notes: `reports/2025-10-vectorization/phase_c/implementation_notes.md`; code in `src/nanobrag_torch/models/crystal.py` (commit 12742e5). |
| C2 | Add gather-specific test suite | [D] | ✅ Attempt #15. `tests/test_tricubic_vectorized.py` + logs (`phase_c/test_tricubic_vectorized.log`, `gather_notes.md`). Includes CPU+CUDA device cases. |
| C3 | Regression + gradient/device smoke | [D] | ✅ Attempt #16 (2025-10-08). Artifacts: `phase_c/gradient_smoke.log`, `runtime_probe.json`, `status_snapshot.txt`; targeted pytest selectors recorded. |

### Phase D - Polynomial Evaluation Vectorization (Active Gate)
Goal: Batch the 1D/2D/3D polynomial interpolation helpers (`polint`, `polin2`, `polin3`) so batched gathers avoid nearest-neighbour fallback.
Prereqs: Phase C output confirmed; `design_notes.md` §3 ready; create `reports/2025-10-vectorization/phase_d/` directory.
Exit Criteria: Vectorised polynomial helpers integrated, CPU+CUDA tests passing, documentation + metrics captured.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Draft polynomial validation worksheet | [D] | ✅ Attempt #8 (2025-10-07). Worksheet lives at `reports/2025-10-vectorization/phase_d/polynomial_validation.md` with tensor-shape specs, C references (`nanoBragg.c:4150-4187`), gradcheck plan, and tap-point notes. |
| D2 | Implement batched `polint`/`polin2`/`polin3` | [D] | ✅ Attempt #10 (2025-10-07) landed `polint_vectorized`/`polin2_vectorized`/`polin3_vectorized` in `src/nanobrag_torch/utils/physics.py` (commit f796861). CLAUDE Rule #11 docstrings cite `nanoBragg.c:4150-4187`; gradients/device/dtype neutrality validated in `reports/2025-10-vectorization/phase_d/pytest_cpu_pass.log` with supplementary notes in `polynomial_validation.md`. `_tricubic_interpolation` now calls the batched helper (no fallback warning). |
| D3 | Add polynomial regression tests | [D] | ✅ Attempt #9 (2025-10-07). Extended `tests/test_tricubic_vectorized.py` with `TestTricubicPoly` (11 tests covering scalar equivalence, gradient flow, device/dtype parametrisation, batch-shape preservation). XFail markers removed after Phase D2 landing; live logs in `phase_d/pytest_cpu_pass.log`. Artifacts: `phase_d/collect.log`, `phase_d/pytest_cpu.log`, `phase_d/implementation_notes.md`. |
| D4 | Execute targeted pytest sweep | [D] | ✅ Attempt #11 (2025-10-07). CPU: 11/11 passed (2.37s), CUDA: 11/11 passed (2.36s), AT-STR-002: 3/3 passed (2.13s). Artifacts: `phase_d/pytest_d4_cpu.log`, `phase_d/pytest_d4_cuda.log`, `phase_d/pytest_d4_acceptance.log`, `collect_d4.log`. Metrics appended to `polynomial_validation.md` with device metadata (CUDA 12.8, PyTorch 2.8.0+cu128). |

### Phase E - Integration, Parity, and Performance Validation
Goal: Confirm the full tricubic interpolation path stays vectorised, maintains parity, and improves performance per PERF-PYTORCH-004 objectives.
Prereqs: Phase D tasks D1-D4 complete; nearest-neighbour fallback eliminated for batched queries.
Exit Criteria: Parity metrics (tests + nb-compare/ROI) pass, microbenchmarks show expected speedup, documentation + fix_plan updated.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| E1 | Verify acceptance & regression tests | [D] | ✅ Attempt #11 (2025-10-07). CPU & CUDA logs stored in `reports/2025-10-vectorization/phase_e/{pytest_cpu.log,pytest_cuda.log,collect.log,env.json,sha256.txt}`; 19/19 tests passed per device with gradcheck markers intact. |
| E2 | Run microbenchmarks post-vectorization | [D] | ✅ Attempt #12 (2025-10-08). Benchmarks captured under `reports/2025-10-vectorization/phase_e/perf/20251009T034421Z/` (cpu/cuda logs, `perf_results.json`, `perf_summary.md`); 200-repeat runs show <=1.2% delta vs Phase A baseline. |
| E3 | Document parity/perf summary | [D] | ✅ Attempt #12 (2025-10-08). `reports/2025-10-vectorization/phase_e/summary.md` consolidates E1-E3 results, notes runtime checklist compliance, and docs/fix_plan Attempt #12 threads Phase F tasks. |

### Phase F - Detector Absorption Vectorization
Goal: Batch detector absorption loops over `detector_thicksteps` and oversample dimensions, reusing the tricubic vectorization patterns while keeping physics parity.
Prereqs: Phase E exit criteria satisfied; confirm current absorption baseline artifacts (Phase A3) on hand.
Exit Criteria: Vectorised absorption in production path, tests/benchmarks passing, documentation updated.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| F1 | Author absorption vectorization design | [D] | ✅ Attempt #13 (2025-10-08). Design notes at `reports/2025-10-vectorization/phase_f/design_notes.md` (13 sections, 30.8KB); discovered current implementation already vectorized (lines 1764-1787); design doc still valuable for validation/test templates/performance baselines. Commands/env/checksums captured. |
| F2 | Implement batched absorption | [D] | ✅ Attempt #14 (2025-12-22). Validated existing vectorized path: added C-code reference, extended `tests/test_at_abs_001.py` parametrisation (device + `oversample_thick`), recorded CPU proof in `reports/2025-10-vectorization/phase_f/validation/20251222T000000Z/`. CUDA execution remains blocked by the global device-placement defect noted in `docs/fix_plan.md` Attempt #14. |
| F3 | Add regression + perf tests | [D] | ✅ Attempt #15 (2025-10-09). CPU benchmark (`scripts/benchmarks/absorption_baseline.py --sizes 256 512 --thicksteps 5 --repeats 200 --device cpu`) logged in `reports/2025-10-vectorization/phase_f/perf/20251009T050859Z/` with `perf_summary.md` + `perf_results.json`. Throughput matched Phase A baseline (13.80 Mpx/s @ 256², 18.89 Mpx/s @ 512²; 0% delta). CUDA perf remains blocked by the global device-placement defect noted in docs/fix_plan Attempt #14. |
| F4 | Summarise results + update fix_plan | [D] | ✅ Attempt #16 (2025-10-09). Summary: `reports/2025-10-vectorization/phase_f/summary.md` consolidates F2 validation (8/8 CPU tests, CUDA blocked) + F3 perf (0.0% delta vs baseline). Artifacts: `phase_f/commands.txt` (Phase F4 section), `pytest_collect_phase_f4.log` (689 tests). CUDA rerun commands documented; blocker tracked in fix_plan Attempt #14. |

### Phase G — Documentation & Handoff
Goal: Capture the vectorization lessons in the permanent docs, align the runtime checklist with the new batched flows, and close the fix-plan entry while leaving a clear hook for the CUDA follow-up.
Prereqs: Phase F summary in place (`reports/2025-10-vectorization/phase_f/summary.md`), plan Status Snapshot refreshed, and fix_plan Attempts #13-#16 reviewed.
Exit Criteria: Updated documentation committed with cited artifacts, doc-only verification recorded, final fix_plan Attempt logged, and CUDA rerun explicitly delegated to PERF-PYTORCH-004.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| G1a | Update `docs/architecture/pytorch_design.md` | [ ] | Add a concise subsection summarising the tricubic gather + batched polynomial path and the detector absorption vectorization, citing Phases C–F artifacts and nanoBragg.c references. Note the CUDA blocker and cross-link to PERF-PYTORCH-004. |
| G1b | Refresh `docs/development/pytorch_runtime_checklist.md` | [ ] | Expand the vectorization/device bullets to mention the tricubic + absorption evidence, required regression commands, and the expectation to rerun CUDA once the device-placement defect clears. |
| G1c | Audit `docs/development/testing_strategy.md` | [ ] | Confirm Tier-1/2 guidance reflects the new tests (e.g., `tests/test_tricubic_vectorized.py`, parametrised AT-ABS-001). Update the document or record “no update needed” in `reports/2025-10-vectorization/phase_g/<timestamp>/summary.md`. |
| G1d | Capture doc-only verification | [ ] | Run `pytest --collect-only -q` (docs-only loop) and archive the log + commands under `reports/2025-10-vectorization/phase_g/<timestamp>/`. |
| G2a | Log closure Attempt in docs/fix_plan.md | [ ] | After docs land, add Attempt #17 (or next) with links to the updated files, Phase G summary, and explicit CUDA follow-up pointer. |
| G2b | Update this plan’s Status Snapshot | [ ] | Refresh the snapshot to note Phase G completion, then mark rows G1a–G2c accordingly. Prepare the plan for archival once CUDA work moves under PERF-PYTORCH-004. |
| G2c | Confirm CUDA follow-up delegation | [ ] | Ensure PERF-PYTORCH-004 (or equivalent) tracks the device-placement blocker; document the handoff in both Phase G summary and fix_plan. |
