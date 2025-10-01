# Plan: PERF-PYTORCH-004 4096² Warm Performance Recovery

**Status:** Active (reopened 2025-10-10)
**Priority:** Critical — long-term goal blocker (PyTorch still 3.4× slower than C at 4096² warm)
**Related fix_plan item:** `[PERF-PYTORCH-004]` Fuse physics kernels — docs/fix_plan.md
**Created:** 2025-09-30 (refreshed 2025-10-10 by galph)

## Context
- Initiative: Speed up PyTorch nanoBragg so the warm run at 4096×4096 outperforms the C reference.
- Current baseline (reports/benchmarks/20250930-230702/benchmark_results.json):
  - C warm: **0.527 s**; PyTorch warm: **1.793 s** (speedup_warm≈0.29 → PyTorch is 3.4× slower).
  - Cold timings are dominated by torch.compile warm-up (>1.94 s) but warm latency remains unacceptable.
- Previous partial fixes (kernel hoisting, torch.compile caching) improved ≤1024² sizes but never addressed large-detector warm behavior; benchmarks marked “complete” were captured before weighted-source parity was verified.
- Dependencies: `docs/architecture/pytorch_design.md` §§2.4–3.3, `docs/development/pytorch_runtime_checklist.md`, `scripts/benchmarks/benchmark_detailed.py`, torch profiler tooling, `docs/fix_plan.md` `[PERF-PYTORCH-004]` attempt history, plan `plans/active/dtype-default-fp32/plan.md` (ensures float32 context), plateau plan for AT-012 (must not regress peak parity).

## Target Outcome
Reduce PyTorch warm-run latency at 4096² (CPU) to ≤1.2× the C binary while preserving parity/gradient guarantees and without regressing CUDA performance. Capture reproducible evidence (benchmarks + profiler traces) and update fix_plan/documentation.

---

### Phase A — Baseline Refresh & Evidence Capture
Goal: Produce authoritative, up-to-date warm/cold benchmarks (CPU + CUDA when available) with clear provenance before attempting fixes.
Prerqs: None (execute immediately).
Exit Criteria: `reports/benchmarks/<date>-4096-warm-baseline/` directory containing C vs PyTorch cold/warm metrics (sizes 512–4096), JSON + markdown summary, and notes about cache hits.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A0 | Fix weighted-source validation output path | [X] | ✅ Complete (2025-10-01 loop BJ). Added `argparse` with `--outdir` flag and timestamped default (`YYYYMMDD-HHMMSS-multi-source-normalization`). Script now produces unique directories per run. Verified with CPU+CUDA validation run (artifacts under `reports/benchmarks/20251001-004135-multi-source-normalization/`). Core tests 31/31 passed. |
| A1 | Re-run CPU benchmark sweep | [X] | ✅ Complete (2025-10-01 loop BK). Executed `env KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 512,1024,2048,4096 --device cpu --dtype float32 --iterations 5`. Results: 4096² warm 1.783s vs C 0.502s (speedup 0.28, PyTorch 3.55× slower). Commit e64ce6d. Artifacts: `reports/benchmarks/20251001-005052-cpu-baseline/`. |
| A2 | Capture C binary timings | [X] | ✅ Complete (2025-10-01 loop BK). C timings captured simultaneously by benchmark script (uses `./golden_suite_generator/nanoBragg` automatically). All correlations = 1.000000. |
| A3 | (Optional CUDA) Measure GPU warm | [-] | Skipped for Phase A. GPU benchmarking deferred to separate validation once CPU hotspots addressed. |
| A4 | Summarise baseline | [X] | ✅ Complete (2025-10-01 loop BK). Created `reports/benchmarks/20251001-005052-cpu-baseline/phase_a_summary.md` with detailed performance table, cache effectiveness metrics, and comparison to prior benchmarks. Key finding: 4096² gap unchanged at 3.55× slower (target ≤1.2×). Ready for Phase B profiling. |

### Phase B — Profiling & Hotspot Identification
Goal: Obtain profiler traces isolating the dominant kernels/ops responsible for the 4096² warm latency.
Prerqs: Phase A artifacts (ensures we profile the same workload).
Exit Criteria: Torch profiler (`.json`/Chrome trace) + optional `torch._inductor.config.print_log=True` logs stored under `reports/profiling/<date>-4096-warm/` with annotated hotspot summary.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Instrument benchmark for profiling | [X] | ✅ Complete (2025-10-01 loop BK). Added `--profile`, `--keep-artifacts`, and `--disable-compile` flags to `benchmark_detailed.py`. Implemented torch.profiler integration with Chrome trace export. Updated run_pytorch_timed() to accept profiler parameters. |
| B2 | Collect PyTorch trace | [X] | ✅ Complete (2025-10-01 loop BK). Executed `env KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --keep-artifacts --iterations 1`. Results: PyTorch 0.652s vs C 0.524s (1.25× slower). Trace saved to `reports/benchmarks/20251001-010128/profile_4096x4096/trace.json`. Note: Significantly better than Phase A baseline (3.55× slower) — requires validation. |
| B3 | Collect reference C profile (optional) | [ ] | Use `perf record --call-graph dwarf --` or `gprof` around the C binary for same config. Store flamegraph/pdf if available. |
| B4 | Summarise hotspots | [ ] | Create `hotspot_analysis.md` quantifying top PyTorch ops (polarization, lattice accumulation, memory copies) and explain why the 1-iteration run shows 1.25× vs the 5-iteration baseline at 3.55×; re-run both settings and cite the new metrics alongside any C-profile observations. |
| B5 | Profile structure-factor lookup | [ ] | Run `KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 1024 --device cpu --disable-compile --profile --iterations 1 --keep-artifacts --out reports/profiling/<stamp>-sf-eager/` to capture eager-mode trace. Focus on `Crystal._nearest_neighbor_lookup` advanced indexing cost; export Chrome trace and annotate in Phase B summary. |

### Phase C — Diagnostic Experiments & Hypothesis Testing
Goal: Narrow down root causes through controlled experiments (e.g., disable components, vary batch dimensions, inspect memory bandwidth).
Prerqs: Phase B hotspot summary.
Exit Criteria: `diagnostic_experiments.md` enumerating each experiment, findings, and decision on whether it explains the slowdown.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Measure impact of torch.compile | [ ] | Compare warm latencies with `NB_DISABLE_COMPILE=1` (pure eager) vs compiled path to quantify residual overhead; run `benchmark_detailed.py --sizes 4096 --device cpu --disable-compile` and log results. |
| C2 | Isolate per-dimension reductions | [ ] | Patch a diagnostic branch (behind flag) that flattens `(sources, phi, mosaic, oversample²)` into single dimension and performs one `torch.sum` (mirroring C loop) to see change in timing; ensure spec guarding (no merge into main). |
| C3 | Check memory allocator pressure | [ ] | Enable `PYTORCH_JIT_LOG_LEVEL=>>` or memory snapshot (`torch.cuda.memory_stats` / `torch._C._debug_set_autograd_fork_join_debug(True)`) to detect recurrent reallocations; correlate with plan tasks (ROI caching, guard tensors). |
| C4 | Evaluate dtype/precision sensitivity | [ ] | Run warm benchmark with `--dtype float64` to see whether numeric precision affects kernel fusion or caching; log results for float32 vs float64. |
| C5 | Validate weighted-source path | [ ] | Run 3-source config to ensure multi-source fixes don’t reintroduce warm penalties; capture metrics (same directory). |
| C6 | Compare HKL gather strategies | [ ] | Prototype a microbenchmark (512² ROI) that contrasts current advanced indexing `self.hkl_data[h_idx, k_idx, l_idx]` vs flattened `torch.take` / `gather` approach. Record timing + memory deltas under `reports/profiling/<stamp>-gather-study/` and decide if refactor justified. |
| C7 | Quantify pixel-coordinate memory pressure | [ ] | Log host memory usage after `_cached_pixel_coords_meters` construction for 2048² and 4096² detectors (use `psutil` + `torch.cuda.memory_allocated`). Document whether tiling/blocking is needed to stay under 1.5× C runtime. |

### Phase D — Optimization Implementation
Goal: Apply targeted code changes driven by Phase C findings (e.g., restructure reductions, hoist caches, adjust data layout) while preserving vectorization and differentiability.
Prerqs: Hypothesis chosen with supporting evidence.
Exit Criteria: Optimized branch delivering ≤1.2× C warm time at 4096² with documented reasoning.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Design fix with spec compliance checklist | [ ] | Update design note summarising intended change, referencing spec clauses (vectorization, device neutrality). Obtain supervisor sign-off before coding. |
| D2 | Implement optimization under `prompts/perf_debug.md` | [ ] | Modify simulator/crystal helpers accordingly; add focused unit/benchmark tests capturing new path. Maintain batched reductions and avoid `.item()` usage. |
| D3 | Run regression + parity tests | [ ] | `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_parallel_012.py -vv` and `NB_RUN_PARALLEL=1 NB_C_BIN=... pytest tests/test_parity_matrix.py -k AT-PARALLEL-012`. Archive logs alongside benchmark artifacts. |
| D4 | Benchmark improvement | [ ] | Repeat Phase A command set to quantify delta; ensure warm speedup ≥0.83 (PyTorch warm ≤1.2× C). Capture both CPU and CUDA metrics if available. |

### Phase E — Documentation & Closure
Goal: Update plans/docs, capture lessons learned, and archive artifacts once targets met.
Prerqs: Phase D demonstrates success.
Exit Criteria: Fix plan marked complete with evidence; documentation updated; plan archived.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| E1 | Update docs/fix_plan.md | [ ] | Add final Attempt entry summarising improvements, linking to benchmark/profiler artifacts, and explicitly stating warm speedup achieved. |
| E2 | Refresh documentation | [ ] | Update `docs/development/pytorch_runtime_checklist.md` and `docs/architecture/pytorch_design.md` if optimization changes developer guidance. |
| E3 | Archive plan | [ ] | Move this file to `plans/archive/perf-pytorch-compile-refactor/plan.md` with completion note once all tasks closed. |

## Notes & Guardrails
- Maintain device/dtype neutrality; no `.cpu()`/`.cuda()` inside vectorized paths.
- Reuse existing caches (pixel coords, misset rotations) rather than introducing per-run allocations.
- Coordinate with plateau mitigation (AT-012 plan) to avoid reintroducing float64 overrides.
- All experiments that modify physics must cite spec clauses and capture parity traces before merging.
- Protected Assets Rule: ensure any tooling updates respect files referenced in `docs/index.md` (e.g., keep `loop.sh`).
- Ensure weighted-source tooling (`scripts/validate_weighted_source_normalization.py`) remains path-agnostic so artifacts land under `reports/` on all OSes.
- When profiling eager paths (`--disable-compile`), cap detector sizes (≤1024²) to keep traces manageable while exposing `Crystal.get_structure_factor` hotspots.
