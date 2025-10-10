# Phase C1 Warm Profiler Capture - Summary

**Date:** 2025-10-10
**Timestamp:** 20251010T043632Z
**Task:** VECTOR-TRICUBIC-002 Phase C1 - Warm profiler capture for 4096² detector
**Status:** ❌ **FAILED** - Parity regression confirmed

## Command Executed

```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py \
  --sizes 4096 \
  --device cpu \
  --dtype float32 \
  --profile \
  --iterations 1 \
  --keep-artifacts
```

## Results

### Correlation Metrics
- **Correlation (cold):** 0.721175 ❌ (threshold: ≥0.999)
- **Correlation (warm):** 0.721175 ❌ (threshold: ≥0.999)

### Performance Metrics
- **C time:** 0.781s
- **PyTorch COLD:** 2.542s (speedup: 0.31x - C faster)
- **PyTorch WARM:** 0.657s (speedup: 1.19x - PyTorch faster)
- **Cache effectiveness:** 72607.7x faster setup (✓ meets <50ms criterion)

### Profiler Artifacts
- **Trace file:** `reports/benchmarks/20251009-213704/profile_4096x4096/trace.json`
- **Benchmark results:** `reports/benchmarks/20251009-213704/benchmark_results.json`
- **Full stdout log:** `reports/2026-01-vectorization-gap/phase_b/20251010T043632Z/benchmark_stdout.log`

## Critical Findings

### Parity Regression Confirmed
The correlation of **0.721175** confirms the parity regression documented in `docs/fix_plan.md` under `[VECTOR-PARITY-001]`. This is significantly below the required threshold of ≥0.999.

### Impact on Vectorization Work
**This profiler evidence CANNOT be used for Phase C2/C3 hotspot mapping** until the parity regression is resolved. Using these traces would risk:
- Mis-prioritizing vectorization work based on incorrect physics
- Introducing fixes that optimize the wrong code paths
- Wasting engineering effort on phantom performance issues

## Blocking Dependencies

### [VECTOR-PARITY-001] Must Complete First
From `docs/fix_plan.md`:
- **Reproduction:** ROI comparison shows corr_roi=0.999999999 ✓, but full-frame corr_warm=0.721175 ❌
- **Next Actions (Phase C):** Trace comparison for pixels (2048,2048), (1791,2048), (4095,2048)
- **Exit Criteria:** Correlation ≥0.999 and |sum_ratio−1| ≤5×10⁻³ for full-frame

## Recommendations

### Immediate Next Steps
1. **Do NOT proceed with Phase C2/C3** until parity is restored
2. **Execute [VECTOR-PARITY-001] Phase C1-C3** parallel trace comparison:
   - Add C trace instrumentation for the three pixel coordinates
   - Generate PyTorch traces using `scripts/debug_pixel_trace.py`
   - Identify first divergence and root cause
3. **Rerun this profiler capture** after parity fix is validated

### Artifact Retention
- Keep these profiler artifacts for historical reference
- Mark as "BLOCKED - Parity Regression" in any documentation
- Do not reference these traces in vectorization planning until revalidated

## torch.compile Status
- Compilation: ENABLED (default)
- Device: CPU
- Dtype: float32
- No Dynamo warnings observed in stdout

## Environment
- PyTorch version: 2.7.1+cu126
- CUDA available: True
- GPU: NVIDIA GeForce RTX 3090 (not used - CPU run)
- CPU cores: 32
- Total RAM: 125.7 GB
- KMP_DUPLICATE_LIB_OK: TRUE

## References
- `docs/fix_plan.md` › `[VECTOR-PARITY-001]` (blocking)
- `docs/fix_plan.md` › `[VECTOR-GAPS-002]` (downstream dependency)
- `docs/fix_plan.md` › `[VECTOR-TRICUBIC-002]` (this task)
- `plans/active/vectorization.md` Phase C1 (this attempt)
- `docs/development/testing_strategy.md` §1.4 & §2 (parity requirements)
