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
| P0.1 | Design pure function signature | [ ] | Extract ALL self references: beam_config, fluence, r_e_sqr, kahn_factor, polarization_axis, crystal.shape, crystal.config.N_cells, etc. Document in blueprint.md. |
| P0.2 | Refactor to module-level function or @staticmethod | [ ] | Move function outside Simulator class; update signature with explicit params; ensure no closure captures. |
| P0.3 | Update all call sites | [ ] | Pass explicit parameters at every invocation site (run(), subpixel loops, etc.); verify gradients flow through. |
| P0.4 | Validate with full test suite | [ ] | Run core + AT-PARALLEL tests; ensure no regressions; confirm gradient tests pass. |
| P0.5 | Document refactoring rationale | [ ] | Add comments explaining why pure function is required for caching; reference Attempt #1 findings. |

**Alternative Investigation (defer until after P0.4):**
- Investigate whether torch.compile's internal cache already provides cross-instance reuse for pure functions
- If torch.compile already optimizes this case, Phase 2-4 may be unnecessary
- Document findings in blueprint.md before proceeding to Phase 2

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

### Phase 2 — Shared Compiled Kernel Cache
Goal: Reuse a compiled `_compute_physics_for_position` across simulator instances sharing runtime parameters.
Prerqs: Phase 0 blueprint approved, Phase 1 graph stability confirmed.
Exit Criteria: Benchmark shows second→tenth simulator instantiations skip compile (<50 ms setup) with cache-hit log in `reports/benchmarks/<date>-perf-cache/cache_hits.log`.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| P2.1 | Implement cache container per blueprint (module singleton or helper class) | [ ] | Add under `src/nanobrag_torch/utils/runtime_cache.py`; ensure device/dtype aware. |
| P2.2 | Plumb cache lookup into `Simulator.__init__` | [ ] | Inject debug counter (`NB_SIM_CACHE_DEBUG`) to print hit/miss; disable in production. |
| P2.3 | Extend benchmark script to span multiple constructions | [ ] | Update `scripts/benchmarks/benchmark_detailed.py` to loop N=5 instantiations; capture compile timings. |
| P2.4 | Validate gradients unaffected | [ ] | Run `pytest tests/test_units.py::TestCrystalGeometry::test_gradients` (or equivalent) with cache enabled. |

### Phase 3 — Remove Full-Graph Blockers
Goal: Enable `torch.compile(fullgraph=True)` by eliminating data-dependent host branches and `.item()` calls.
Prerqs: Phase 1 + 2 artifacts, knowledge of interpolation guard logic (`_tricubic_interpolation`).
Exit Criteria: Successful `torch.compile(fullgraph=True, mode="max-autotune")` run on CUDA + CPU with logs archived under `reports/benchmarks/<date>-fullgraph/`.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| P3.1 | Refactor `_tricubic_interpolation` guard (`torch.any(out_of_bounds)`) using tensor control flow | [ ] | Evaluate `torch.where` or `torch.cond`; confirm parity via targeted unit test. |
| P3.2 | Replace `.item()` driven toggles (e.g., `Crystal.interpolate`) with tensor-safe alternatives | [ ] | Introduce config-time ints or `bool` flags stored outside grad path; update tests. |
| P3.3 | Audit remaining host-side branches in simulator + models | [ ] | Use Dynamo trace logs to identify auto-guards; capture findings in `reports/benchmarks/<date>-fullgraph/host_branch_audit.md`. |
| P3.4 | Attempt `fullgraph=True` compile on CPU & CUDA | [ ] | Record command, success/failure, and fallback reasons; include stack traces if still blocked. |

### Phase 4 — Kernel Fusion Follow-Up
Goal: Quantify kernel launch reduction and scope custom kernel fallback if Dynamo remains fragmented.
Prerqs: Phase 3 results (success or documented blocker) plus profiler baselines.
Exit Criteria: Report `reports/benchmarks/<date>-fusion/summary.md` capturing kernel counts before/after and go/no-go decision on Triton prototype.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| P4.1 | Capture profiler traces pre/post Phase 3 | [ ] | Use `torch.profiler` or Nsight; annotate kernel counts and durations. |
| P4.2 | Decide on Triton fallback scope | [ ] | If Dynamo still launches >5 kernels, outline Triton MVP (oversample=1) with acceptance tests. |
| P4.3 | Draft Triton experiment checklist | [ ] | Only execute after parity backlog clears; store under `plans/archive/` if deferred. |

## Exit criteria
- Repeated simulator construction (e.g., 10 consecutive runs at 1024², float32, CUDA) shows ≤50 ms setup after first compile (cache hit confirmed).
- `torch.profiler` trace shows ≤3 kernels dominating runtime for `_compute_physics_for_position` (vs current ~20).
- Benchmark script demonstrates ≥2× speedup at 1024² relative to current warm baseline without parity regressions.
- `docs/fix_plan.md` `[PERF-PYTORCH-004]` entry updated with attempt logs, metrics, and this plan marked as complete (move to archive).

## Notes for Ralph
- Work must happen under `prompts/perf_debug.md` (or `prompts/debug.md` if perf prompt unavailable); no more verification-only loops while the plan is active.
- Treat caching layer as infrastructural: add targeted unit tests (e.g., `tests/test_simulator_compile_cache.py`) but avoid touching physics logic until derivatives verified.
- Coordinate with parity tasks: brief supervisor ping required before merging Triton/Inductor-level changes to ensure parity harness stays authoritative.
