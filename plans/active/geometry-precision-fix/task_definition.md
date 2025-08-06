# Task: Investigate and Fix Numerical Precision Errors in Crystal Geometry Engine

**Status:** CRITICAL  
**Priority:** Immediate follow-up to triclinic fix  
**Created:** 2025-01-29

## Problem Statement

The recent "unit cell initiative" successfully implemented the C-code's crystallographic conventions, raising the triclinic_P1 test correlation from 0.005 to 0.957. However, to make the `test_metric_duality` and `test_rotation_invariance` unit tests pass, their tolerances had to be loosened to an unacceptable `rtol=1e-2` (1% error).

Fundamental geometric identities should hold to machine precision (e.g., 1e-12). A 1% error indicates a subtle but significant bug remains in the `compute_cell_tensors` method in `src/nanobrag_torch/models/crystal.py`.

## Technical Context

### Current Symptoms
- `test_metric_duality`: Tests that `a* · a = 1`, `a* · b = 0`, etc. Currently requires 1% tolerance
- `test_rotation_invariance`: Tests that lattice vectors maintain proper relationships under rotation. Currently requires 1% tolerance
- These are fundamental crystallographic identities that should be exact to machine precision

### Hypothesis
The C-code convention implementation may have introduced:
- Accumulated numerical errors in the complex trigonometric calculations
- Loss of precision in the cross-product/volume calculations
- Possible mixed float32/float64 operations
- Order-of-operations differences from the C implementation

## Investigation Plan

### Phase 1: Numerical Analysis
1. Create instrumented version of `compute_cell_tensors` that logs intermediate values
2. Compare PyTorch calculations step-by-step with C-code using double precision
3. Identify exact point where precision loss occurs
4. Check for any implicit float32 conversions

### Phase 2: Root Cause Identification
1. Test with simplified cases (cubic, tetragonal) to isolate angle-dependent errors
2. Verify all torch operations maintain float64 precision
3. Compare order of operations with C-code
4. Check for numerically unstable formulas (e.g., subtraction of nearly equal values)

### Phase 3: Implementation Fix
1. Implement numerically stable version of problematic calculations
2. Ensure all operations maintain full float64 precision
3. Consider using torch.float128 if needed for intermediate calculations
4. Validate against C-code with extended precision

## Files to Investigate

1. **Primary Target:**
   - `src/nanobrag_torch/models/crystal.py`: `compute_cell_tensors()` method

2. **Test Files:**
   - `tests/test_crystal_geometry.py`: `test_metric_duality()` and `test_rotation_invariance()`

3. **Reference Implementation:**
   - `nanoBragg.c`: Lines containing the canonical orientation calculations
   - Debug traces from `nanoBragg_trace.c` if available

## Acceptance Criteria

1. **Precision Fix:**
   - Root cause of numerical discrepancy identified and documented
   - Geometry calculations achieve machine precision (errors < 1e-12)

2. **Test Suite:**
   - `rtol` and `atol` for `test_metric_duality` restored to 1e-12
   - `rtol` and `atol` for `test_rotation_invariance` restored to 1e-12
   - All geometry tests pass with strict tolerances

3. **Integration:**
   - Triclinic_P1 correlation remains ≥0.957 (ideally improves to >0.990)
   - Simple cubic test maintains high correlation
   - No regression in other tests

4. **Documentation:**
   - Document the specific numerical issue found
   - Add comments explaining any numerical stability techniques used
   - Update CLAUDE.md if new implementation rules discovered

## Success Metrics

- All geometric identities hold to 1e-12 relative tolerance
- No performance degradation from precision improvements
- Clear documentation of the fix for future reference
- Potential improvement in triclinic_P1 correlation to >0.990

## Risk Assessment

- **Low Risk:** Fix only affects internal precision, not algorithmic approach
- **Medium Risk:** May expose other latent numerical issues in downstream calculations
- **Mitigation:** Comprehensive testing at each step, maintain debug traces

## Notes

This task directly addresses the reviewer's concern about "treating the symptom rather than the cause." The loosened tolerances indicate a real numerical issue that must be resolved for the geometry engine to be truly correct.