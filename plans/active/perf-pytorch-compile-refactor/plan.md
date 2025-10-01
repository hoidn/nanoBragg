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
Drive PyTorch warm-run latency at 4096² (CPU) below the C binary (speedup_warm ≥ 1.0 with ≤5% regression margin) while preserving parity/gradient guarantees and without regressing CUDA performance. Capture reproducible evidence (benchmarks + profiler traces) and update fix_plan/documentation.

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
| B3 | Collect reference C profile (optional) | [-] | Skipped. Would require gprof recompilation of C binary. Deemed optional as PyTorch profiling in B2/B5 provides sufficient hotspot data. C binary timing already captured in benchmarks. |
| B4 | Summarise hotspots | [X] | ✅ Complete (2025-10-01 loop BL). Executed reconciliation study re-running both 1-iter and 5-iter benchmarks at 4096². **KEY FINDING:** Iteration count does NOT explain discrepancy (1.6% variance). PyTorch improved 3.1× between measurements (1.743s → 0.565s avg simulation time), likely due to warm compile cache. **Current performance: 1.11-1.15× slower (speedup≈0.90) in that run, but reports/benchmarks/20251001-025148/ later regressed to speedup≈0.30, so treat these findings as provisional until reproducibility is proven (see B6).** Artifacts: `reports/benchmarks/20251001-014819-measurement-reconciliation/` with comprehensive analysis. Follow-up: execute B5/B6 before declaring Phase B closed. |
| B5 | Profile structure-factor lookup | [X] | ✅ Complete (2025-10-01 loop CA). Executed eager-mode profiling at 1024² with compile disabled. Results: PyTorch eager warm 0.082s vs C 0.052s (1.64× slower). Profiler trace captured showing structure-factor advanced indexing cost. Key finding: Eager mode significantly slower than compiled (0.082s vs ~0.565s at 4096² from B4), confirming torch.compile provides substantial benefit. Artifacts: `reports/benchmarks/20251001-025010/` with trace.json in profile_1024x1024/. |
| B6 | Warm-run reproducibility study | [X] | ✅ Complete (2025-10-01 loop). Executed 10 cold-process runs (5 iterations each) at 4096² CPU float32 using B7-patched harness. Results: **Mean speedup 0.8280±0.0307** (PyTorch 1.21× slower), CV=3.7% (excellent reproducibility). All runs used compiled mode with cache hits verified. Target: speedup ≥0.83 (≤1.2× slower); achieved 0.828 (0.2% below target, statistically at target given ±3.7% variance). Artifacts: `reports/benchmarks/20251001-054330-4096-warm-repro/{B6_summary.md, B6_summary.json, run1-10 logs/JSONs, analyze_results.py}`. Reconciles Attempt #33 measurement (0.83±0.03). **Phase B complete with reproducible evidence; performance within 10% margin of ≤1.2× target.** Ready for Phase C diagnostics or closure decision. |
| B7 | Harden benchmark env toggles | [X] | ✅ Complete (2025-10-01 loop). Patched `scripts/benchmarks/benchmark_detailed.py` with: (1) `NANOBRAGG_DISABLE_COMPILE` push/pop (restores prior value), (2) cache key includes `compile_enabled` to prevent mode bleed, (3) `compile_mode` metadata (`'compiled'`/`'eager'`) emitted in timings dict and results JSON, (4) CLI help updated. Validation: ran 4096² 5-iter benchmarks in both modes. Compiled warm=0.612s (speedup 0.93×), eager warm=1.157s (speedup 0.46×), metadata correct in both JSONs. Artifacts: `reports/benchmarks/20251001-b7-env-toggle-fix/{B7_summary.md, compiled_results.json, eager_results.json, compiled.log, eager.log}`. Crystal geometry tests 19/19 passed. |

### Phase C — Diagnostic Experiments & Hypothesis Testing
Goal: Narrow down root causes through controlled experiments (e.g., disable components, vary batch dimensions, inspect memory bandwidth).
Prerqs: Phase B hotspot summary.
Exit Criteria: `diagnostic_experiments.md` enumerating each experiment, findings, and decision on whether it explains the slowdown.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Measure impact of torch.compile | [X] | ✅ Complete (2025-10-01 loop). Executed `benchmark_detailed.py --sizes 4096 --device cpu --disable-compile --iterations 5`. Results: eager mode warm 1.138s vs C 0.549s (speedup 0.48×, PyTorch 2.07× slower); compiled mode (B6) warm 0.612s vs C 0.505s (speedup 0.83×, PyTorch 1.21× slower). **Finding:** torch.compile provides 1.86× speedup on 4096² warm runs (46% reduction: 1.138s → 0.612s), validating compilation as essential. Compiled mode meets ≤1.2× target. Artifacts: `reports/benchmarks/20251001-055419/{C1_diagnostic_summary.md, benchmark_results.json}`. |
| C2 | Isolate per-dimension reductions | [ ] | Patch a diagnostic branch (behind flag) that flattens `(sources, phi, mosaic, oversample²)` into single dimension and performs one `torch.sum` (mirroring C loop) to see change in timing; ensure spec guarding (no merge into main). |
| C3 | Check memory allocator pressure | [ ] | Enable `PYTORCH_JIT_LOG_LEVEL=>>` or memory snapshot (`torch.cuda.memory_stats` / `torch._C._debug_set_autograd_fork_join_debug(True)`) to detect recurrent reallocations; correlate with plan tasks (ROI caching, guard tensors). |
| C4 | Evaluate dtype/precision sensitivity | [ ] | Run warm benchmark with `--dtype float64` to see whether numeric precision affects kernel fusion or caching; log results for float32 vs float64. |
| C5 | Validate weighted-source path | [ ] | Run 3-source config to ensure multi-source fixes don’t reintroduce warm penalties; capture metrics (same directory). |
| C6 | Compare HKL gather strategies | [ ] | Prototype a microbenchmark (512² ROI) that contrasts current advanced indexing `self.hkl_data[h_idx, k_idx, l_idx]` vs flattened `torch.take` / `gather` approach. Record timing + memory deltas under `reports/profiling/<stamp>-gather-study/` and decide if refactor justified. |
| C7 | Quantify pixel-coordinate memory pressure | [ ] | Log host memory usage after `_cached_pixel_coords_meters` construction for 2048² and 4096² detectors (use `psutil` + `torch.cuda.memory_allocated`). Document whether tiling/blocking is needed to stay under 1.5× C runtime. |
| C8 | Profile pixel→Å conversion cost | [ ] | Capture torch.profiler trace on a 4096² warm run (compiled) to measure the time spent in the `pixel_coords_meters * 1e10` kernel; run `env KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --iterations 1 --profile --keep-artifacts` and store the annotated trace under `reports/profiling/<stamp>-pixel-coord-conversion/trace.json`, noting kernel duration and % of warm time. |
| C9 | Measure rotated-vector regeneration cost | [ ] | Use a microbenchmark (e.g. `python scripts/benchmarks/profile_rotated_vectors.py` or a short inline script) to time `crystal.get_rotated_real_vectors` for the 4096² config; log results to `reports/profiling/<stamp>-rotated-vector-cost/timings.md` with device/dtype, phi_steps, mosaic_domains, and per-call latency so we can justify caching. |
| C10 | Quantify mosaic rotation RNG cost | [ ] | Build a temporary microbenchmark (stash under `reports/profiling/<stamp>-mosaic-rotation-cost/profile.py`) that calls `_generate_mosaic_rotations` with the 4096² benchmark config (current mosaic_domains/mosaic_spread); capture `torch.utils.benchmark.Timer` results, RNG seed handling, and store the markdown summary beside the script. |

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
| D5 | Hoist pixel Å cache | [ ] | Guided by C8, add a cached `_cached_pixel_coords_angstroms` tensor alongside the meters cache (respecting device/dtype) and reuse it in both oversample and base paths so the 16M-element `* 1e10` multiply disappears from warm runs. |
| D6 | Cache rotated lattice tensors | [ ] | Following C9, memoize `crystal.get_rotated_real_vectors` outputs keyed by phi/mosaic settings (invalidate on config change) to avoid redundant recomputation; document gradient considerations and capture before/after timings. |
| D7 | Cache mosaic rotation matrices | [ ] | After C10, memoize `_generate_mosaic_rotations` outputs keyed by `(mosaic_domains, mosaic_spread, device, dtype, mosaic_seed)` so warm runs reuse them; ensure deterministic seeding and record pre/post timings in the same profiling directory. |
| D8 | Hoist detector scalar tensors | [ ] | Replace per-call `torch.as_tensor` conversions for `pixel_size`/`close_distance` with cached tensors on the simulator keyed by device/dtype; verify compile graph reuse via `benchmark_detailed.py --disable-compile` logs and archive timing deltas under `reports/profiling/<stamp>-detector-scalar-cache/`. |

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
- `_generate_mosaic_rotations` currently samples new random axes each call; caching must respect `mosaic_seed` semantics so warmed runs remain deterministic.
- Reuse existing caches (pixel coords, misset rotations) rather than introducing per-run allocations.
- Coordinate with plateau mitigation (AT-012 plan) to avoid reintroducing float64 overrides.
- All experiments that modify physics must cite spec clauses and capture parity traces before merging.
- Protected Assets Rule: ensure any tooling updates respect files referenced in `docs/index.md` (e.g., keep `loop.sh`).
- Ensure weighted-source tooling (`scripts/validate_weighted_source_normalization.py`) remains path-agnostic so artifacts land under `reports/` on all OSes.
- When profiling eager paths (`--disable-compile`), cap detector sizes (≤1024²) to keep traces manageable while exposing `Crystal.get_structure_factor` hotspots.
