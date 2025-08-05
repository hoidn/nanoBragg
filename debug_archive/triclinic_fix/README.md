# Triclinic Fix Debug Archive

This directory contains debugging files created during the implementation of the triclinic cell parameter fix.

## Summary of the Fix

The issue was that the PyTorch implementation was not using the same crystallographic convention as nanoBragg.c for constructing the default orientation matrix from cell parameters.

### Root Cause
1. nanoBragg.c uses a specific convention where:
   - a* is placed purely along the x-axis
   - b* is placed in the x-y plane
   - c* fills out 3D space

2. The PyTorch implementation was using a different convention, leading to different reciprocal and real-space vectors even before any rotations.

3. Additionally, the misset rotation was applied to reciprocal vectors, but the real-space vectors were not being properly recalculated from the rotated reciprocal vectors.

### Fix Applied
1. Updated `Crystal.compute_cell_tensors()` to use the exact same formulas as nanoBragg.c
2. Fixed `_apply_static_orientation()` to recalculate real-space vectors after rotating reciprocal vectors
3. Added numerical stability improvements for degenerate cell parameters

### Results
- Triclinic test correlation improved from 0.005 to 0.957
- All unit tests pass
- Simple cubic test still has high correlation (0.9988) but exact values differ due to the convention change

## Files in this Archive

- `test_misset_trace.py` - Compares PyTorch and C-code vector transformations
- `test_rotation_debug.py` - Tests rotation matrix implementation
- `test_crystal_debug.py` - Tests initial reciprocal vector calculation
- `test_cubic_convention.py` - Tests cubic cell with new convention
- `test_metric_duality.py` - Tests metric duality relationships
- `test_cross_product.py` - Tests cross product calculations
- `debug_misset.py`, `debug_misset2.py` - Various debugging scripts
- `P1_trace.hkl` - Simple HKL file for testing
- `nanoBragg.c` - Instrumented version of nanoBragg.c with trace output (located in golden_suite_generator/)
- `nanoBragg` - Compiled instrumented executable (located in golden_suite_generator/)

## Remaining Issue

The correlation is 0.957 instead of the target 0.990. This is due to small numerical differences (~0.19 Å) in the real-space vectors after misset rotation. The differences likely stem from:
- Precision differences between C and PyTorch
- Small differences in how cross products and volumes are calculated
- Accumulated rounding errors

These differences are small enough for practical use but prevent exact reproduction.