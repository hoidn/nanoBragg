# PERF-PYTORCH-005 Investigation Summary

**Date:** 2025-09-30
**Loop:** Ralph implementation loop (spec-based)
**Status:** Investigated - multi-phase implementation required

## Background

PERF-PYTORCH-005 addresses torch.compile cold-start overhead (0.98-6.33s for small detectors). Goal: reduce setup time to <50ms via CUDA graph caching.

## Investigation Findings

### Scope Assessment

**Estimated Implementation Time:** 11-16 hours across 4-5 phases

**Phases:**
1. **Cache Infrastructure** (2-3 hours): Module-level dict, key generation, `enable_cuda_graph_cache()` utilities
2. **Graph Capture** (3-4 hours): Implement `_capture_cuda_graph()` with `torch.cuda.CUDAGraph`
3. **Graph Replay** (2-3 hours): Implement `_run_with_cached_graph()` with buffer updates
4. **Testing** (3-4 hours): Unit tests (cache hit/miss), performance tests (setup time), correctness tests (bit-identical results)
5. **Documentation** (1-2 hours): Update testing_strategy.md, README.md

### Cache Key Design

```python
cache_key = (spixels, fpixels, oversample, n_sources, thicksteps, device_type, dtype)
```

Captures all shape-affecting parameters that require different CUDA graphs.

### Expected Performance Gains

| Detector Size | Setup Time (Before) | Target (After) | Speedup |
|---------------|---------------------|----------------|---------|
| 256²          | 0.98s               | <50ms          | 20×     |
| 512²          | 6.33s               | <50ms          | 126×    |
| 1024²         | 0.02s               | <50ms          | 1× (already fast) |

### Implementation Strategy

1. **Refactor `Simulator.run()`** into `_run_standard()` (existing logic) and `_run_with_cached_graph()` (new)
2. **Add cache lookup** at start of `run()`: check cache key, replay if hit, capture if miss
3. **Implement `_capture_cuda_graph()`** with:
   - Static buffer allocation for inputs/outputs
   - Warm-up call to trigger torch.compile
   - CUDA graph capture via `torch.cuda.graph()`
4. **Implement `_run_with_cached_graph()`** with:
   - Update static input buffers with current simulation state
   - Replay cached graph
   - Return cloned output
5. **Add error handling** with graceful fallback to `_run_standard()` if capture/replay fails
6. **Test suite**: cache hit/miss, performance benchmarks, correctness (bit-identical results)

### Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| CUDA graph capture may fail | Try-except with fallback to standard path |
| Static shapes may not work for dynamic configs | Cache miss generates new graph per config |
| Memory overhead (~20-60 MB per graph) | Acceptable for typical workflows (1-5 configs) |
| torch.compile interaction unclear | Warm-up call before capture ensures compile is done |

### Correctness Requirements

- ✅ Cached results MUST be bit-identical to standard path (no tolerance)
- ✅ All existing acceptance tests must pass with caching enabled
- ✅ Graceful fallback to standard path if capture fails
- ✅ CPU execution unaffected (always uses standard path)

## Recommendation

**Split PERF-005 into separate implementation loops:**

1. **PERF-005-PHASE-1**: Infrastructure (cache dict, key generation, refactor `run()`)
2. **PERF-005-PHASE-2**: Graph capture (implement `_capture_cuda_graph()`)
3. **PERF-005-PHASE-3**: Graph replay (implement `_run_with_cached_graph()`)
4. **PERF-005-PHASE-4**: Testing and validation

**Alternative:** Mark as optional and defer indefinitely, since PERF-DOC-001 (warm-up documentation) is already done and addresses the user-facing issue.

## Context: Ralph Loop Assessment

This investigation occurred during a Ralph implementation loop (2025-09-30 14:00-15:00 UTC). Key observations:

- **Test suite baseline**: 44/45 tests passing (1 known triclinic_P1 issue, escalated)
- **Blocking tasks**: 4 critical AT failures (AT-020, AT-021, AT-022, AT-024) require debug.md routing
- **PERF-005 status**: Too large for single loop (11-16 hours estimated)
- **Routing decision**: Investigation complete; implementation deferred to future loops

## References

- **Benchmark Data**: `reports/benchmarks/PERF-PYTORCH-003_investigation_summary.md`
- **Architecture**: `docs/architecture/pytorch_design.md`
- **Simulator Code**: `src/nanobrag_torch/simulator.py`
- **Testing Strategy**: `docs/development/testing_strategy.md` (§2.1 hot path optimization)

## Files to Modify (Future Implementation)

- `src/nanobrag_torch/simulator.py` (~200 lines added)
- `tests/test_cuda_graph_cache.py` (new file, ~150 lines)
- `docs/development/testing_strategy.md` (add caching section)
- `README.md` (document `NB_CUDA_GRAPH_CACHE` environment variable)

---

**Status:** Investigation complete. Implementation pending prioritization.