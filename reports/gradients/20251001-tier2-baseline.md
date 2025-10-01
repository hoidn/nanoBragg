# Tier 2 Gradient Coverage Baseline Audit

**Date:** 2025-10-01
**Purpose:** Document current gradcheck coverage vs testing_strategy.md §4.1 requirements
**Status:** Phase A of gradcheck-tier2-completion plan

## Spec Requirements (testing_strategy.md §4.1)

> "The following parameters (at a minimum) must pass gradcheck:
> - **Crystal:** `cell_a`, `cell_gamma`, `misset_rot_x`
> - **Detector:** `distance_mm`, `Fbeam_mm`
> - **Beam:** `lambda_A`
> - **Model:** `mosaic_spread_rad`, `fluence`"

## Current Coverage Analysis

### ✅ Implemented Tests

**Location:** `tests/test_suite.py::TestTier2GradientCorrectness`

1. **test_gradcheck_crystal_params** (lines 1616-1683)
   - ✅ `cell_a` (line 1659)
   - ✅ `cell_b` (line 1660)
   - ✅ `cell_c` (line 1661)
   - ✅ `cell_alpha` (line 1662)
   - ✅ `cell_beta` (line 1663)
   - ✅ `cell_gamma` (line 1664)

2. **test_gradcheck_detector_params** (lines 1685-1763)
   - ✅ `distance_mm` (line 1722)
   - ✅ `beam_center_f` (line 1753) — *Note: spec calls for `Fbeam_mm`, this provides equivalent coverage*

### ❌ Missing Coverage

Per §4.1 requirements, the following are NOT yet tested:

1. **Crystal misset_rot_x** — MISSING
   - Spec requirement: `misset_rot_x`
   - Current state: No gradcheck test exists
   - Related code: `src/nanobrag_torch/models/crystal.py` misset pipeline (Core Rule #12)

2. **Beam wavelength_A** — MISSING
   - Spec requirement: `lambda_A`
   - Current state: No gradcheck test exists
   - Related code: `src/nanobrag_torch/config.py::BeamConfig.wavelength_A`

3. **Beam fluence** — MISSING
   - Spec requirement: `fluence`
   - Current state: No gradcheck test exists
   - Related code: `src/nanobrag_torch/config.py::BeamConfig.fluence`

4. **Model mosaic_spread_rad** — MISSING
   - Spec requirement: `mosaic_spread_rad`
   - Current state: No gradcheck test exists
   - Related code: `src/nanobrag_torch/config.py::CrystalConfig.mosaic_spread_deg`

## Environment Configuration

**Compile-disable mechanism:**
- Current usage: `NANOBRAGG_DISABLE_COMPILE=1`
- Implementation: `src/nanobrag_torch/simulator.py` lines 577-591
- Purpose: Work around torch.compile C++ codegen bugs in backward passes
- Status: Functional per commit d45a0f3

**Note:** Some test documentation still references `NB_DISABLE_COMPILE` (inconsistent naming). Recommend standardizing on `NANOBRAGG_DISABLE_COMPILE` across all harnesses.

## Summary

**Coverage Rate:** 50% (4 of 8 spec-mandated parameters tested)

**Priority Gap Items:**
1. `misset_rot_x` (Crystal) — High priority, differentiability showcase parameter
2. `lambda_A` (Beam) — High priority, fundamental physics parameter
3. `fluence` (Beam) — Medium priority, intensity scaling parameter
4. `mosaic_spread_rad` (Model) — Lower priority, optional feature

## Next Steps

1. Capture baseline gradcheck run (Phase A task A2)
2. Implement missing tests starting with highest priority gaps
3. Ensure all new tests follow existing patterns (float64, small ROI, disable compile)
