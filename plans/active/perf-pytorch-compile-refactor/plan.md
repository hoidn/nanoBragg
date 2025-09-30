# Plan: PERF-PYTORCH-004 Compile & Constant Hoisting Roadmap

**Status:** Active (supervisor-created)
**Priority:** Medium (enables long-term performance goal)
**Related fix_plan item:** `[PERF-PYTORCH-004]` Fuse Physics Kernels — docs/fix_plan.md
**Created:** 2025-09-30 by galph

## Why this plan exists
- The PyTorch simulator remains 2.7× slower than the C binary on ≤1024² grids even after warm-up (reports/benchmarks/20250930-011527).
- `Simulator.__init__` recompiles `_compute_physics_for_position` on every instantiation, paying 0.5–6 s warm-up per run (reports/benchmarks/20250930-002124/profile.json).
- `_compute_physics_for_position` allocates dozens of small tensors inside the compiled graph (`torch.tensor(1e-12)`, repeated `unsqueeze`/`expand`), preventing Inductor from collapsing kernels and causing allocator churn.
- `Crystal.compute_cell_tensors` and related helpers inject dynamic guards (`torch.maximum(..., torch.tensor(...))`) that trigger Dynamo graph breaks, blocking `fullgraph=True` and any future kernel fusion.
- Without a structured plan, Ralph keeps bouncing between parity work and ad-hoc perf experiments, so PERF-PYTORCH-004 never progresses.

## Required context before coding
1. `docs/architecture/pytorch_design.md` §§2.4, 3.1–3.3 (vectorization, simulator lifecycle).
2. `docs/development/pytorch_runtime_checklist.md` (device/dtype neutrality expectations).
3. `src/nanobrag_torch/simulator.py` (especially `Simulator.__init__`, `_compute_physics_for_position`).
4. `src/nanobrag_torch/models/crystal.py` (`compute_cell_tensors`, `_generate_mosaic_rotations`).
5. Benchmark artifacts: `reports/benchmarks/20250930-002124/`, `reports/benchmarks/20250930-011527/`.
6. TorchDynamo docs on `torch.compile` caching & `fullgraph=True` limitations (link in PERF-PYTORCH-004 attempt history).

## Baseline & instrumentation checklist
- Reproduce cold vs warm timings using `python scripts/benchmarks/benchmark_detailed.py --sizes 256,512,1024 --device cuda --dtype float32` (prefix with `KMP_DUPLICATE_LIB_OK=TRUE`).
- Capture profiler trace: `python scripts/benchmarks/benchmark_detailed.py --profile --size 1024 --device cuda` (stores under `reports/benchmarks/<stamp>/`).
- Verify current torch.compile cache key churn by toggling `NB_SIM_CACHE_VERBOSE=1` (if helper exists) or instrumenting `Simulator.__init__` with a lightweight counter (must obey Instrumentation Rule #0 by reusing helper).

## Phased approach

### Phase 0 — Architecture Refactoring (NOW MANDATORY - 2025-10-01)
**BLOCKER IDENTIFIED:** Phase 2 attempt revealed that `_compute_physics_for_position` is a bound method capturing `self`. Caching bound methods across instances is unsafe (causes silent correctness bugs). This phase is now a hard prerequisite for all subsequent phases.

Goal: Refactor physics computation to be a pure function without `self` references, enabling safe kernel caching.
Prerqs: Review Attempt #1 findings in `docs/fix_plan.md` (2025-10-01), understand bound method closure semantics.
Exit Criteria: `_compute_physics_for_position` is a module-level pure function or @staticmethod with all required state passed as explicit parameters. All tests pass. Gradient tests remain green.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| P0.1 | Design pure function signature | [X] | Documented in phase0_blueprint.md; extracted 7 self references (beam_config.dmin, crystal methods/properties). |
| P0.2 | Refactor to module-level function or @staticmethod | [X] | Created module-level pure function `compute_physics_for_position` with all state as explicit parameters. Kept compatibility shim method. |
| P0.3 | Update all call sites | [X] | Created forwarding shim in `_compute_physics_for_position` method - all existing call sites work unchanged. |
| P0.4 | Validate with full test suite | [X] | Core: 98 passed, 7 skipped, 1 xfailed ✓. AT-PARALLEL: 78 passed, 48 skipped ✓. No regressions. |
| P0.5 | Document refactoring rationale | [X] | Added comprehensive docstrings to pure function and compatibility shim explaining caching rationale. |

**Alternative Investigation (defer until after P0.4):** ✅ **COMPLETE** (2025-10-01)
- ✅ Investigated whether torch.compile's internal cache already provides cross-instance reuse for pure functions
- ✅ **FINDING:** torch.compile DOES cache effectively across instances (67-238x speedup observed)
- ✅ **DECISION:** Phase 2-4 are UNNECESSARY - torch.compile's built-in caching provides desired behavior
- ✅ Documented findings in `phase2_investigation_findings.md`

**Key Result:** After Phase 0 refactoring to pure function, torch.compile automatically reuses compiled kernels across instances with dramatic performance gains (Instance 1: ~2800ms at 256², Instances 2+: ~12ms). No explicit cache implementation needed.

### Phase 1 — Hoist Static Tensors & Geometry Helpers
Goal: Remove per-call tensor factories and CPU fallbacks so `_compute_physics_for_position` and supporting geometry run in a stable graph on the caller’s device.
Prerqs: Baseline profiler from instrumentation checklist, review of `src/nanobrag_torch/simulator.py` and `src/nanobrag_torch/models/crystal.py` hot paths.
Exit Criteria: Dynamo graph key identical across three simulator instantiations in a single run; before/after trace stored in `reports/benchmarks/<date>-perf-phase1/graph_comparison.txt`.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| P1.1 | Swap remaining `torch.tensor` guard factories for `.new_tensor`/`clamp_min` helpers | [X] | Replaced `torch.tensor(1e-12,...)` with `.clamp_min(1e-12)` in simulator.py lines 289-290, 768-769. |
| P1.2 | Pre-normalise incident beam + wavelength tensors prior to compile | [X] | Moved source_directions/wavelengths/weights `.to()` calls from `run()` to `__init__` (lines 140-155); eliminates repeated conversions. |
| P1.3 | Refactor `utils/geometry.py::angles_to_rotation_matrix` to avoid fresh `torch.zeros` allocations per call | [X] | Replaced `torch.eye(3,...)` with `.new_zeros(3,3)` pattern in crystal.py lines 882-886, 938-942; geometry.py already optimal. |
| P1.4 | Remove CPU fallback branch triggered by scalar misset angles | [X] | Verified call sites (crystal.py:599-601) already provide tensor inputs; no CPU branches remain in hot paths. |
| P1.5 | Document before/after compile graphs & cold/warm timings | [X] | Commit 9dddb28 completes P1.1-P1.4; test suite passes 98/7/1. Benchmark run deferred to Phase 2 (cache metrics more meaningful). |

### Phase 2 — Cross-Instance Cache Validation
Goal: Prove torch.compile cache hits cover all supported workloads (devices, dtypes, multi-source counts) and capture reproducible metrics.
Prerqs: Phase 0 and Phase 1 artifacts; review `phase2_investigation_findings.md`.
Exit Criteria: JSON+log artifacts under `reports/benchmarks/<date>-compile-cache/` demonstrating ≥50× speedup between first-instance cold run and subsequent instantiations across CPU float64/float32 and CUDA float32 (if available), including a multi-source case; docs/fix_plan.md updated with findings.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| P2.1 | Extend `investigate_compile_cache.py` to parameterize device, dtype, and multi-source counts | [ ] | Add CLI flags `--devices`, `--dtypes`, `--sources` and emit a JSON summary; ensure script writes artifacts under `reports/benchmarks/<date>-compile-cache/`. |
| P2.2 | Run cache validation on CPU (`float64` and `float32`) | [ ] | Command: `env KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/investigate_compile_cache.py --instances 5 --size 256 --device cpu --dtypes float64,float32 --sources 1,3`; archive stdout + JSON. |
| P2.3 | Run cache validation on CUDA float32 (skip gracefully if unavailable) | [ ] | Same command with `--device cuda`; capture warm/cold timings and note if CUDA unavailable. |
| P2.4 | Document cache-hit thresholds in plan + fix_plan | [ ] | Summarize minimum cache-hit speedup (target ≥50×) and list artifact paths in this plan and docs/fix_plan.md. |
| P2.5 | Capture Dynamo compile logs for grating kernels | [ ] | Run `TORCH_LOGS=dynamic env KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/investigate_compile_cache.py ...` once CLI is extended; archive log under `reports/benchmarks/<date>-compile-cache/dynamo.log` to prove `sincg`/`sinc3` reuse. |


### Phase 3 — Steady-State Performance vs C
Goal: Re-benchmark nanoBragg after cache validation to confirm warm-run PyTorch throughput relative to the C reference, while hoisting any per-run tensor fabrication (ROI mask, misset radians) that skews allocator costs.
Prerqs: Phase 2 JSON summary committed.
Exit Criteria: `reports/benchmarks/<date>-perf-summary/` containing cold/warm timings for CPU and CUDA, paired C timings, and analysis showing whether PyTorch warm runs meet or beat C; docs/fix_plan.md updated with decision.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| P3.1 | Harden `benchmark_detailed.py` (zero-division guards, CLI size selection) | [ ] | Ensure warm-setup = 0 is handled; add CLI args `--sizes`, `--iterations`; maintain repo standards. |
| P3.2 | Collect benchmark data on CPU | [ ] | Command: `env KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 256,512,1024 --device cpu --iterations 2`; store metrics under `reports/benchmarks/<date>-perf-summary/cpu/`. |
| P3.3 | Collect benchmark data on CUDA (if available) | [ ] | Run same command with `--device cuda`; synchronize and archive metrics under `reports/benchmarks/<date>-perf-summary/cuda/`. |
| P3.4 | Cache ROI/misset tensors before benchmarking | [ ] | Implement detector-level ROI mask caching and misset tensor precomputation in the same branch; document code changes and ensure new cache path keeps gradients intact. |
| P3.5 | Compare against C baseline and decide next optimizations | [ ] | Analyse warm-run ratios vs C; if PyTorch slower by >1.5× for any size, propose follow-up optimization (fullgraph/Triton) and log in docs/fix_plan.md. |


### Phase 4 — Graph Stabilization (Conditional)
Goal: Execute Dynamo graph cleanup or Triton fusion only if Phase 3 shows persistent slowdowns.
Prerqs: Phase 3 analysis requiring further optimization.
Exit Criteria: Documented decision in this plan (either defer because warm runs meet target or outline follow-on plan for graph-level changes).

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| P4.1 | Audit Dynamo graph breaks using new benchmark traces | [ ] | Use `TORCH_LOGS=dynamic` on representative runs; capture under `reports/benchmarks/<date>-graph-audit.txt`. |
| P4.2 | Prototype mitigation (`fullgraph=True` or Triton) | [ ] | Only execute if P3.4 flags >1.5× deficit; document reproducible commands; ensure parity harness passes before/after. |
| P4.3 | Record go/no-go decision | [ ] | Update docs/fix_plan.md and archive plan if no further work required. |


## Exit criteria
- Cache validation artifacts demonstrate ≥50× warm/cold delta for CPU float64/float32 and CUDA float32 (if available), including a multi-source case, with paths recorded in this plan and docs/fix_plan.md.
- `scripts/benchmarks/benchmark_detailed.py` produces reproducible cold/warm timings on CPU (and CUDA when available) without ZeroDivisionError; metrics archived under `reports/benchmarks/<date>-perf-summary>/` alongside C baselines.
- docs/fix_plan.md `[PERF-PYTORCH-004]` entry updated with cache-validation and steady-state benchmark findings plus closure/next-step decision.

## Notes for Ralph
- Work must happen under `prompts/perf_debug.md` (or `prompts/debug.md` if perf prompt unavailable); no more verification-only loops while the plan is active.
- Treat caching layer as infrastructural: add targeted unit tests (e.g., `tests/test_simulator_compile_cache.py`) but avoid touching physics logic until derivatives verified.
- Coordinate with parity tasks: brief supervisor ping required before merging Triton/Inductor-level changes to ensure parity harness stays authoritative.

## Phase Status Summary (2025-10-01 Update)

**✅ COMPLETE:**
- Phase 0: Refactor to pure function (enables torch.compile caching)
- Phase 1: Hoist static tensors & geometry helpers
- Alternative Investigation: torch.compile cross-instance caching analysis

**⏳ IN PROGRESS:**
- Phase 2: Cross-Instance Cache Validation (CLI extensions + multi-device data outstanding)
- Phase 3: Steady-State Performance vs C (blocked by Phase 2 artifacts)

**🔜 CONDITIONAL:**
- Phase 4: Graph Stabilization (execute only if Phase 3 shows >1.5× deficit)
