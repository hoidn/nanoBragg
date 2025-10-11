# Phase C Testing Strategy Notes — DETERMINISM-001

**Date:** 2025-10-11T05:29:20Z
**Phase:** C (Documentation & Remediation Blueprint)
**Purpose:** Capture determinism reproduction workflow, env vars, pytest selectors, and artifact expectations for inclusion in `docs/development/testing_strategy.md`.

---

## Overview

This document provides the authoritative workflow for validating PyTorch RNG determinism, including:
- Environment configuration (CPU-only execution, Dynamo disablement)
- Test suite selectors and runtime expectations
- Validation metrics and thresholds
- Artifact storage conventions

**Target Audience:** Engineers debugging determinism regressions, CI pipeline maintainers, contributors adding new stochastic features.

---

## 1. Determinism Test Suite

### 1.1 Authoritative Tests

| Test File | Purpose | Key Validations |
|-----------|---------|----------------|
| `tests/test_at_parallel_013.py` | Cross-platform determinism | Same-seed bitwise equality, different-seed independence, float64 precision, platform fingerprint |
| `tests/test_at_parallel_024.py` | Mosaic/misset RNG determinism | LCG bitstream parity, seed isolation, `mosaic_rotation_umat` determinism, umat↔misset round-trip |

### 1.2 Coverage Map

| Acceptance Test | Test Function(s) | Spec Reference |
|-----------------|------------------|----------------|
| AT-PARALLEL-013 | `test_pytorch_determinism_same_seed`, `test_pytorch_determinism_different_seeds`, `test_pytorch_consistency_across_runs`, `test_numerical_precision_float64`, `test_platform_fingerprint` | `specs/spec-a-parallel.md` §AT-PARALLEL-013 |
| AT-PARALLEL-024 | `test_pytorch_determinism`, `test_seed_independence`, `test_lcg_compatibility`, `test_mosaic_rotation_umat_determinism`, `test_umat2misset_round_trip` | `specs/spec-a-parallel.md` §AT-PARALLEL-024 |

**Notes:**
- `test_c_pytorch_equivalence` (both files): Skipped by default. Requires `NB_RUN_PARALLEL=1` and C binary (`NB_C_BIN`).
- `test_lcg_compatibility`: Validates bitstream parity between PyTorch `LCGRandom` and C `ran1()`. Critical for seed contract verification.

---

## 2. Environment Configuration

### 2.1 Required Environment Variables

**Determinism tests MUST set these variables before `torch` import:**

```bash
export CUDA_VISIBLE_DEVICES=''           # Force CPU-only execution
export TORCHDYNAMO_DISABLE=1             # Disable TorchDynamo graph capture
export NANOBRAGG_DISABLE_COMPILE=1       # Disable torch.compile in simulator
export KMP_DUPLICATE_LIB_OK=TRUE         # Avoid MKL library conflicts
```

**Rationale:**

1. **`CUDA_VISIBLE_DEVICES=''`**
   - **Purpose:** Hide CUDA devices, forcing CPU-only execution.
   - **Why:** GPU operations (atomics, non-deterministic reductions) can introduce numerical differences. CPU execution guarantees bitwise reproducibility.
   - **Impact:** Tests run on CPU even if GPUs are available.

2. **`TORCHDYNAMO_DISABLE=1`**
   - **Purpose:** Completely disable TorchDynamo's graph capture and optimization passes.
   - **Why:** TorchDynamo/Triton attempts CUDA device queries even when `CUDA_VISIBLE_DEVICES=''` is set. When `torch.cuda.is_available()==True` but `torch.cuda.device_count()==0`, Triton tries to index device 0 → `IndexError: list index out of range` at `torch/_dynamo/device_interface.py:218`.
   - **Impact:** Prevents graph optimization, slightly slower execution (acceptable for determinism tests).

3. **`NANOBRAGG_DISABLE_COMPILE=1`**
   - **Purpose:** Ensure `Simulator` respects Dynamo disable flag.
   - **Why:** Simulator may conditionally use `torch.compile()` for performance. This flag forces compilation to be skipped.
   - **Impact:** Pure eager-mode execution, no compilation overhead.

4. **`KMP_DUPLICATE_LIB_OK=TRUE`**
   - **Purpose:** Prevent MKL library initialization conflicts.
   - **Why:** Multiple libraries (PyTorch, NumPy) may load OpenMP runtime (`libiomp5`). Without this flag, duplicate library initialization raises error.
   - **Impact:** Suppresses MKL warnings. Standard for PyTorch test environments.

### 2.2 Implementation Note

**Test files MUST set environment variables at module level before `torch` import:**

```python
# CORRECT (tests/test_at_parallel_013.py lines 1-10):
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['TORCHDYNAMO_DISABLE'] = '1'
os.environ['NANOBRAGG_DISABLE_COMPILE'] = '1'

import torch  # ← Import AFTER env setup
import numpy as np
import pytest
```

**INCORRECT (will fail):**
```python
import torch  # ← Import BEFORE env setup (CUDA runtime already initialized)
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''  # ← Too late!
```

**Why:** PyTorch initializes CUDA runtime on import if `torch.cuda.is_available()` returns `True`. Setting `CUDA_VISIBLE_DEVICES` after import has no effect.

---

## 3. Reproduction Commands

### 3.1 Full Determinism Test Suite

```bash
# Run both AT-PARALLEL-013 and AT-PARALLEL-024:
CUDA_VISIBLE_DEVICES='' TORCHDYNAMO_DISABLE=1 NANOBRAGG_DISABLE_COMPILE=1 \
KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_013.py \
  tests/test_at_parallel_024.py
```

**Expected Results:**
- AT-PARALLEL-013: 5 passed, 1 skipped (runtime ~5-6s)
- AT-PARALLEL-024: 5 passed, 1 skipped (runtime ~4-5s)
- Total: 10 passed, 2 skipped

**Skipped Tests:**
- `test_c_pytorch_equivalence` (both files): Requires `NB_RUN_PARALLEL=1` and C binary

### 3.2 Individual Test Selectors

```bash
# Same-seed bitwise equality (critical):
CUDA_VISIBLE_DEVICES='' TORCHDYNAMO_DISABLE=1 NANOBRAGG_DISABLE_COMPILE=1 \
KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_013.py::TestATParallel013CrossPlatformConsistency::test_pytorch_determinism_same_seed

# Different-seed independence:
CUDA_VISIBLE_DEVICES='' TORCHDYNAMO_DISABLE=1 NANOBRAGG_DISABLE_COMPILE=1 \
KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_013.py::TestATParallel013CrossPlatformConsistency::test_pytorch_determinism_different_seeds

# LCG bitstream parity (seed contract validation):
CUDA_VISIBLE_DEVICES='' TORCHDYNAMO_DISABLE=1 NANOBRAGG_DISABLE_COMPILE=1 \
KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_024.py::TestATParallel024RandomMisset::test_lcg_compatibility

# mosaic_rotation_umat determinism:
CUDA_VISIBLE_DEVICES='' TORCHDYNAMO_DISABLE=1 NANOBRAGG_DISABLE_COMPILE=1 \
KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_024.py::TestATParallel024RandomMisset::test_mosaic_rotation_umat_determinism
```

### 3.3 C-PyTorch Equivalence (Optional, Requires C Binary)

```bash
# Enable live C comparison:
export NB_C_BIN=./golden_suite_generator/nanoBragg  # or ./nanoBragg
export NB_RUN_PARALLEL=1

CUDA_VISIBLE_DEVICES='' TORCHDYNAMO_DISABLE=1 NANOBRAGG_DISABLE_COMPILE=1 \
KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_013.py::TestATParallel013CrossPlatformConsistency::test_c_pytorch_equivalence \
  tests/test_at_parallel_024.py::TestATParallel024RandomMisset::test_c_pytorch_equivalence
```

**Note:** `test_c_pytorch_equivalence` in AT-PARALLEL-024 has known scaling issues (documented). Focus on PyTorch-only tests for determinism validation.

---

## 4. Validation Metrics

### 4.1 Same-Seed Runs (Bitwise Reproducibility)

**Requirement:** Identical seeds → identical output (bitwise)

| Metric | Threshold | Spec Reference |
|--------|-----------|----------------|
| `np.array_equal(img1, img2)` | ✅ True (exact match) | AT-PARALLEL-013 §Same-Seed |
| Correlation | ≥0.9999999 | AT-PARALLEL-013 §Same-Seed |
| `np.allclose(img1, img2, rtol=1e-7, atol=1e-12)` | ✅ True | AT-PARALLEL-013 §Same-Seed |
| Max absolute difference | ≤1e-10 (float64) | AT-PARALLEL-013 §Precision |

**Interpretation:**
- `np.array_equal`: Strictest check. Every pixel must match exactly (bitwise).
- Correlation: Allows for floating-point rounding differences. Threshold 0.9999999 = 7 nines.
- `np.allclose`: Numerical tolerance check. `rtol=1e-7` = 0.00001% relative error.

**Example Passing Results:**
```
img1.shape: (128, 128)
img2.shape: (128, 128)
np.array_equal(img1, img2): True
Correlation: 1.0
Max abs diff: 0.0
Mean abs diff: 0.0
```

### 4.2 Different-Seed Runs (Statistical Independence)

**Requirement:** Different seeds → statistically independent outputs

| Metric | Threshold | Spec Reference |
|--------|-----------|----------------|
| `np.array_equal(img1, img2)` | ❌ False (must differ) | AT-PARALLEL-013 §Diff-Seed |
| Correlation | ≤0.7 (low correlation) | AT-PARALLEL-013 §Diff-Seed |
| Non-zero pixels differ | ≥50% | AT-PARALLEL-013 §Diff-Seed |

**Interpretation:**
- `np.array_equal`: Must return False (images differ).
- Correlation: ≤0.7 indicates weak correlation (independent). Typical values: 0.3-0.5.
- Pixel difference: At least half of non-zero pixels should have different values.

**Example Passing Results:**
```
img1 (seed=12345): max=154.7, mean=20.2, non-zero=128/16384
img2 (seed=67890): max=142.3, mean=18.9, non-zero=131/16384
np.array_equal(img1, img2): False ✅
Correlation: 0.42 ✅ (≤0.7)
Differing pixels: 87/128 = 68% ✅ (≥50%)
```

### 4.3 Float64 Precision

**Requirement:** Tests must maintain float64 precision throughout pipeline

| Component | dtype Check | Validation |
|-----------|-------------|------------|
| Simulator input | `crystal.dtype == torch.float64` | Assert in test setup |
| Detector basis vectors | `detector.fdet_vec.dtype == torch.float64` | Assert after instantiation |
| Output image | `output.dtype == torch.float64` | Assert after `simulator.run()` |
| RNG helper | `mosaic_rotation_umat(..., dtype=torch.float64)` | Pass explicit dtype |

**Rationale:** float32 precision (7 decimal digits) is insufficient for determinism tests. float64 (15-16 digits) ensures bitwise reproducibility across platforms.

---

## 5. Artifact Storage

### 5.1 Directory Structure

```
reports/
  2026-01-test-suite-triage/
    phase_d/
      <TIMESTAMP>/
        determinism/
          phase_a/             # Evidence gathering
            summary.md
            commands.txt
            env.json
            at_parallel_013/
              pytest.log
            at_parallel_024/
              pytest.log
          phase_a_fix/         # Post-fix validation
            logs/
              summary.txt      # Key results summary
            at_parallel_013/
              pytest.log
            at_parallel_024/
              pytest.log
  determinism-callchain/       # Seed flow analysis
    phase_b3/
      <TIMESTAMP>/
        c_seed_flow.md         # C-side seed contract
        c_rng_excerpt.c
    phase_c/
      <TIMESTAMP>/
        remediation_summary.md  # This bundle
        docs_updates.md
        testing_strategy_notes.md
```

### 5.2 Key Artifacts

**Environment Snapshot (`env.json`):**
```json
{
  "python_version": "3.13.5",
  "pytorch_version": "2.7.1+cu126",
  "cuda_version": "12.6",
  "cuda_available": true,
  "cuda_device_count": 0,
  "default_dtype": "torch.float32",
  "timestamp": "2025-10-11T05:00:24Z"
}
```

**Test Results (`summary.txt`):**
```
=== AT-PARALLEL-013 Results ===
5 passed, 1 skipped
Runtime: 5.43s

=== AT-PARALLEL-024 Results ===
5 passed, 1 skipped
Runtime: 3.95s

=== Key Metrics ===
Same-seed correlation: 1.0 (≥0.9999999 ✅)
Different-seed correlation: 0.42 (≤0.7 ✅)
Bitwise equality: True ✅
```

**Commands Log (`commands.txt`):**
```bash
# Phase A evidence gathering
pytest --collect-only -q tests/ > collect_only.log 2>&1
python -c "import torch; print(torch.__version__)" > torch_version.txt
CUDA_VISIBLE_DEVICES='' pytest -v tests/test_at_parallel_013.py > at_parallel_013/pytest.log 2>&1
...
```

---

## 6. Known Limitations & Future Work

### 6.1 CUDA Determinism (Deferred)

**Current Status:** Tests force CPU-only execution via `CUDA_VISIBLE_DEVICES=''`.

**Future Work:** Re-enable CUDA execution after TorchDynamo/Triton device query bug is resolved:
1. Remove `CUDA_VISIBLE_DEVICES=''` environment guard
2. Add CUDA-specific seed initialization:
   ```python
   torch.cuda.manual_seed_all(seed)
   torch.backends.cudnn.deterministic = True
   torch.backends.cudnn.benchmark = False
   ```
3. Run full test suite with `device='cuda'`
4. Validate correlation ≥0.9999999 on GPU

**Risks:**
- Some CUDA operations (atomics, grid-stride loops) may introduce numerical differences
- CuDNN non-deterministic algorithms (e.g., convolution autotuner) require explicit disablement
- Cross-device determinism (CPU vs GPU) may require relaxed thresholds (e.g., correlation ≥0.999 instead of 0.9999999)

**Validation Plan:**
- Add `@pytest.mark.gpu` decorator for CUDA-specific tests
- Run both CPU and GPU variants in CI (if GPU runners available)
- Document any CUDA-specific tolerance adjustments in `specs/spec-a-parallel.md`

### 6.2 Noise Seed Coverage (Future Enhancement)

**Current Status:** Tests focus on `mosaic_seed` and `misset_seed`. Noise seed (`seed` parameter) is validated implicitly through full-image comparisons but not traced in detail.

**Future Work (if Poisson noise determinism regressions occur):**
1. Add explicit `test_noise_seed_determinism` to AT-PARALLEL-013
2. Apply Phase B callchain workflow to trace `seed` → `poidev` → `ran1(&seed)` propagation
3. Validate Poisson noise RNG consumption matches C implementation

**Triggers:**
- Different noise patterns for same `seed` value
- Correlation drop in `-noisefile` output comparisons
- `poidev` bitstream parity failures

### 6.3 Multi-Threaded Determinism (Not Tested)

**Current Status:** Tests run single-threaded (no `OMP_NUM_THREADS` override).

**Consideration:** C implementation uses OpenMP parallelization. If PyTorch implementation adds multi-threading (e.g., `torch.set_num_threads()`), validate:
- Thread-local RNG state isolation
- Deterministic reduction operations
- No race conditions in seed mutation

**Mitigation:** Explicitly set `torch.set_num_threads(1)` in determinism tests to force single-threaded execution.

---

## 7. Integration with CI/CD

### 7.1 Recommended CI Gates

**Fast Gate (Pre-Merge):**
```bash
# Run determinism tests on every PR:
CUDA_VISIBLE_DEVICES='' TORCHDYNAMO_DISABLE=1 NANOBRAGG_DISABLE_COMPILE=1 \
KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_013.py::TestATParallel013CrossPlatformConsistency::test_pytorch_determinism_same_seed \
  tests/test_at_parallel_024.py::TestATParallel024RandomMisset::test_pytorch_determinism

# Runtime: ~10s
# Fail if: Any test fails OR correlation <0.9999999
```

**Full Gate (Nightly or Release):**
```bash
# Run full determinism suite:
CUDA_VISIBLE_DEVICES='' TORCHDYNAMO_DISABLE=1 NANOBRAGG_DISABLE_COMPILE=1 \
KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_013.py \
  tests/test_at_parallel_024.py

# Runtime: ~10s
# Fail if: Any test fails (except skipped C-equivalence)
```

**GPU Gate (If GPU Runners Available):**
```bash
# Run with CUDA enabled (future):
TORCHDYNAMO_DISABLE=1 NANOBRAGG_DISABLE_COMPILE=1 \
KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_013.py -m gpu_smoke

# Runtime: ~15-20s
# Fail if: Any test fails OR GPU correlation <0.999
```

### 7.2 Artifact Archiving

**CI should archive:**
- Test logs (`pytest.log` for each test file)
- Environment snapshot (`env.json`)
- Results summary (`summary.txt`)

**Storage:** `reports/ci/<BUILD_ID>/determinism/` (or equivalent CI artifact storage)

**Retention:** Keep artifacts for 90 days (debugging regressions)

---

## 8. Debugging Workflow

### 8.1 When Determinism Tests Fail

**Step 1: Reproduce Locally**
```bash
# Use exact env vars from CI:
CUDA_VISIBLE_DEVICES='' TORCHDYNAMO_DISABLE=1 NANOBRAGG_DISABLE_COMPILE=1 \
KMP_DUPLICATE_LIB_OK=TRUE pytest -v -x \
  tests/test_at_parallel_013.py::TestATParallel013CrossPlatformConsistency::test_pytorch_determinism_same_seed
```

**Step 2: Check Environment**
- Verify `CUDA_VISIBLE_DEVICES=''` set before torch import
- Confirm PyTorch/CUDA versions match expected (`torch.__version__`, `torch.version.cuda`)
- Check for MKL warnings (missing `KMP_DUPLICATE_LIB_OK=TRUE`)

**Step 3: Add Tracing**
```python
# In test function, add:
print(f"Device: {device}")
print(f"dtype: {dtype}")
print(f"Crystal dtype: {crystal.dtype}")
print(f"Detector basis dtype: {detector.fdet_vec.dtype}")
print(f"mosaic_seed: {mosaic_seed}")
print(f"Image stats: min={img1.min()}, max={img1.max()}, mean={img1.mean()}")
```

**Step 4: Compare Seed State**
```python
# In src/nanobrag_torch/utils/c_random.py, add:
def mosaic_rotation_umat(...):
    rng = LCGRandom(seed)
    r1 = rng.uniform()
    print(f"[TRACE] mosaic_rotation_umat: seed={seed}, r1={r1}")  # ← Debug
    ...
```

**Step 5: Bisect Changes**
- Use `git bisect` to find first commit breaking determinism
- Focus on changes to RNG helpers, seed propagation, or device/dtype handling

### 8.2 Correlation Below Threshold (But Non-Zero)

**Symptom:** `correlation = 0.999` (below 0.9999999 threshold)

**Likely Causes:**
- Mixed float32/float64 precision (check `Crystal.dtype`, `Detector.dtype`)
- Non-deterministic operations (e.g., `torch.sort()` without `stable=True`)
- CUDA operations slipping through (verify `CUDA_VISIBLE_DEVICES=''`)

**Diagnosis:**
```python
# In test, add:
diff = np.abs(img1 - img2)
print(f"Max diff: {diff.max()}")
print(f"Mean diff: {diff.mean()}")
print(f"Non-zero diffs: {(diff > 0).sum()}/{diff.size}")

# If max diff ~1e-7: float32 precision issue
# If max diff ~1: logic error (different code paths)
```

### 8.3 Bitwise Equality Fails (But Correlation ≥0.9999999)

**Symptom:** `np.array_equal(img1, img2) == False` but `correlation = 1.0`

**Likely Causes:**
- Floating-point rounding differences (rare on CPU, common on GPU)
- Different CPU instruction sets (AVX vs SSE)

**Mitigation:**
- Relax test to use `np.allclose` instead of `np.array_equal`
- Document platform-specific differences in test comments

---

## 9. References

### 9.1 Specification
- `specs/spec-a-core.md` §5.3 — RNG determinism requirements
- `specs/spec-a-parallel.md` AT-PARALLEL-013 — Cross-platform consistency
- `specs/spec-a-parallel.md` AT-PARALLEL-024 — Random misset determinism

### 9.2 Architecture
- `arch.md` ADR-05 — Deterministic Sampling & Seeds
- `docs/architecture/c_function_reference.md` — RNG algorithm documentation (to be added)

### 9.3 Implementation
- `src/nanobrag_torch/utils/c_random.py` — LCG implementation
- `src/nanobrag_torch/models/crystal.py` — Seed propagation (line ~720)
- `tests/test_at_parallel_013.py` — Cross-platform determinism tests
- `tests/test_at_parallel_024.py` — Mosaic/misset RNG tests

### 9.4 Phase C Artifacts
- `reports/determinism-callchain/phase_c/20251011T052920Z/remediation_summary.md` — Fix summary
- `reports/determinism-callchain/phase_c/20251011T052920Z/docs_updates.md` — Documentation checklist
- `reports/determinism-callchain/phase_b3/20251011T051737Z/c_seed_flow.md` — C-side seed contract

---

## 10. Next Steps

### 10.1 Immediate (Phase C Completion)
1. ✅ Author this document (`testing_strategy_notes.md`)
2. ⬜ Integrate content into `docs/development/testing_strategy.md` §2.6 (new section)
3. ⬜ Update `docs/fix_plan.md` [DETERMINISM-001] ledger with Phase C summary

### 10.2 Short-Term (Documentation Updates)
1. ⬜ Add RNG section to `docs/architecture/c_function_reference.md` (per `docs_updates.md` §1.1)
2. ⬜ Update `src/nanobrag_torch/utils/c_random.py` docstrings (per `docs_updates.md` §2.1)
3. ⬜ Enhance `src/nanobrag_torch/models/crystal.py` docstrings (per `docs_updates.md` §2.2)

### 10.3 Long-Term (Future Enhancements)
1. ⬜ Re-enable CUDA determinism tests after Dynamo bug fix
2. ⬜ Add explicit noise seed determinism tests (if regressions occur)
3. ⬜ Add multi-threaded determinism validation (if parallelism added)

---

**Authored by:** ralph (documentation-only loop)
**Timestamp:** 2025-10-11T05:29:20Z
**Target:** `docs/development/testing_strategy.md` §2.6 (new section)
