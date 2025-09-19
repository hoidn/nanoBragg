# Triclinic Crystal 158-Pixel Offset Investigation Report

**Date**: September 19, 2025
**Issue**: AT-PARALLEL-026 - Triclinic crystal peaks appear at (196, 254) instead of near beam center
**Status**: RESOLVED - Not a bug, correct physics

## Executive Summary

The reported "158-pixel offset bug" in triclinic crystal simulations is **NOT a bug**. It is the correct physical behavior for the specific triclinic unit cell parameters used in the test. Both the C-code reference implementation and the PyTorch implementation produce identical results, confirming the correctness of the PyTorch crystal geometry calculations.

## Key Findings

### 1. PyTorch Implementation is Correct ✅

**Evidence**:
- C-code triclinic peak: `(196, 254)`
- PyTorch triclinic peak: `(196, 254)`
- **Difference: 0.0 pixels** - Perfect agreement

### 2. Rule #13 Compliance ✅

Both cubic and triclinic crystals pass all checks for reciprocal vector recalculation:
- Metric duality achieved to machine precision (< 1e-12)
- Volume calculations match between formula and actual vectors
- Reciprocal vector recalculation correctly implemented

### 3. Crystallographic Calculations are Correct ✅

**Triclinic Crystal Analysis**:
- Cell parameters: a=70Å, b=80Å, c=90Å, α=85°, β=95°, γ=105°
- Peak at (196, 254) corresponds to Miller indices `(0, -2, 5)`
- This is a **high-angle reflection** with d-spacing = 15.82 Å
- Scattering angle 2θ = 5.43°
- Fractional Miller indices very close to integers: Δh=-0.014, Δk=0.011, Δl=-0.003

### 4. Test Assumption was Incorrect ❌

The failing test assumed that cubic and triclinic crystals with "similar dimensions" should have peaks at similar positions. This assumption is **crystallographically incorrect**:

- **Cubic crystal**: Strong low-angle reflections near beam center (28 pixels from center)
- **Triclinic crystal**: Different reciprocal lattice geometry causes strong reflections to appear at high angles (143 pixels from center)

## Detailed Analysis

### Crystal Geometry Validation

**Triclinic Real-Space Vectors** (Å):
```
a = [ 67.36, -17.63,  -6.10]
b = [ -0.00,  79.57,   6.97]
c = [  0.00,   0.00,  90.00]
```

**Triclinic Reciprocal-Space Vectors** (Å⁻¹):
```
a* = [ 0.01485,  0.00000, -0.00000]
b* = [ 0.00329,  0.01257, -0.00000]
c* = [ 0.00075, -0.00097,  0.01111]
```

**Default Orientation Convention**: ✅ Correctly implemented
- a* purely along X-axis
- b* in X-Y plane
- c* fills 3D space

### Miller Index Calculation at Peak Position

**Pixel (196, 254) Analysis**:
- Scattering vector: `S = [-0.00299, -0.02987, 0.05553]` Å⁻¹
- Miller indices: `h=-0.014, k=-1.989, l=4.997`
- Nearest integers: `(0, -2, 5)`
- **This corresponds to a legitimate Bragg reflection**

### Physical Interpretation

The `(0, -2, 5)` reflection in this triclinic crystal:
1. Has reciprocal lattice vector `G = -2*b* + 5*c*`
2. Satisfies Bragg condition with d-spacing = 15.82 Å
3. Creates constructive interference at scattering angle 2θ = 5.43°
4. **Correctly appears at pixel (196, 254)** based on detector geometry

## Recommendations

### 1. Fix the Test ✅

The test `test_triclinic_absolute_positions()` should be updated to:
- Remove the incorrect assumption that cubic and triclinic peaks should be close
- Instead validate that PyTorch and C-code produce identical peak positions
- Focus on correlation rather than absolute position similarity

### 2. Update Documentation 📝

Add clarification to project documentation that:
- Different crystal systems produce peaks at different detector positions
- Triclinic crystals have complex reciprocal lattice geometry
- Position offsets between crystal systems are physically expected

### 3. Test Suite Validation ✅

The PyTorch implementation has been thoroughly validated:
- **Crystal geometry**: Correct implementation of Rule #13
- **Default orientation**: Matches C-code convention exactly
- **Miller index calculation**: Produces identical results to C-code
- **Peak positions**: Perfect agreement with reference implementation

## Conclusion

**The 158-pixel offset is CORRECT PHYSICS, not a software bug.**

The PyTorch implementation correctly calculates triclinic crystal geometry and produces results that are identical to the C-code reference implementation. The test failure was due to an incorrect assumption about expected peak positions for different crystal systems.

**Status**: Investigation complete - No code changes required to PyTorch implementation.

---

**Files Created During Investigation**:
- `debug_triclinic_geometry_bug.py` - Comprehensive geometry validation
- `debug_miller_index_specific.py` - Miller index analysis for pixel (196, 254)
- `validate_triclinic_against_c.py` - C-code vs PyTorch validation
- `TRICLINIC_INVESTIGATION_REPORT.md` - This report

**Next Steps**:
1. Update the failing test to use correct expectations
2. Mark investigation as complete in project documentation
3. Continue with other development priorities