# Phase B1 Profiler Rerun (20251010T020149Z) - FAILED

## Executive Summary
**Status:** FAILED - Parity threshold not met
**Date:** 2025-10-10 (UTC)
**Phase:** VECTOR-GAPS-002 Phase B1

## Failure Metrics
- **correlation_warm:** 0.721175 (threshold: ≥0.999)
- **correlation_cold:** 0.721175 (threshold: ≥0.999)
- **Failure margin:** 0.278 below threshold
- **sum_ratio:** not computed (temp files deleted)

## Performance Metrics (for reference only)
- **C time:** 0.814s
- **PyTorch warm time:** 0.663s
- **speedup_warm:** 1.23x (PyTorch faster)
- **Setup speedup:** 88778.4x (warm cache)

## Root Cause Analysis
The extremely low correlation (0.72 vs expected >0.999) indicates a **fundamental parity issue** between C and PyTorch implementations, not a performance optimization problem. This suggests:

1. **Possible causes:**
   - Source weighting divergence (SOURCE-WEIGHT-001 may not be fully resolved)
   - Device/dtype mismatch (float32 vs float64 precision issues)
   - Recent code changes introducing numerical differences
   - RNG seed mismatches
   - Scaling/normalization differences

2. **Evidence:**
   - Both cold and warm runs show identical low correlation (0.72)
   - This rules out cache/compilation issues
   - Points to fundamental computation difference

## Next Actions (per input.md blocked protocol)
1. ✅ Stashed profile_run.log and benchmark_results.json to `failed/`
2. ✅ Ran pytest --collect-only -q > collect.log
3. ⏭️ Update docs/fix_plan.md with failure attempt
4. ⏭️ **BLOCK Phase B** - Cannot proceed with profiler analysis until C↔PyTorch parity restored
5. ⏭️ Investigate correlation failure with parallel trace debugging

## Artifacts
- Failure logs: `reports/2026-01-vectorization-gap/phase_b/20251010T020149Z/failed/`
- Profiler trace: `reports/benchmarks/20251009-190219/profile_4096x4096/trace.json`
- Test collection: `collect.log`
- Environment: `env.json`
- Commands: `commands.txt`

## Recommendations
1. **Immediate:** Run AT-PARALLEL parity matrix to identify which tests are failing
2. **Root cause:** Use parallel trace debugging (debugging.md §2.1) to find first divergence
3. **Regression check:** Review commits since last known-good parity (SOURCE-WEIGHT-001 Phase H)
4. **Do NOT proceed to Phase B2** until correlation ≥0.999 is restored
