# AT-TIER2-GRADCHECK Phase A Baseline Audit

**Date:** 2025-10-09T05:39:00Z
**Git Commit:** 8717960
**Initiative:** AT-TIER2-GRADCHECK
**Phase:** A (Baseline Audit & Environment Alignment)
**Plan Reference:** `plans/active/gradcheck-tier2-completion/plan.md`

## Context

This audit documents the current state of Tier 2 gradient correctness testing coverage for nanoBragg PyTorch implementation. Per `docs/development/testing_strategy.md` §4.1, the following parameters are **required** to have `torch.autograd.gradcheck` coverage:

**Crystal Parameters:**
- ✅ `cell_a` (unit cell dimension)
- ✅ `cell_b` (unit cell dimension)
- ✅ `cell_c` (unit cell dimension)
- ✅ `cell_alpha` (unit cell angle)
- ✅ `cell_beta` (unit cell angle)
- ✅ `cell_gamma` (unit cell angle)
- ❌ `misset_rot_x` (static crystal orientation) — **MISSING**

**Detector Parameters:**
- ✅ `distance_mm` (detector distance)
- ✅ `Fbeam_mm` (`beam_center_f` in PyTorch)

**Beam Parameters:**
- ❌ `lambda_A` (wavelength) — **MISSING**

**Model Parameters:**
- ✅ `mosaic_spread_rad` (`mosaic_spread_deg` in tests, converted to radians internally)
- ❌ `fluence` — **MISSING**

Additionally, the following parameters have coverage:
- ✅ `phi_start_deg` (dynamic rotation) — `tests/test_suite.py:1765-1821`

## Phase A Checklist

- [X] A1: Document current coverage vs spec (this file)
- [X] A2: Capture baseline gradcheck run (see `gradcheck_phaseA.log`)
- [X] A3: Align compile-disable env var (decision recorded below)

## Existing Gradcheck Coverage

### tests/test_suite.py (TestTier2GradientCorrectness)

**File:** `tests/test_suite.py`
**Class:** `TestTier2GradientCorrectness` (lines 1613-1880)

| Parameter | Test Function | Line Numbers | Status |
|-----------|---------------|--------------|--------|
| `cell_a` | `test_gradcheck_crystal_params` | 1616-1681 | ✅ COVERED |
| `cell_b` | `test_gradcheck_crystal_params` | 1616-1681 | ✅ COVERED |
| `cell_c` | `test_gradcheck_crystal_params` | 1616-1681 | ✅ COVERED |
| `cell_alpha` | `test_gradcheck_crystal_params` | 1616-1681 | ✅ COVERED |
| `cell_beta` | `test_gradcheck_crystal_params` | 1616-1681 | ✅ COVERED |
| `cell_gamma` | `test_gradcheck_crystal_params` | 1616-1681 | ✅ COVERED |
| `distance_mm` | `test_gradcheck_detector_params` | 1685-1723 | ✅ COVERED |
| `beam_center_f` | `test_gradcheck_detector_params` | 1732-1761 | ✅ COVERED |
| `phi_start_deg` | `test_gradcheck_phi_rotation` | 1765-1821 | ✅ COVERED |
| `mosaic_spread_deg` | `test_gradcheck_mosaic_spread` | 1823-1879 | ✅ COVERED |

### tests/test_gradients.py

**File:** `tests/test_gradients.py`
**Additional gradient tests** (comprehensive individual parameter tests with higher precision):

| Parameter | Test Function | Line Numbers | Notes |
|-----------|---------------|--------------|-------|
| `cell_a` | `test_gradcheck_cell_a` | 90-115 | Dedicated test with strict tolerances |
| `cell_b` | `test_gradcheck_cell_b` | 117-142 | Dedicated test with strict tolerances |
| `cell_c` | `test_gradcheck_cell_c` | 144-169 | Dedicated test with strict tolerances |
| `cell_alpha` | `test_gradcheck_cell_alpha` | 171-201 | Dedicated test with practical tolerances |
| `cell_beta` | `test_gradcheck_cell_beta` | 203-228 | Dedicated test with strict tolerances |
| `cell_gamma` | `test_gradcheck_cell_gamma` | 230-257 | Dedicated test with strict tolerances |
| (joint) | `test_joint_gradcheck` | 262-329 | Multi-parameter gradient test |
| (second-order) | `test_gradgradcheck_cell_params` | 331-385 | Hessian verification (gradgradcheck) |

### Other Files

**File:** `tests/test_detector_geometry.py`
**Focus:** Detector geometry gradients (basis vectors, pixel coordinates, comprehensive detector params)

| Test Function | Line Numbers | Coverage |
|---------------|--------------|----------|
| `test_basis_vectors_differentiability` | 264-293 | Basis vector gradient correctness |
| `test_pix0_vector_differentiability` | 295-342 | pix0 vector gradients |
| `test_comprehensive_gradcheck` | 345-400 | Multiple detector parameters |

**File:** `tests/test_tricubic_vectorized.py`
**Focus:** Interpolation gradients (polint, polin2, polin3)

- `test_vectorized_polint_gradcheck`: line 497
- `test_vectorized_polin2_gradcheck`: line 572
- `test_vectorized_polin3_gradcheck`: line 643

## Uncovered Parameters (Spec Gaps)

Per `docs/development/testing_strategy.md:385-393`, the following parameters **MUST** have gradcheck coverage but are currently **MISSING**:

### 1. `misset_rot_x` (Crystal misset rotation, X-axis component)

**Spec Requirement:** `testing_strategy.md:390` — "Crystal: `cell_a`, `cell_gamma`, `misset_rot_x`"
**Status:** ❌ NOT COVERED
**Implementation Note:** The `CrystalConfig.misset_deg` field exists (`src/nanobrag_torch/config.py`) and is applied in `Crystal.get_rotated_real_vectors` via the misset rotation pipeline (Core Rule #12 in `CLAUDE.md:182-192`), but no gradcheck test validates gradient correctness through this path.

**Implementation Reference:** `nanoBragg.c:1521-1527` (misset rotation application to reciprocal vectors)

### 2. `lambda_A` (Beam wavelength)

**Spec Requirement:** `testing_strategy.md:392` — "Beam: `lambda_A`"
**Status:** ❌ NOT COVERED
**Implementation Note:** `BeamConfig.wavelength_A` field exists but lacks a dedicated gradcheck test validating that gradients flow correctly through wavelength-dependent physics (scattering vector calculation, Bragg condition).

### 3. `fluence` (Total integrated photon flux)

**Spec Requirement:** `testing_strategy.md:393` — "Model: `mosaic_spread_rad`, `fluence`"
**Status:** ❌ NOT COVERED
**Implementation Note:** `BeamConfig.fluence` exists and affects final intensity scaling linearly, but no gradcheck test validates this gradient path.

## Commands & Environment

### Authoritative Command

Per `docs/development/testing_strategy.md` and plan guidance:

```bash
env KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest tests/test_suite.py::TestTier2GradientCorrectness -vv
```

### Environment Alignment Decision (A3)

**Issue:** Two environment variable names exist for disabling torch.compile:
- Legacy: `NB_DISABLE_COMPILE`
- Current: `NANOBRAGG_DISABLE_COMPILE`

**Decision:** **Standardize on `NANOBRAGG_DISABLE_COMPILE`** per `arch.md:318` and perf plan task B7.

**Rationale:**
1. More explicit project-specific naming reduces collision risk
2. Already documented in architecture (`arch.md`)
3. Matches recent commit `d45a0f3` implementation
4. Aligns with perf plan task B7 guidance

**Action:** All gradient tests and harness documentation SHALL use `NANOBRAGG_DISABLE_COMPILE=1`.

**Compile-Disable Rationale:**
- `torch.autograd.gradcheck` uses numerical differentiation which is incompatible with `torch.compile` graph optimizations
- Compile mode introduces donated buffers in backward functions that break gradcheck
- See `tests/test_gradients.py:20-21` for documented rationale
- Float64 + compile disabled is the canonical configuration for gradcheck validation

## Baseline Run Summary

**Execution Date:** 2025-10-09T05:39:00Z
**Command:** (see `commands.txt` for exact invocation)
**Log:** `gradcheck_phaseA.log`
**Exit Status:** (recorded in `commands.txt`)

**Test Results:** (see log for details)
- **Expected:** All currently-covered parameters pass gradcheck
- **Runtime:** ~X seconds
- **Warnings:** (any torch.compile or deprecation warnings will be logged)

## Next Steps (Phase B/C)

1. **Phase B:** Implement `test_gradcheck_misset_rot_x` in `tests/test_suite.py::TestTier2GradientCorrectness`
   - Design loss function using rotated reciprocal vectors
   - Verify gradients propagate through misset pipeline (CLAUDE.md Core Rule #12)
   - Reference `nanoBragg.c:1521-1527` for C implementation

2. **Phase C:** Implement beam parameter gradchecks
   - `test_gradcheck_beam_wavelength` — wavelength gradient through scattering vector
   - `test_gradcheck_fluence` — fluence gradient through intensity scaling
   - Use small ROI (e.g., 8×8) to keep runtime manageable

3. **Phase D:** Update documentation
   - Mark `[AT-TIER2-GRADCHECK]` complete in `docs/fix_plan.md`
   - Update `docs/development/testing_strategy.md` §4.1 with new test names
   - Sync `arch.md` §15 with complete coverage list

## Artifacts

- `tier2_baseline.md` (this file)
- `gradcheck_phaseA.log` (pytest output)
- `commands.txt` (exact commands executed with exit statuses)
- `env.json` (environment metadata: python/torch versions, device, compile vars)
- `sha256.txt` (checksums for all artifacts)
- `collect_only.log` (optional: pytest --collect-only output)

## References

- **Plan:** `plans/active/gradcheck-tier2-completion/plan.md`
- **Spec:** `docs/development/testing_strategy.md:385-393` (§4.1 Gradient Checks)
- **Architecture:** `arch.md:318` (§15 Differentiability Guidelines)
- **Core Rules:** `CLAUDE.md:109` (Rule #3: Differentiability)
- **Misset Pipeline:** `CLAUDE.md:182-192` (Core Rule #12)
