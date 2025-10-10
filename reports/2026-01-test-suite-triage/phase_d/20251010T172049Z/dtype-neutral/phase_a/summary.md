# DTYPE-NEUTRAL-001 Phase A Summary: Evidence Capture

**Timestamp:** 2025-10-10T172049Z
**Initiative:** DTYPE-NEUTRAL-001 — enforce dtype neutrality across detector geometry and caching
**Phase:** A — Failure Reproduction & Evidence Capture
**Status:** ✓ COMPLETE

---

## Executive Summary

Successfully reproduced dtype mismatch failures in AT-PARALLEL-013 and AT-PARALLEL-024 determinism tests. Root cause confirmed: `Detector.get_pixel_coords()` performs dtype-incompatible tensor comparisons when cached basis vectors (float32) are compared against current basis vectors (float64).

**Error Location:** `src/nanobrag_torch/models/detector.py:767`
**Error Message:** `RuntimeError: Float did not match Double`

---

## A1: Environment Snapshot ✓

**File:** `env.json`

- Python: 3.13.5
- PyTorch: 2.7.1+cu126
- NumPy: 2.3.1
- CUDA Available: True
- Default dtype: `torch.float32`
- Default device: `cpu`
- Test collection: **PASSED** (588 tests collected)

**Reference:** `docs/development/testing_strategy.md` §1.4

---

## A2: AT-PARALLEL-013 Reproduction ✓

**Test:** `tests/test_at_parallel_013.py::TestATParallel013CrossPlatformConsistency::test_pytorch_determinism_same_seed`

**Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_013.py::TestATParallel013CrossPlatformConsistency::test_pytorch_determinism_same_seed \
  --maxfail=0 --durations=10
```

**Result:** FAILED

**Failure Stack Trace:**
```python
tests/test_at_parallel_013.py:146: in test_pytorch_determinism_same_seed
    result1 = run_simulation_deterministic(seed=42)
tests/test_at_parallel_013.py:131: in run_simulation_deterministic
    simulator = Simulator(crystal, detector, crystal_config, beam_config)
src/nanobrag_torch/simulator.py:569: in __init__
    self._cached_pixel_coords_meters = self.detector.get_pixel_coords().to(device=self.device, dtype=self.dtype)
src/nanobrag_torch/models/detector.py:767: in get_pixel_coords
    torch.allclose(self.fdet_vec, cached_f, atol=1e-15)
.../torch/utils/_device.py:104: in __torch_function__
    return func(*args, **kwargs)
E       RuntimeError: Float did not match Double
```

**Artifact:** `at_parallel_013/pytest.log`

---

## A3: AT-PARALLEL-024 Reproduction ✓

**Test:** `tests/test_at_parallel_024.py::TestAT_PARALLEL_024::test_pytorch_determinism`

**Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_024.py::TestAT_PARALLEL_024::test_pytorch_determinism \
  --maxfail=0 --durations=10
```

**Result:** FAILED

**Failure Stack Trace:**
```python
tests/test_at_parallel_024.py:116: in test_pytorch_determinism
    sim1 = Simulator(crystal1, detector1, crystal_config1, beam_config)
src/nanobrag_torch/simulator.py:569: in __init__
    self._cached_pixel_coords_meters = self.detector.get_pixel_coords().to(device=self.device, dtype=self.dtype)
src/nanobrag_torch/models/detector.py:767: in get_pixel_coords
    torch.allclose(self.fdet_vec, cached_f, atol=1e-15)
E       RuntimeError: Float did not match Double
```

**Artifact:** `at_parallel_024/pytest.log`

**Observation:** Identical failure signature at same line in both tests.

---

## A4: Minimal Reproducer ✓

**Script:** `trace/minimal_reproducer.py`

**Key Finding:**
- Creating a new `Detector` instance with `dtype=torch.float64` succeeds
- But `Simulator` initialization fails when calling `detector.get_pixel_coords()`
- This suggests the cache is shared across detector instances or populated during initialization

**Reproducer Output Highlights:**
```
Step 3: Create new Detector instance with float64 dtype
  detector.dtype = torch.float64
  detector.fdet_vec.dtype = torch.float64

Step 4: Attempt to call get_pixel_coords() (this will fail)
  SUCCESS: coords.dtype = torch.float64
```

**Simulator Integration Test:**
```
Creating Crystal and Detector with float64 dtype...
  crystal.dtype = torch.float64
  detector.dtype = torch.float64

Attempting to create Simulator (triggers detector.get_pixel_coords())...
  FAILURE: RuntimeError: Float did not match Double
```

**Artifact:** `trace/reproducer_output.log`

---

## A5: Root Cause Analysis

### Code Location

**File:** `src/nanobrag_torch/models/detector.py:767`

**Problematic Code:**
```python
# Lines 760-774
if hasattr(self, "_cached_basis_vectors") and hasattr(self, "_cached_pix0_vector"):
    # Check if basis vectors have changed
    # Move cached vectors to current device for comparison
    cached_f = self._cached_basis_vectors[0].to(self.device)  # ❌ NO dtype coercion
    cached_s = self._cached_basis_vectors[1].to(self.device)  # ❌ NO dtype coercion
    cached_o = self._cached_basis_vectors[2].to(self.device)  # ❌ NO dtype coercion

    if not (
        torch.allclose(self.fdet_vec, cached_f, atol=1e-15)  # ❌ Compares float32 vs float64
        and torch.allclose(self.sdet_vec, cached_s, atol=1e-15)
        and torch.allclose(self.odet_vec, cached_o, atol=1e-15)
    ):
```

### The Problem

1. **Cached tensors** are stored during first `get_pixel_coords()` call (lines 795-800 in the full file)
2. Cached tensors are **cloned with their original dtype** (e.g., float32 if detector was created with default dtype)
3. When a test creates a **new detector with float64**, the cached tensors remain float32
4. Lines 762-764 move cached tensors to the **current device** but **DO NOT** convert dtype
5. `torch.allclose()` at line 767 attempts to compare **float32 cached** vs **float64 current** tensors
6. PyTorch raises `RuntimeError: Float did not match Double`

### Tensors Involved

**Cached (float32):**
- `self._cached_basis_vectors[0/1/2]` — fdet/sdet/odet basis vectors from initial creation
- `self._cached_pix0_vector` — detector origin position

**Current (float64):**
- `self.fdet_vec`, `self.sdet_vec`, `self.odet_vec` — current basis vectors
- `self.pix0_vector` — current detector origin

### Why Tests Fail

**AT-PARALLEL-013** and **AT-PARALLEL-024** both:
1. Create `Crystal` and `Detector` with `dtype=torch.float64` for numerical precision
2. Create `Simulator`, which calls `detector.get_pixel_coords()` (simulator.py:569)
3. Cache comparison fails because cached vectors are float32 (from class-level default?)

**Note:** The exact mechanism of how the cache becomes populated with float32 tensors when the detector is created with float64 requires Phase B analysis, but the symptom is clear.

---

## Phase A Exit Criteria ✓

- [x] **A1:** Environment snapshot captured in `env.json`
- [x] **A2:** AT-PARALLEL-013 failure reproduced with full stack trace
- [x] **A3:** AT-PARALLEL-024 failure reproduced with identical error
- [x] **A4:** Minimal reproducer created and executed
- [x] **A5:** Summary with failure signatures and root cause hypothesis

---

## Artifacts

All artifacts stored under: `reports/2026-01-test-suite-triage/phase_d/20251010T172049Z/dtype-neutral/phase_a/`

```
.
├── env.json                              # Environment snapshot
├── collect.log                            # pytest collection output
├── at_parallel_013/
│   └── pytest.log                         # AT-PARALLEL-013 test output
├── at_parallel_024/
│   └── pytest.log                         # AT-PARALLEL-024 test output
├── trace/
│   ├── minimal_reproducer.py              # Standalone reproduction script
│   └── reproducer_output.log              # Script execution output
└── summary.md                             # This file
```

---

## Next Steps (Phase B)

1. **Static audit:** Trace how `_cached_basis_vectors` are initialized and stored
2. **Identify all torch.allclose() calls** in `Detector` that lack dtype coercion
3. **Survey other components** (Crystal, Simulator) for similar dtype coupling
4. **Design fix strategy:** Add `dtype=self.dtype` to all `.to()` calls in cache comparisons

**Blocking Dependency:** [DETERMINISM-001] cannot proceed until dtype neutrality is restored.

---

## References

- `plans/active/dtype-neutral.md` — Phase A tasks
- `docs/development/testing_strategy.md` §1.4 — Device & Dtype Discipline
- `docs/architecture/detector.md` §7-8 — Detector caching invariants
- `src/nanobrag_torch/models/detector.py:760-781` — Cache comparison logic
- Prior evidence: `reports/2026-01-test-suite-triage/phase_d/20251010T171010Z/determinism/phase_a/summary.md` (Attempt #1)

---

**Evidence Capture Complete. Ready for Phase B Root-Cause Analysis.**
