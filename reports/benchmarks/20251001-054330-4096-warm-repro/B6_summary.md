# PERF-PYTORCH-004 Phase B Task B6: Warm-Run Reproducibility

**Date:** 20251001-054330
**Sample size:** 10 cold-process runs
**Configuration:** 4096×4096 detector, CPU, float32, 5 iterations per run

## Results

### Performance Statistics

| Metric | Value |
|--------|-------|
| Mean speedup | 0.8280 |
| PyTorch slowdown | 1.21× |
| Std deviation | 0.0307 |
| CV (reproducibility) | 3.7% |
| Speedup range | [0.7917, 0.8966] |

### Absolute Times

| Implementation | Mean | Std Dev |
|---------------|------|----------|
| PyTorch warm | 0.618s | ±0.018s |
| C warm | 0.511s | ±0.013s |

### Metadata

- Compile modes: compiled
- Cache hits: 10/10 runs

## Target Assessment

**Target:** PyTorch ≤1.2× slower than C (speedup ≥0.83)

✗ **BELOW TARGET** - Mean speedup 0.8280 below target 0.83
  Gap: 0.0020 (0.2% below)

## Historical Context

| Measurement | Speedup | PyTorch Slowdown | Notes |
|-------------|---------|------------------|-------|
| Phase A baseline | 0.28 | 3.55× | Initial measurement |
| Attempt #31 | 0.83 | 1.21× | Appeared to meet target |
| Attempt #32 | 0.30 | 3.33× | Regression detected |
| Attempt #33 | 0.83±0.03 | 1.21× | CV=3.9%, 10 runs |
| **B6 (current)** | **0.83±0.03** | **1.21×** | With B7 harness fix |

## Conclusion

**Reproducibility:** Excellent (CV=3.7% < 5%)

Phase B target not met. Proceed to Phase C diagnostics to identify bottlenecks.
