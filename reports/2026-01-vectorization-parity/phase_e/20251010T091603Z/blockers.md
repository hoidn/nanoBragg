# Phase E Blocker Report

**Date:** 2025-10-10T09:16:03Z
**Git SHA:** (see below)
**Active Item:** [VECTOR-PARITY-001] Phase E full-frame validation

## Blocker Summary

**4096² benchmark correlation FAILED spec threshold:**
- **Actual:** 0.721177
- **Required:** ≥0.999
- **Delta:** −0.277823 (far below threshold)

## Environment

```bash
NB_C_BIN=./golden_suite_generator/nanoBragg
KMP_DUPLICATE_LIB_OK=TRUE
Device: CPU
Dtype: float32
```

## Commands Executed

### 1. Benchmark (FAILED)
```bash
export NB_C_BIN=./golden_suite_generator/nanoBragg && \
export KMP_DUPLICATE_LIB_OK=TRUE && \
python scripts/benchmarks/benchmark_detailed.py \
  --sizes 4096 \
  --device cpu \
  --dtype float32 \
  --iterations 1 \
  --profile \
  --keep-artifacts
```

**Result:**
- Correlation (warm): 0.721177 ❌
- C time: 0.532s
- PyTorch time: 0.654s (warm)
- Speedup: 0.81× (C faster)

## Observations

1. **ROI vs Full-Frame Divergence:**
   - ROI parity (512² center, `[TEST-GOLDEN-001]` Attempt #20): corr=1.000000 ✅
   - Full-frame parity (4096² complete): corr=0.721177 ❌
   - **Implication:** Physics is correct in signal-rich central regions but diverges at edges/background

2. **Phase D5 Lattice Fix Limitations:**
   - Lattice vector unit conversion (Attempt #15, commit bc36384c) resolved ROI parity
   - Did NOT resolve full-frame parity
   - **Hypothesis:** Additional physics bugs exist outside the central ROI

3. **Correlation Unchanged from Phase B:**
   - Phase B baseline (Attempt #0, 2025-12-30): corr_warm=0.721175
   - Phase E rerun (Attempt #21, 2025-10-10): corr_warm=0.721177
   - **Delta:** +0.000002 (effectively unchanged despite Phase D1-D6 fixes)

4. **Regenerated Golden Data Validated:**
   - `[TEST-GOLDEN-001]` Phase C (Attempt #20) confirmed ROI parity with regenerated `tests/golden_data/high_resolution_4096/image.bin`
   - Golden data is NOT the issue; the PyTorch simulator has residual full-frame bugs

## Next Actions (Supervisor Sign-Off Required)

### Option 1: ROI-Only Gating (Scope Reduction)
- Treat full-frame parity as out-of-scope for Phase E
- Gate vectorization work on ROI parity only (corr≥0.999 for 512² central window)
- Document full-frame limitation in known issues
- **Risk:** Ships with edge/background physics bugs

### Option 2: Extended Trace Debugging (Root Cause)
- Generate C + PyTorch traces for edge pixels (e.g., (0,0), (4095,4095), (2048,0))
- Compare against central pixel traces to isolate edge-specific divergence
- Likely culprits: boundary handling, background calculation, edge solid-angle factors
- **Effort:** 2-3 additional debugging loops

### Option 3: Threshold Adjustment (Pragmatic)
- Lower full-frame correlation threshold to 0.72 (matching observed parity)
- Document as "acceptable engineering tolerance" pending future improvement
- **Risk:** Masks underlying physics bugs; not spec-compliant

## Artifacts

- Benchmark log: `reports/2026-01-vectorization-parity/phase_e/20251010T091603Z/logs/benchmark.log`
- Benchmark results: `reports/benchmarks/20251010-021637/benchmark_results.json`
- Profiler trace: `reports/benchmarks/20251010-021637/profile_4096x4096/trace.json`

## Recommendation

**HALT Phase E until supervisor selects mitigation strategy.** Do not proceed with nb-compare or pytest steps; correlation failure is blocking per `input.md` line 8 guidance.
7ac34ad3ed8d3bf2681d630e233a973a0f3cd195
