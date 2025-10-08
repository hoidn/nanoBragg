# Phase E1 Evidence — Tricubic Vectorization CPU/GPU Parity

**Date:** 2025-10-07
**Owner:** ralph (loop execution per galph input.md)
**Plan Reference:** plans/active/vectorization.md Phase E1
**Fix Plan Item:** VECTOR-TRICUBIC-001

## Purpose

Capture CPU and CUDA parity evidence for the vectorized tricubic interpolation path to unlock Phase E progress. This validates device/dtype neutrality per `docs/development/pytorch_runtime_checklist.md` §1.4 and arch.md ADR-11.

## Reproduction Commands

### CPU Test Run
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py tests/test_at_str_002.py -v
```

### CUDA Test Run
```bash
CUDA_VISIBLE_DEVICES=0 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py tests/test_at_str_002.py -v
```

### Collection Metadata
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only tests/test_tricubic_vectorized.py tests/test_at_str_002.py -q
```

## Test Results Summary

**CPU Run:** 19 passed in 2.40s
**CUDA Run:** 19 passed in 2.39s
**Status:** ✅ All tests pass on both devices

### Test Coverage
- Vectorized tricubic gather matches scalar implementation
- Neighborhood gathering internals validated
- Out-of-bounds warning behavior (single-fire)
- Device neutrality (CPU + CUDA)
- Polynomial interpolation (polint, polin2, polin3)
- Gradient flow preservation
- Batch shape preservation
- Float32 and Float64 dtype support
- AT-STR-002 acceptance tests (tricubic enablement, OOB fallback, auto-enable)

## Artifacts

- `pytest_cpu.log` — CPU test execution log
- `pytest_cuda.log` — CUDA test execution log
- `collect.log` — Test collection metadata
- `env.json` — Environment snapshot (Python, PyTorch, CUDA versions, commit SHA)
- `sha256.txt` — SHA256 hashes of all artifacts for reproducibility

## Environment

See `env.json` for full details. Key information:
- Python 3.13.7
- PyTorch with CUDA support
- CUDA available: Yes
- Test framework: pytest 8.4.2

## Verification Gates

Per input.md Phase E1 guidance:
- ✅ CPU tests executed and logged
- ✅ CUDA tests executed and logged
- ✅ Collection metadata captured
- ✅ Environment snapshot recorded
- ✅ SHA256 hashes generated
- ✅ No skipped tests (both devices fully exercised)
- ✅ Runtime checklist compliance (device/dtype neutrality maintained)

## Next Steps

1. Phase E2: Microbenchmark sweep with `scripts/benchmarks/tricubic_baseline.py`
2. Phase E3: Parity/perf summary consolidation before Phase F planning
3. Update `docs/fix_plan.md` with this Attempt entry citing artifact paths

## References

- Plan: `plans/active/vectorization.md` Phase E tasks
- Checklist: `docs/development/pytorch_runtime_checklist.md`
- Architecture: `arch.md` ADR-11 (vectorization)
- Spec: `specs/spec-a-parallel.md:220` (tricubic acceptance tolerances)
