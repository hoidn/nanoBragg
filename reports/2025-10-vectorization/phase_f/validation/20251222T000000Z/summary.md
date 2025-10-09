# Phase F2 Validation Summary

**Date:** 2025-12-22
**Mode:** Perf/Validation
**Focus:** VECTOR-TRICUBIC-001 Phase F2 - Absorption vectorization validation

## Overview

This validation confirms that the detector absorption vectorization implementation (`_apply_detector_absorption`) is functioning correctly on CPU and documents CUDA device placement issues for follow-up.

## Changes Made

### 1. Docstring Update (CLAUDE Rule #11)

Updated `src/nanobrag_torch/simulator.py:1707-1746` to include the exact C-code reference from `nanoBragg.c` lines 2975-2983:

```c
/* now calculate detector thickness effects */
if(capture_fraction == 0.0 || oversample_thick)
{
    /* inverse of effective thickness increase */
    parallax = dot_product(diffracted,odet_vector);
    /* fraction of incoming photons absorbed by this detector layer */
    capture_fraction = exp(-thick_tic*detector_thickstep*detector_mu/parallax)
                      -exp(-(thick_tic+1)*detector_thickstep*detector_mu/parallax);
}
```

Added vectorization notes documenting the batched implementation approach.

### 2. Test Parametrization

Extended `tests/test_at_abs_001.py` to parametrize all tests over:
- `device`: cpu and cuda (when available)
- `oversample_thick`: False and True (for relevant tests)

This expanded the test suite from 5 tests to 16 parametrized test cases.

## Test Results

### CPU Tests ✅ (All Passing)

```
tests/test_at_abs_001.py::TestAT_ABS_001::test_absorption_disabled_when_zero[cpu] PASSED
tests/test_at_abs_001.py::TestAT_ABS_001::test_capture_fraction_calculation[False-cpu] PASSED
tests/test_at_abs_001.py::TestAT_ABS_001::test_capture_fraction_calculation[True-cpu] PASSED
tests/test_at_abs_001.py::TestAT_ABS_001::test_last_value_vs_accumulation_semantics[cpu] PASSED
tests/test_at_abs_001.py::TestAT_ABS_001::test_parallax_dependence[False-cpu] PASSED
tests/test_at_abs_001.py::TestAT_ABS_001::test_parallax_dependence[True-cpu] PASSED
tests/test_at_abs_001.py::TestAT_ABS_001::test_absorption_with_tilted_detector[False-cpu] PASSED
tests/test_at_abs_001.py::TestAT_ABS_001::test_absorption_with_tilted_detector[True-cpu] PASSED
```

**Result:** 8/8 CPU tests passing

### CUDA Tests ⚠️ (Device Placement Issue)

```
tests/test_at_abs_001.py::TestAT_ABS_001::test_absorption_disabled_when_zero[cuda] FAILED
tests/test_at_abs_001.py::TestAT_ABS_001::test_capture_fraction_calculation[False-cuda] PASSED
tests/test_at_abs_001.py::TestAT_ABS_001::test_capture_fraction_calculation[True-cuda] PASSED
... [6 more CUDA failures]
```

**Root Cause:** `RuntimeError: Expected all tensors to be on the same device, but found at least two devices, cuda:0 and cpu!`

The `incident_beam_direction` tensor is created on CPU in the `Simulator` initialization but not moved to the specified device. This is a pre-existing issue in the simulator's device handling, not specific to the absorption implementation.

**Impact:** The absorption vectorization code itself is device-neutral (uses `.device` property from input tensors), but the simulator needs fixes to move all configuration tensors to the target device during initialization.

## Validation Evidence

### Shape Probes (From Test Execution)

The vectorized absorption implementation correctly handles:

1. **Parallax calculation**: shape (S, F) from detector normal (3,) and observation dirs (S, F, 3)
2. **Capture fractions (oversample_thick=True)**: shape (thicksteps, S, F) via broadcasting
3. **Final intensity**: shape (S, F) after reduction over thickness layers

### Physics Correctness

All CPU tests validate:
- ✅ Zero thickness disables absorption
- ✅ Capture fractions follow `exp(−t·Δz·μ/ρ) − exp(−(t+1)·Δz·μ/ρ)` formula
- ✅ Fractions sum to `1 − exp(−thickness·μ/ρ)` (within 1e-6 tolerance)
- ✅ Last-value vs accumulation semantics differ correctly
- ✅ Parallax dependence observed (off-axis vs on-axis pixels)
- ✅ Tilted detector geometry handled correctly

## Next Actions (Phase F3 Blocked)

### Critical Blocker
The CUDA device placement issue must be resolved before Phase F3 benchmarking can proceed. This is tracked separately from absorption work.

**Recommended approach:**
1. Add device transfer in `Simulator.__init__` for all beam/crystal/detector configuration tensors
2. Re-run the parametrized absorption tests to confirm CUDA parity
3. Proceed with Phase F3 CPU+CUDA benchmarks once tests pass

### Phase F3 Prerequisites
- CPU-only benchmarks can proceed immediately
- CUDA benchmarks blocked until device placement fixed
- Recommend fixing device issue in next loop before F3

## Artifacts

- Test output log: `test_output.log`
- Parametrized test file: `tests/test_at_abs_001.py` (16 test cases)
- Updated simulator: `src/nanobrag_torch/simulator.py` (docstring lines 1715-1746)

## Compliance

- ✅ CLAUDE Rule #11: C-code reference added to docstring
- ✅ Device parametrization: CPU + CUDA tests created
- ✅ Oversample_thick parametrization: False/True coverage
- ✅ Vectorization preserved: No Python loops introduced
- ⚠️ Device neutrality: Pre-existing simulator issue discovered

