# Plan Task B7: Benchmark Environment Toggle Fix — Summary

**Date:** 2025-10-01
**Plan:** `plans/active/perf-pytorch-compile-refactor/plan.md` Phase B, task B7
**Objective:** Harden benchmark env toggles to prevent compile mode confusion

## Problem Statement

The benchmark harness (`scripts/benchmarks/benchmark_detailed.py`) had several bugs:

1. **Wrong env var name:** Set `NB_DISABLE_COMPILE` but Simulator reads `NANOBRAGG_DISABLE_COMPILE`
2. **No env restoration:** Deleted env var immediately, so downstream callers inherited indeterminate state
3. **Cache bleed:** Compiled simulators reused in eager mode (and vice versa) due to cache key not including compile mode
4. **Missing metadata:** No `compile_mode` field in benchmark_results.json to verify actual execution mode

## Implementation

### Code Changes

1. **Cache key enhancement:** Added `compile_enabled` parameter to `get_cache_key()` so compiled/eager simulators are cached separately
2. **Env var push/pop:** Store prior `NANOBRAGG_DISABLE_COMPILE` value and restore it after simulator creation
3. **Metadata emission:** Added `compile_mode` field (`'compiled'` or `'eager'`) to timings dict and results JSON
4. **Help text update:** Documented the flag behavior and cache invalidation rule

### Files Modified

- `scripts/benchmarks/benchmark_detailed.py` (lines 36-50, 111-164, 246-248, 437-438)

## Validation Results

### Compiled Mode (torch.compile enabled)

Command:
```bash
env KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py \
  --sizes 4096 --device cpu --dtype float32 --iterations 5
```

Results (4096² warm):
- **PyTorch warm:** 0.612s
- **C:** 0.568s
- **Speedup:** 0.93× (PyTorch 1.08× slower)
- **Correlation:** 1.0
- **compile_mode_warm:** `"compiled"` ✅

### Eager Mode (torch.compile disabled)

Command:
```bash
env KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py \
  --sizes 4096 --device cpu --dtype float32 --iterations 5 --disable-compile
```

Results (4096² warm):
- **PyTorch warm:** 1.157s
- **C:** 0.528s
- **Speedup:** 0.46× (PyTorch 2.19× slower)
- **Correlation:** 1.0
- **compile_mode_warm:** `"eager"` ✅

## Key Findings

1. **Mode separation verified:** Compiled mode (0.612s) is 1.89× faster than eager mode (1.157s)
2. **Metadata correctness:** JSON records show correct `compile_mode` field matching CLI flags
3. **Cache isolation:** No mode bleed observed — compiled and eager simulators cached separately
4. **Env restoration:** No warnings about missing/incorrect env vars in subsequent runs

## Artifacts

- `reports/benchmarks/20251001-b7-env-toggle-fix/compiled_results.json`
- `reports/benchmarks/20251001-b7-env-toggle-fix/eager_results.json`
- `reports/benchmarks/20251001-b7-env-toggle-fix/compiled.log` (full stdout)
- `reports/benchmarks/20251001-b7-env-toggle-fix/eager.log` (full stdout)

## Exit Criteria

All exit criteria from Plan B7 met:

- ✅ `NANOBRAGG_DISABLE_COMPILE` pushed/popped safely (prior value restored)
- ✅ Cache key includes compile mode (prevents mode bleed)
- ✅ `compile_mode` metadata emitted in benchmark_results.json
- ✅ CLI help explains flag and cache invalidation
- ✅ Validation run with both compiled and eager modes captured

## Next Actions

1. Mark Plan B7 as `[X]` complete
2. Re-run Plan B6 (ten-process reproducibility) with fixed harness to capture cache-hit + compile-mode metadata
3. Update `docs/fix_plan.md` with B7 completion entry
