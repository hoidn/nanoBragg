# PERF-PYTORCH-004 Phase A Summary: Baseline Benchmarking

**Date:** 2025-10-01 00:50:52
**Commit:** e64ce6d33f48ccabcbb77719d1dc392d25aa1f92
**Plan Reference:** `plans/active/perf-pytorch-compile-refactor/plan.md` Phase A

## Executive Summary

Completed Phase A baseline benchmarking for PERF-PYTORCH-004. Results confirm the critical performance gap: **PyTorch is 3.55× slower than C at 4096² warm runs** (1.783s vs 0.502s), failing the target criterion of ≤1.2× slower.

## Configuration

- **Device:** CPU (32 cores)
- **Dtype:** float32
- **Iterations:** 5 per size
- **Sizes:** 512², 1024², 2048², 4096²
- **C Binary:** `./golden_suite_generator/nanoBragg`
- **Environment:** `KMP_DUPLICATE_LIB_OK=TRUE`

## Detailed Results

### Performance Table

| Size      | Pixels       | C (s) | PyTorch COLD (s) | PyTorch WARM (s) | Warm Speedup | Correlation |
|-----------|--------------|-------|------------------|------------------|--------------|-------------|
| 512²      | 262,144      | 0.014 | 4.989            | 0.006            | 2.22×        | 1.000000    |
| 1024²     | 1,048,576    | 0.044 | 0.667            | 0.093            | 0.47× (C 2.11× faster) | 1.000000 |
| 2048²     | 4,194,304    | 0.136 | 0.475            | 0.428            | 0.32× (C 3.15× faster) | 1.000000 |
| **4096²** | **16,777,216** | **0.502** | **1.919**    | **1.783**        | **0.28× (C 3.55× faster)** | **1.000000** |

### Cache Effectiveness

All sizes demonstrate excellent torch.compile cache effectiveness:

| Size  | Setup COLD (ms) | Setup WARM (ms) | Setup Speedup | Exit Criteria |
|-------|-----------------|-----------------|---------------|---------------|
| 512²  | 5.8             | 0.0             | 6,035×        | ✓             |
| 1024² | 8.2             | 0.0             | 8,627×        | ✓             |
| 2048² | 39.0            | 0.0             | 18,177×       | ✓             |
| 4096² | 162.4           | 0.0             | 113,508×      | ✓             |

**Average setup speedup:** 36,587× (all sizes meet <50ms warm setup criterion)

## Key Findings

1. **Critical Gap at 4096²:** PyTorch warm run is **3.55× slower** than C (1.783s vs 0.502s). This exceeds the ≤1.2× target by a factor of ~3×.

2. **Performance Degradation with Size:** The performance gap worsens as detector size increases:
   - 512²: PyTorch **2.22× faster** (excellent) ✓
   - 1024²: C 2.11× faster (tolerable)
   - 2048²: C 3.15× faster (poor)
   - 4096²: C 3.55× faster (critical) ✗

3. **Excellent Numerical Agreement:** All correlations = 1.000000, confirming correctness.

4. **Cache System Working:** torch.compile cache delivers massive setup speedups (6k-114k×), with warm setup consistently <1ms.

## Comparison with Prior Benchmarks

From `reports/benchmarks/20250930-230702/benchmark_results.json`:
- Previous 4096² warm: 1.793s (C 0.527s → speedup 0.29)
- **Current 4096² warm: 1.783s (C 0.502s → speedup 0.28)**
- **Δ = -0.010s PyTorch improvement, -0.025s C improvement**

Performance gap remains essentially unchanged. Previous work did not resolve the large-detector bottleneck.

## Next Steps (Phase B)

Per plan guidance, proceed to Phase B profiling:

1. **B1-B2:** Capture torch profiler trace for 4096² warm run to identify hotspots
2. **B5:** Profile eager-mode structure factor lookup (1024² detector, `--disable-compile`)
3. **B3:** (Optional) Collect C profiler baseline with `perf` or `gprof`
4. **B4:** Summarize hotspot analysis

Focus areas based on prior investigation:
- Pixel coordinate caching (~200 MB at 4096²)
- Structure factor advanced indexing (`Crystal._nearest_neighbor_lookup`)
- ROI mask reconstruction overhead
- Multi-stage reduction patterns

## Artifacts

- Benchmark output: `benchmark_output.log`
- JSON results: `results/benchmark_results.json`
- Command: `env KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 512,1024,2048,4096 --device cpu --dtype float32 --iterations 5`

## Status

- Phase A Tasks A1-A2: ✓ Complete (C and PyTorch timings captured)
- Phase A Task A3: Skipped (no CUDA benchmark requested for Phase A)
- Phase A Task A4: ✓ Complete (this summary)

**Ready to proceed to Phase B (Profiling & Hotspot Identification).**
