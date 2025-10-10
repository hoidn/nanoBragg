# Phase A Summary: Determinism Evidence Capture

**Initiative**: [DETERMINISM-001] PyTorch RNG determinism
**Date**: 2025-10-10T17:10:10Z
**Branch**: feature/spec-based-2
**Commit**: a79a14f605cc3f564cf5cef651a2a8b266455fae

## Environment

- **Python**: 3.13.5 (Anaconda)
- **PyTorch**: 2.7.1+cu126
- **NumPy**: 2.3.1
- **CUDA**: 12.6 (available, 1 device)
- **Default dtype**: torch.float32
- **cudnn.deterministic**: False
- **cudnn.benchmark**: False

## Test Collection

`KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q`

**Result**: ✅ SUCCESS - All 410 tests collected successfully

## AT-PARALLEL-013 Results

**Command**: `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py --maxfail=0 --durations=10`

### Summary
- **Total**: 6 tests
- **PASSED**: 1 (test_platform_fingerprint)
- **FAILED**: 4
- **SKIPPED**: 1 (test_c_pytorch_equivalence - requires NB_RUN_PARALLEL=1)

### Failures

#### 1. `test_pytorch_determinism_same_seed`
- **Error**: `RuntimeError: Float did not match Double`
- **Location**: `src/nanobrag_torch/models/detector.py:767` in `get_pixel_coords()`
- **Context**: `torch.allclose(self.fdet_vec, cached_f, atol=1e-15)` comparison
- **Root Cause**: dtype mismatch between float32 (self.fdet_vec) and float64 (cached_f) in cache validation
- **Note**: Test explicitly creates `dtype=torch.float64` objects, but Detector basis vectors default to float32

#### 2. `test_pytorch_determinism_different_seeds`
- **Error**: Identical to #1 (`RuntimeError: Float did not match Double`)
- **Location**: Same (`detector.py:767`)

#### 3. `test_pytorch_consistency_across_runs`
- **Error**: Identical to #1 (`RuntimeError: Float did not match Double`)
- **Location**: Same (`detector.py:767`)

#### 4. `test_numerical_precision_float64`
- **Error**: `InternalTorchDynamoError` during torch.compile() of `sincg` function
- **Location**: PyTorch Dynamo compilation stack trace
- **Context**: Complex torch._dynamo failure with message ending in "Exception: RuntimeError: Unsupported dtype passed to Tensor constructor!"
- **Note**: Different failure mode - this is a compile-time error, not runtime dtype mismatch

### Common Pattern (Failures #1-3)

The primary blocker is **not a seed determinism issue** but a **dtype neutrality violation**:

```python
# Test creates float64 objects:
detector = Detector(detector_config, dtype=torch.float64)

# But Detector basis vectors (fdet_vec, sdet_vec, odet_vec) are float32
# When cache validation runs torch.allclose(float32_tensor, float64_tensor), it fails
```

This prevents tests from even reaching the seed/determinism logic.

## AT-PARALLEL-024 Results

**Command**: `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_024.py --maxfail=0 --durations=10`

### Summary
- **Total**: 6 tests
- **PASSED**: 2 (test_lcg_compatibility, test_umat2misset_round_trip)
- **FAILED**: 3
- **SKIPPED**: 1 (test_c_pytorch_equivalence - requires NB_RUN_PARALLEL=1)

### Failures

#### 1. `test_pytorch_determinism`
- **Error**: `RuntimeError: Float did not match Double`
- **Location**: `src/nanobrag_torch/models/detector.py:767` in `get_pixel_coords()`
- **Context**: Identical to AT-PARALLEL-013 failures
- **Root Cause**: Same dtype mismatch issue

#### 2. `test_seed_independence`
- **Error**: Identical to #1 (`RuntimeError: Float did not match Double`)

#### 3. `test_mosaic_rotation_umat_determinism`
- **Error**: Identical to #1 (`RuntimeError: Float did not match Double`)

### Common Pattern

All three failures share the same **dtype neutrality violation** as AT-PARALLEL-013. None of the failures are related to seed determinism itself.

## Key Findings

### 1. Primary Blocker: Dtype Neutrality Violation

**The determinism tests cannot execute because of a dtype mismatch bug introduced by incomplete device/dtype neutrality in `Detector.get_pixel_coords()`.**

- Tests explicitly request `dtype=torch.float64` for high-precision determinism validation
- `Detector` basis vectors (`fdet_vec`, `sdet_vec`, `odet_vec`) remain float32 (default)
- Cache validation in `get_pixel_coords()` attempts `torch.allclose(float32, float64)` → RuntimeError

**This is a violation of Core Implementation Rule #16** (PyTorch Device & Dtype Neutrality) from CLAUDE.md.

### 2. Secondary Issue: Dynamo Compilation Failure

`test_numerical_precision_float64` hits a torch.compile() failure in the `sincg` function. This is a separate issue unrelated to determinism logic.

### 3. Actual Determinism Status: Unknown

**We cannot yet assess seed determinism behavior** because the tests fail before reaching seed-dependent code paths. The dtype mismatch blocks instantiation of the `Simulator` object.

### 4. Passing Tests (Baseline Evidence)

Two tests in AT-PARALLEL-024 passed:
- `test_lcg_compatibility`: C-compatible LCG implementation works correctly
- `test_umat2misset_round_trip`: Misset matrix conversions are bidirectional

These provide confidence that the **underlying RNG and misset math are sound**, once the dtype issue is resolved.

## Artifacts

All logs stored under:
```
reports/2026-01-test-suite-triage/phase_d/20251010T171010Z/determinism/phase_a/
├── at_parallel_013/
│   └── pytest.log       # Full test output (3 identical dtype errors + 1 dynamo error)
├── at_parallel_024/
│   └── pytest.log       # Full test output (3 identical dtype errors)
├── commands.txt         # Reproduction commands
├── env.json            # Environment snapshot
└── summary.md          # This file
```

## Recommended Next Steps

### Immediate (Blocking)
1. **Fix dtype neutrality in `Detector`**: Ensure basis vectors respect the `dtype` parameter
   - `fdet_vec`, `sdet_vec`, `odet_vec` must use `self.dtype`, not default float32
   - Cache validation must compare tensors of matching dtypes
   - Verify all tensor allocations in `Detector.__init__()` honor `dtype` parameter

2. **Investigate Dynamo compilation failure** in `sincg` (separate issue)

### Phase B (After Fix)
Once dtype issues are resolved, proceed with Phase B (callchain analysis) to:
- Trace seed propagation from CLI → `CrystalConfig` → `Crystal` → random misset generation
- Compare against C-code `nanoBragg.c` seed handling
- Generate parallel traces for any remaining determinism drift

## Conclusion

**This Phase A evidence run reveals that the determinism failures are currently masked by a device/dtype neutrality bug, not seed-related logic errors.**

The good news: The RNG primitives (`test_lcg_compatibility`) and misset math (`test_umat2misset_round_trip`) already work correctly. Once the dtype issue is fixed, we expect most determinism tests to pass or expose much narrower seed-handling gaps.

**Status**: Phase A complete. Artifacts captured. Blocker identified.
**Next**: Update `docs/fix_plan.md` with Attempt #1 entry referencing this summary.
