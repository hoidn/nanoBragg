
# Phase B1 profiler rerun (20251010T021229Z) — BLOCKED

**Status:** PARITY THRESHOLD NOT MET

## Metrics

- correlation_warm: 0.721175271078 (**BELOW ≥0.999 threshold**)
- correlation_cold: 0.721175271078
- sum_ratio: not computed (temp files deleted by benchmark script)
- speedup_warm: 1.179x
- C time: 0.786s
- PyTorch warm time: 0.667s
- Cache speedup: 90176.9x

## Command

```bash
NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts
```

## Analysis

**CRITICAL REGRESSION:** Correlation 0.721175 is FAR BELOW the required ≥0.999 threshold from `plans/active/vectorization-gap-audit.md` Phase B1.

This correlation matches previous failed attempts (#3, #4, #6 in fix_plan.md), indicating the parity issue has NOT been resolved despite SOURCE-WEIGHT-001 Phase H claiming completion.

## Root Cause Hypotheses

1. SOURCE-WEIGHT-001 Phase H fixes were incomplete or reverted
2. Weighted-source normalization bug persists
3. Per-source polarization issue unresolved  
4. RNG seed mismatch between C and PyTorch implementations
5. Device/dtype configuration mismatch
6. Tricubic interpolation regression

## Blocked Protocol Followed

Per `input.md` blocked protocol:
- ✅ Artifacts stashed to `failed/`
- ✅ Test collection captured: `collect.log`
- ✅ Summary documented (this file)
- ✅ Failure logged in `docs/fix_plan.md` [VECTOR-GAPS-002] Attempts History

## Next Actions

**BLOCK Phase B2/B3** until correlation ≥0.999 restored.

Required before unblocking:
1. Git bisect between last known-good (Attempt #5: 0.999998 correlation, 2025-12-25) and current HEAD
2. Parallel trace debugging per `docs/debugging/debugging.md` §2.1
3. AT-PARALLEL validation run to identify failing tests
4. Escalate to supervisor (galph) for triage
5. Reopen SOURCE-WEIGHT-001 if weighted-source parity evidence insufficient

## Thresholds (normative)

From `plans/active/vectorization-gap-audit.md`:
- correlation_warm ≥ 0.999 (REQUIRED)
- |sum_ratio - 1| ≤ 5e-3 (REQUIRED)
