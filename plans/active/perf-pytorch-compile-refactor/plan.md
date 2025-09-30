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

### Phase 0 — Caching design (no code changes yet)
- Document desired cache key: `(device.type, device.index, dtype, oversample, n_sources, compiled_options)`.
- Decide whether to store compiled callable on the `Crystal`/`Simulator` instance, a module-level LRU, or a new `RuntimeKernelCache` helper under `src/nanobrag_torch/utils/`.
- Confirm lifecycle interactions with `torch.compile` (thread safety, deterministic teardown).

### Phase 1 — Hoist static tensors & reshape ops
- Replace per-call `torch.tensor(1e-12, device=...)` constructs with `.new_tensor(1e-12)` or `clamp_min` so they originate outside Dynamo-traced regions.
- Audit `_compute_physics_for_position` for redundant `unsqueeze/expand`; prefer `view`/`reshape` when shapes are static to improve fusion opportunities.
- Refactor `Crystal.compute_cell_tensors` guards to use `.clamp_min`/`torch.where` instead of `torch.maximum(..., torch.tensor(...))` to maintain graph continuity.
- Ensure constants live on the caller’s device/dtype via helper factories (e.g., `device_dtype_tensor(reference, value)`).
- Normalize incident beam direction / wavelength tensors on the caller before entering the compiled graph so the current `incident_beam_direction.to(...)` call disappears from `_compute_physics_for_position`.

### Phase 2 — Shared compiled kernel cache
- Implement lazy cache: first instantiation compiles `_compute_physics_for_position`, stores the graph; subsequent simulators with matching key reuse callable without recompilation.
- Add diagnostic counter (behind debug flag) to confirm reuse during benchmarks.
- Update `scripts/benchmarks/benchmark_detailed.py` to exercise caching across multiple simulator constructions.

### Phase 3 — Remove fullgraph blockers
- Target `Crystal.compute_cell_tensors` and interpolation paths for data-dependent branches that cause graph breaks (`torch.any(out_of_bounds)`). Replace with tensor-friendly control flow (e.g., `torch.where`) or `torch.cond` wrappers as allowed by differentiability rules.
- Once guards removed, experiment with `torch.compile(fullgraph=True, mode="max-autotune")` on CUDA and `reduce-overhead` on CPU. Capture success/failure logs under `reports/benchmarks/<date>-fullgraph/`.
- Eliminate `.item()`-based host decisions that sever graphs (e.g., auto-enabling `Crystal.interpolate` via `self.N_cells_a.item()`). Move those checks to configuration-time integers or tensor-safe comparisons so Dynamo sees a pure tensor program.

### Phase 4 — Kernel fusion follow-up
- If fullgraph succeeds, compare kernel launch count before/after with `torch.profiler`. Document improvement.
- If Dynamo still breaks, sketch Triton kernel MVP covering oversample=1 single-source path. Defer implementation until parity backlog clears, but record findings.

## Exit criteria
- Repeated simulator construction (e.g., 10 consecutive runs at 1024², float32, CUDA) shows ≤50 ms setup after first compile (cache hit confirmed).
- `torch.profiler` trace shows ≤3 kernels dominating runtime for `_compute_physics_for_position` (vs current ~20).
- Benchmark script demonstrates ≥2× speedup at 1024² relative to current warm baseline without parity regressions.
- `docs/fix_plan.md` `[PERF-PYTORCH-004]` entry updated with attempt logs, metrics, and this plan marked as complete (move to archive).

## Notes for Ralph
- Work must happen under `prompts/perf_debug.md` (or `prompts/debug.md` if perf prompt unavailable); no more verification-only loops while the plan is active.
- Treat caching layer as infrastructural: add targeted unit tests (e.g., `tests/test_simulator_compile_cache.py`) but avoid touching physics logic until derivatives verified.
- Coordinate with parity tasks: brief supervisor ping required before merging Triton/Inductor-level changes to ensure parity harness stays authoritative.
