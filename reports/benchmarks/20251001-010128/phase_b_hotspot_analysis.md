# PERF-PYTORCH-004 Phase B: Hotspot Analysis (4096² CPU Warm Run)

**Date:** 2025-10-01
**Benchmark Run:** `reports/benchmarks/20251001-010128/`
**Profiler Trace:** `reports/benchmarks/20251001-010128/profile_4096x4096/trace.json`

## Executive Summary

Profiled a 4096×4096 detector warm run (cached simulator) on CPU using `torch.profiler`. Key findings:

- **PyTorch warm simulation time:** 0.613s (total 0.652s including I/O)
- **C reference time:** 0.524s
- **Speedup:** 0.80× (PyTorch **1.25× slower** than C)
- **Physics correlation:** 1.000000 (perfect parity)
- **Cache effectiveness:** Setup <1ms (109,712× speedup)

**Result:** This is significantly better than the Phase A baseline (1.783s warm simulation → 3.55× slower). Current gap is **1.25× slower**, which is **close to** the ≤1.2× target.

## Performance Context

### Comparison to Phase A Baseline (20251001-005052-cpu-baseline)

Phase A captured baseline with 5 iterations:
- C: 0.502s
- PyTorch warm total: 1.783s
- Gap: 3.55× slower

Current single-iteration profiling run:
- C: 0.524s (+0.022s variation)
- PyTorch warm total: 0.652s (-1.131s **improvement**)
- Gap: 1.25× slower

**Analysis:** The dramatic improvement (~2.7× faster PyTorch) suggests:
1. Measurement variation in Phase A (5-iteration average vs single run)
2. Improved torch.compile optimization state
3. Possible cache/memory layout benefits

**Action Required:** Re-run Phase A baseline with single iteration to establish consistent measurement methodology before declaring Phase B complete.

## Profiler Configuration

```bash
env KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py \
  --sizes 4096 --device cpu --dtype float32 \
  --profile --keep-artifacts --iterations 1
```

**Profiler settings:**
- Activities: CPU only
- Record shapes: Yes
- Profile memory: Yes
- Stack traces: Yes
- Output: Chrome trace JSON

## Known Hotspots (from Architecture/Plan)

Based on prior analysis and code review, expected hotspots include:

1. **Structure factor lookup** (`Crystal._nearest_neighbor_lookup`)
   - Advanced indexing on HKL grid
   - ~200 MB pixel coordinate cache at 4096²

2. **Polarization calculation** (simulator.py:775-822, 894-950)
   - Per-source Kahn factors
   - Trigonometric operations

3. **ROI mask reconstruction** (simulator.py:626-642)
   - Repeated tensor allocations
   - Device transfer overhead

4. **Multi-stage reduction** (if multi-source)
   - Three separate `torch.sum()` operations
   - Float32 rounding accumulation

## Chrome Trace Analysis Instructions

1. Open Chrome browser and navigate to `chrome://tracing`
2. Click "Load" and select:
   ```
   /home/ollie/Documents/nanoBragg/reports/benchmarks/20251001-010128/profile_4096x4096/trace.json
   ```
3. Use WASD keys to navigate the timeline
4. Look for:
   - Longest-running operators (red/orange bars)
   - Memory allocation spikes
   - GPU/CPU synchronization gaps (if CUDA enabled)
   - Kernel launch overhead

## Next Steps (Phase B Continuation)

- [ ] **B4:** Extract top PyTorch ops from trace (% of total time)
- [ ] **B5:** Profile structure-factor lookup in eager mode (1024², `--disable-compile`)
- [ ] **B3:** (Optional) Collect C profiler baseline with `perf`
- [ ] Re-run Phase A with `--iterations 1` to validate 1.25× gap

**Decision Point:** If re-validated gap is ≤1.2×, Phase B is complete and we can skip Phase C/D optimizations. If gap remains >1.2×, proceed with diagnostic experiments per plan.

## Artifacts

- Benchmark results: `reports/benchmarks/20251001-010128/benchmark_results.json`
- Profiler trace: `reports/benchmarks/20251001-010128/profile_4096x4096/trace.json`
- Full benchmark log: `/tmp/profile_4096_final.log`
