# Phase M3 Evidence Bundle — Remaining Clusters

**Date:** 2025-10-12
**STAMP:** 20251012T014618Z
**Baseline:** Phase M2 STAMP 20251011T193829Z (13 failures across 4 clusters)
**Status:** Evidence gathering complete

## Executive Summary

**Net active failures after validation:** 1 implementation bug (C15 zero intensity) + 10 infrastructure items (C2 gradients with documented workaround).

**Key findings:**
- **C8 (MOSFLM offset):** ✅ **RESOLVED** — Test now passing, prior implementation successful
- **C15 (mixed units):** ❌ **ACTIVE** — Zero intensity bug persists, requires parallel trace debugging
- **C16 (orthogonality):** ✅ **RESOLVED** — Tolerance fix (Attempt #43) successful
- **C2 (gradients):** ℹ️ **DOCUMENTED** — Workaround in place (`NANOBRAGG_DISABLE_COMPILE=1`), no action needed

---

## Cluster C8: MOSFLM Beam Center Offset

**Status:** ✅ **RESOLVED**
**Test:** `tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation`
**Runtime:** 1.94s
**Result:** **PASSED**

### Context
Prior failure due to missing MOSFLM +0.5 pixel offset in beam center calculation (spec-a-core.md §72).

### Validation
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation
```

**Output:**
```
============================== 1 passed in 1.94s ===============================
```

### Resolution Evidence
- Implementation completed in fix_plan.md Attempts #42-57
- BeamCenterSource enum added to handle explicit vs auto beam centers
- Conditional +0.5 pixel offset applied only for MOSFLM convention
- 5 new tests added covering MOSFLM, XDS, explicit override cases
- Validation: Phase D (STAMP 20251011T223549Z) shows 554/13/119, C8 marked ✅ RESOLVED

### Artifacts
- `c8_mosflm.log` — full pytest output
- Implementation summary: fix_plan.md Attempts #42-57
- Design doc: `reports/.../20251011T214422Z/mosflm_offset/design.md` (23KB)

---

## Cluster C15: Mixed Units Zero Intensity

**Status:** ❌ **ACTIVE BUG**
**Test:** `tests/test_at_parallel_015.py::TestATParallel015MixedUnits::test_mixed_units_comprehensive`
**Runtime:** 3.77s
**Result:** **FAILED**

### Failure Details
```python
AssertionError: Zero maximum intensity
assert tensor(0.) > 0
```

**Configuration:**
- Crystal: triclinic (75.5×82.3×91.7 Å, angles 87.5°×92.3°×95.8°), N=(3,3,3), default_F=100
- Detector: XDS convention, 128×128 pixels, distance=150.5mm, pixel=0.172mm
- Rotations: rotx=5°, roty=3°, rotz=2°, twotheta=10°
- Beam: λ=1.54Å (Cu K-alpha), fluence=1e23, polarization=0.95, dmin=2.0Å

### Symptom
Simulator returns all-zero 128×128 intensity tensor despite valid configuration and non-zero structure factors.

### Hypothesis Space (Ranked by Likelihood)

**H1: dmin Filtering Too Aggressive (HIGHEST)**
- dmin=2.0Å cutoff may exclude all reflections for this geometry/wavelength combination
- Test: Rerun with `dmin=None` (disable filtering)
- Expected: Non-zero intensity if culling is the root cause
- Diagnostic: Check stol values for representative pixels

**H2: Unit Conversion Error in Mixed mm/Å/degrees**
- Complex interaction between mm detector params, Å wavelength/cell, degree rotations
- Test: Minimal reproducer with cubic cell, no rotations, standard units
- Expected: Isolate whether triclinic+mixed-units interaction is causal

**H3: XDS Convention + Rotations Interaction**
- XDS uses +Z beam direction (vs MOSFLM +X), rotx/roty/rotz may not commute correctly
- Test: Rerun with MOSFLM convention, identical rotations
- Expected: Non-zero if XDS-specific geometry issue

**H4: Scattering Vector Calculation Edge Case**
- Triclinic cell + large rotations + dmin may create degenerate q vectors
- Test: Parallel trace comparison (C vs PyTorch) per debugging.md SOP
- Expected: First divergence shows where physics breaks down

**H5: Fluence Too Low**
- fluence=1e23 vs typical 1e24 (10× lower)
- Test: Rerun with fluence=1e24
- Expected: Unlikely root cause (would scale intensity, not zero it)

**H6: N_cells=(3,3,3) Triclinic Edge Case**
- Small crystal size + triclinic shape factors
- Test: Increase to N=(5,5,5) or (10,10,10)
- Expected: Rules out crystal-size-dependent sampling issue

### Reproduction Commands

**Targeted test:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_015.py::TestATParallel015MixedUnits::test_mixed_units_comprehensive
```

**Module-level:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_015.py
```

**Minimal reproducer (recommended first diagnostic):**
Create standalone script testing H1 (dmin hypothesis):
```python
import torch
from nanobrag_torch.models import Crystal, Detector
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, DetectorConvention

# Same config but disable dmin
crystal_config = CrystalConfig(cell_a=75.5, cell_b=82.3, cell_c=91.7,
                                cell_alpha=87.5, cell_beta=92.3, cell_gamma=95.8,
                                default_F=100.0, N_cells=(3,3,3), phi_start_deg=0.0,
                                osc_range_deg=1.0, phi_steps=1)
detector_config = DetectorConfig(distance_mm=150.5, pixel_size_mm=0.172, spixels=128, fpixels=128,
                                  detector_convention=DetectorConvention.XDS,
                                  detector_rotx_deg=5.0, detector_roty_deg=3.0,
                                  detector_rotz_deg=2.0, detector_twotheta_deg=10.0)
beam_config = BeamConfig(wavelength_A=1.54, fluence=1e23, polarization_factor=0.95,
                          dmin=None)  # <-- DISABLE dmin

det = Detector(detector_config)
crystal = Crystal(crystal_config)
sim = Simulator(detector=det, crystal=crystal, beam_config=beam_config)
intensity = sim.run(oversample=1)
print(f"Max intensity (dmin=None): {intensity.max().item()}")
```

### Next Actions

**Sprint 1.3: Parallel Trace Debugging (4-6h)**
1. Execute H1 minimal reproducer (dmin probe) — 30 min
2. If H1 fails, generate parallel traces (C vs PyTorch) per debugging.md — 2-3h
3. Identify first divergence in scattering vector, stol, h/k/l, F_cell, or culling logic
4. Implement fix targeting root cause
5. Revalidate with targeted + module tests

**Exit Criteria:**
- Targeted test passes with non-zero intensity
- No regressions in module-level suite
- Root cause documented in fix_plan Attempts History

### Artifacts
- `c15_mixed_units.log` — full pytest failure output with AssertionError details
- Test source: `tests/test_at_parallel_015.py:226-274`
- Configuration: lines 230-261 (crystal/detector/beam configs)

---

## Cluster C16: Detector Orthogonality Tolerance

**Status:** ✅ **RESOLVED**
**Test:** `tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_large_detector_tilts`
**Runtime:** 3.76s
**Result:** **PASSED**

### Context
Prior failure due to float32 precision limit in large rotation compositions (rotx=50°, roty=45°, rotz=40°, total 135°). Measured orthogonality error 1.49e-08 exceeded strict 1e-10 tolerance.

### Validation
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_large_detector_tilts
```

**Output:**
```
============================== 1 passed in 3.76s ===============================
```

### Resolution Evidence
- fix_plan.md Attempt #43 (Phase M3 Sprint 1.2)
- Relaxed orthogonality tolerance from 1e-10 to 1e-7 (conservative for float32)
- Relaxed normalization tolerance from 1e-10 to 1e-7
- Added inline documentation explaining float32 precision for large rotations
- Test file: `tests/test_at_parallel_017.py:95-100` (orthogonality), lines 103-106 (normalization)

### Physical Analysis
- Measured error ~1.5e-8 represents ~0.00001° misalignment (physically negligible)
- Within float32 machine epsilon for 3-rotation matrix composition
- Matches C-code float precision behavior

### Artifacts
- `c16_orthogonality.log` — full pytest output
- Implementation: Attempt #43 STAMP 20251012T013323Z
- Code changes: `tests/test_at_parallel_017.py` (tolerance adjustments + docstring)

---

## Cluster C2: Gradient Compile Guard (Workaround Documented)

**Status:** ℹ️ **DOCUMENTED WORKAROUND** — No action needed
**Failure count:** 10 gradient tests
**Resolution:** Phase M2 Attempts #29-30

### Context
`torch.compile` creates donated buffers that break `torch.autograd.gradcheck` numerical gradient computation.

### Documented Workaround
Environment variable `NANOBRAGG_DISABLE_COMPILE=1` must be set before importing torch in gradient tests.

**Implementation locations:**
- `tests/test_gradients.py:23` — Sets environment flag before torch import
- `src/nanobrag_torch/simulator.py:617` — Checks flag and skips torch.compile when set

**Canonical command:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  pytest -v tests/test_gradients.py -k "gradcheck" --tb=short
```

**Validation:** Phase M2 Attempt #29 (STAMP 20251011T172830Z)
- 8/8 gradcheck tests passed
- Runtime: 491.54s (8m 11s)
- Environment: Python 3.13.5, PyTorch 2.7.1+cu126, CPU-only with float64 precision

**Documentation:**
- `arch.md` §15 (Gradient Test Execution Requirement)
- `testing_strategy.md` §4.1 (Execution Requirements)
- `pytorch_runtime_checklist.md` §3 (compile guard bullet)

---

## Phase M3 Recommendations

### Sprint 1.2: C16 Orthogonality (COMPLETE ✅)
- **Status:** RESOLVED in Attempt #43
- **Time:** 30 minutes (quick win)
- **Impact:** -1 failure (13→12 remaining)

### Sprint 1.3: C15 Mixed Units (HIGH PRIORITY, 4-6h)
- **Status:** ACTIVE BUG — Zero intensity issue
- **Recommended approach:** H1 dmin probe (30min) → parallel trace debugging (2-3h) → fix + validation (1-2h)
- **Impact:** -1 failure (12→11 remaining) if resolved
- **Blocking dependencies:** None
- **Exit criteria:** Test passes with non-zero intensity, no module regressions

### Post-Sprint 1.3: Test Suite Health
If C15 resolved, remaining state:
- **11 total failures** (from Phase M0 baseline of 46)
- **-76% reduction** overall
- **Pass rate:** ~82% (561/687 passing)

**Deferred clusters:**
- C2 gradient infrastructure: Workaround documented, no code fix needed (10 tests)
- C17/C18: Lower-priority edge cases, defer to Sprint 2+ per remediation_tracker.md

---

## Commands Reference

```bash
# Targeted C8 validation (PASSING)
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation

# Targeted C15 validation (FAILING)
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_015.py::TestATParallel015MixedUnits::test_mixed_units_comprehensive

# Targeted C16 validation (PASSING)
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_large_detector_tilts

# H1 minimal reproducer (dmin hypothesis)
# Create standalone script as shown in C15 section above
```

---

## Environment
- **Python:** 3.13.5
- **PyTorch:** 2.7.1+cu126
- **CUDA:** 12.6 (disabled via CUDA_VISIBLE_DEVICES=-1)
- **Platform:** linux 6.14.0-29-generic
- **Execution mode:** CPU-only, float32 default

---

## Artifacts
- `redundancy/note.md` — Stale input.md detection (7th consecutive)
- `remaining_clusters/c8_mosflm.log` — C8 validation (PASSING)
- `remaining_clusters/c15_mixed_units.log` — C15 validation (FAILING)
- `remaining_clusters/c16_orthogonality.log` — C16 validation (PASSING)
- `remaining_clusters/summary.md` — This document

---

**Next:** Update fix_plan.md Next Actions item #2 as complete, proceed to item #3 (update plan status) OR delegate Sprint 1.3 (C15 debugging) per supervisor priority.
