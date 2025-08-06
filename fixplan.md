# Detector Geometry Fix Plan

**Date:** January 2025  
**Current Status:** Partial Success - Baseline working, tilted configuration has issues  
**Next Steps:** Debug rotation + beam center interaction

## Current Situation

### What's Working ✅
1. **Unit System Fix Applied**: Detector now correctly uses meters internally instead of Angstroms
   - Distance: 100mm → 0.1m (not 1e9 Å)
   - Pixel size: 0.1mm → 0.0001m (not 1e6 Å)
   - This fixed the catastrophic triclinic regression (correlation went from 0.004 back to 0.957)

2. **Baseline Configuration**: 0.999 correlation with C reference
   - Simple detector geometry without rotations works perfectly
   - Confirms our fundamental implementation is correct
   - Cell parameters now properly passed to C reference

3. **Documentation Updated**: 
   - Detector.md now documents the hybrid unit system exception
   - C code overview documents non-standard conventions
   - Debugging guide created to capture lessons learned

### What's Not Working ❌
1. **Tilted Detector Configuration**: -0.02 correlation (essentially random)
   - Combination of rotations + beam center offset produces wrong results
   - PyTorch and C patterns are shifted differently
   - Suggests issue with BEAM pivot mode calculations

2. **Visual Comparison Shows**:
   - Both PyTorch and C produce Bragg spots (not noise)
   - Spots are at different locations when rotations are applied
   - The rotation transformations aren't matching the C implementation

## Root Cause Analysis

### Confirmed Issues
1. **Unit System Mismatch** (FIXED)
   - Detector was using Angstroms instead of meters
   - Caused 9 orders of magnitude error in positions
   - Fixed by updating Detector class to use meters internally

2. **Missing Cell Parameters** (FIXED)
   - C reference runner wasn't passing cell parameters
   - C code was using default values
   - Fixed by adding `-cell` parameters to command

### Suspected Issues
1. **Rotation Order or Convention**
   - C code might apply rotations in different order
   - Or use different rotation matrix conventions
   - Need to trace through C code rotation implementation

2. **Beam Center in BEAM Pivot Mode**
   - When `detector_pivot=BEAM`, rotations happen around beam spot
   - Beam center offset (51.2 → 61.2mm) might be handled differently
   - C formula: `pix0_vector = -Fbeam*fdet - Sbeam*sdet + distance*beam_vec`

3. **Two-Theta Axis Convention**
   - MOSFLM convention uses non-intuitive `[0, 0, -1]` axis
   - Might be implemented incorrectly in rotation calculations

## Next Steps

### 1. Immediate: Trace Rotation Implementation
```bash
# Generate detailed traces for rotation calculations
./nanoBragg -trace_pixel 512 512 -detector_rotx 5 -detector_twotheta 15 ...
KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py --rotations
```

Compare step-by-step:
- Initial basis vectors
- After each rotation (rotx, roty, rotz, twotheta)
- Final pix0_vector calculation
- Beam center transformation

### 2. Create Minimal Test Case
```python
# Test just rotations without physics
# Compare detector basis vectors directly
config = DetectorConfig(
    detector_rotx_deg=5.0,
    detector_twotheta_deg=15.0,
    detector_pivot=DetectorPivot.BEAM,
)
```

### 3. Debug Rotation Order
Check if C code applies rotations as:
- Option A: `R_total = R_twotheta @ R_rotz @ R_roty @ R_rotx` (current PyTorch)
- Option B: `R_total = R_rotx @ R_roty @ R_rotz @ R_twotheta` (reversed)
- Option C: Some other combination

### 4. Verify Two-Theta Implementation
```python
# Check two-theta rotation axis for MOSFLM
# C code: twotheta_axis = [0, 0, -1] for MOSFLM
# Verify our rotation_matrix_axis function
```

### 5. Test Pivot Modes Separately
- Test SAMPLE pivot with rotations (should be simpler)
- Test BEAM pivot without beam center offset
- Test BEAM pivot with offset but single rotation
- Build up complexity gradually

## Proposed Fix Strategy

### Phase 1: Rotation Debugging (1-2 hours)
1. Create focused rotation test comparing basis vectors
2. Add print statements to C code for rotation matrices
3. Compare rotation matrices element by element
4. Fix any discrepancies in rotation order or convention

### Phase 2: Pivot Mode Verification (1-2 hours)
1. Verify BEAM pivot formula implementation
2. Check how beam center affects rotated detector
3. Compare pix0_vector calculations in detail
4. Fix pivot mode calculations if needed

### Phase 3: Integration Testing (1 hour)
1. Run full test suite
2. Verify triclinic still passes (regression test)
3. Check tilted detector configuration
4. Update visual verification plots

### Phase 4: Documentation (30 min)
1. Document the correct rotation conventions
2. Add rotation order to detector.md
3. Create test case for future regression prevention
4. Update debugging guide with rotation debugging tips

## Success Criteria

1. **Tilted detector correlation > 0.99** with C reference
2. **All existing tests still pass** (no regressions)
3. **Clear documentation** of rotation conventions
4. **Regression test** added for rotation + beam center case

## Risk Mitigation

1. **Keep changes minimal** - only fix rotation calculations
2. **Preserve working baseline** - don't break what works
3. **Add comprehensive tests** - prevent future regressions
4. **Document everything** - rotation conventions are tricky

## Fallback Plan

If rotation debugging proves too complex:
1. Mark tilted configuration as "known limitation"
2. Focus on configurations without rotations for now
3. Plan deeper C code analysis for later phase
4. Consider contacting original nanoBragg authors

## Conclusion

We've made significant progress fixing the unit system issue, which resolved the catastrophic triclinic failure. The remaining issue with rotated detectors is more subtle but should be solvable with systematic debugging. The key is to trace through the rotation calculations step-by-step and find where PyTorch and C implementations diverge.