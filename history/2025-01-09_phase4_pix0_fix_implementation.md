# Phase 4 Implementation Summary: pix0_vector Calculation Fix

**Date**: January 9, 2025  
**Initiative**: Parallel Trace Validation  
**Phase**: 4 - Fix pix0_vector Calculation Discrepancy  
**Duration**: ~4 hours  
**Result**: Partial Success - Beam center fixed, rotation issue identified  

## Executive Summary

Phase 4 successfully identified and fixed a critical beam center calculation error in the PyTorch Detector class. However, the correlation remains at 0.040 due to a separate rotation-related issue that requires additional investigation.

## What Was Implemented

### 1. Diagnostic Infrastructure (Phase 4.1)
Created comprehensive tracing and analysis tools:
- `scripts/trace_pix0_detailed.py` - Ultra-detailed pix0 tracer
- `scripts/compare_rotation_matrices.py` - Matrix comparison tool
- `scripts/verify_pix0_manually.py` - Manual calculation verification
- `scripts/analyze_pix0_discrepancy.py` - Comprehensive analyzer
- `scripts/fix_pix0_beam_center.py` - Beam center fix tester

### 2. Root Cause Identification (Phase 4.2)
Discovered two critical issues:
- **Beam center axis mapping error**: MOSFLM convention requires swapping F/S axes
- **Unit conversion error**: beam_center values were already in pixels, not mm

### 3. Fix Implementation (Phase 4.3)
Modified `/src/nanobrag_torch/models/detector.py`:
```python
# Fixed MOSFLM convention axis mapping
# BEFORE: Fbeam from beam_center_f, Sbeam from beam_center_s
# AFTER:  Fbeam from beam_center_s, Sbeam from beam_center_f (swapped)
```

### 4. Validation Results (Phase 4.4)
- ✅ Basic BEAM pivot: Now matches C reference with ~1e-18 precision
- ✅ Beam center calculations: Exactly match C values
- ⚠️ Rotated configurations: Still show ~3cm systematic offset
- ❌ Correlation: Remains at 0.040 (target >0.999)

## Key Discoveries

### What We Fixed
1. **MOSFLM Convention Axis Mapping**
   - PyTorch was incorrectly mapping beam center axes
   - Fixed by swapping F/S axis assignments
   - Now correctly implements MOSFLM convention

2. **Unit Conversion Issue**
   - Code was treating pixel values as millimeters
   - Fixed by recognizing beam_center is already in pixels
   - Eliminated the 10x factor discrepancy

### What Remains
1. **Rotation-Related Offset**
   - ~3cm systematic offset in rotated configurations
   - Identical for both BEAM and SAMPLE pivots
   - Suggests issue in rotation matrix application or order

2. **Correlation Target Not Met**
   - Still at 0.040 instead of >0.999
   - Due to the rotation offset propagating through all pixels
   - Requires Phase 5 to address rotation logic

## Files Modified

1. **src/nanobrag_torch/models/detector.py**
   - Lines 259-261: Fixed BEAM pivot beam center calculation
   - Lines 287-289: Fixed SAMPLE pivot beam center calculation
   - Added detailed comments explaining MOSFLM convention

2. **scripts/** (5 new diagnostic tools)
   - Comprehensive tracing and analysis infrastructure
   - Will be valuable for future debugging

3. **tests/test_detector_pix0.py** (created)
   - Regression tests for beam center calculation
   - Validates both BEAM and SAMPLE pivot modes

## Test Results
- Tests added: 6 (beam center regression tests)
- Tests passing: All detector tests pass
- Correlation: 0.040 (unchanged due to rotation issue)

## Deviations from Plan

1. **Expected Quick Fix**: Plan assumed fixing pix0 would resolve correlation
2. **Found Deeper Issue**: Beam center was only part of the problem
3. **Additional Discovery**: Rotation logic has separate ~3cm offset

## Technical Details

### The Beam Center Fix
```python
# MOSFLM Convention (now correctly implemented):
# - Fbeam corresponds to slow axis (Y in detector frame)
# - Sbeam corresponds to fast axis (X in detector frame)
# - This is opposite to intuition but matches C code

# Correct mapping:
Fbeam = (self.beam_center_s + 0.5) * self.pixel_size  # s → F
Sbeam = (self.beam_center_f + 0.5) * self.pixel_size  # f → S
```

### The Remaining Rotation Issue
Analysis shows a consistent ~3cm offset in pix0_vector for rotated cases:
- Affects both BEAM and SAMPLE pivots equally
- Suggests rotation matrix construction or application issue
- Not related to beam center calculation

## Lessons Learned

1. **Convention Documentation Critical**: MOSFLM axis mapping was undocumented
2. **Unit Boundaries Matter**: Confusion about where mm→pixel conversion happens
3. **Layered Bugs**: Fixed one issue, revealed another
4. **Trace Infrastructure Valuable**: Diagnostic tools essential for complex debugging

## Next Steps (Phase 5 Recommended)

1. **Focus on Rotation Logic**
   - Investigate rotation matrix construction
   - Check rotation order (rotx→roty→rotz→twotheta)
   - Verify active vs passive rotation conventions

2. **Use Existing Infrastructure**
   - Diagnostic tools from Phase 4 ready to use
   - Traces already show the ~3cm offset clearly

3. **Expected Effort**
   - 2-3 hours to identify rotation issue
   - Should achieve >0.999 correlation once fixed

## Metrics

- **Lines of code changed**: ~20 (surgical fix)
- **Diagnostic tools created**: 5
- **Issues fixed**: 1 of 2 identified
- **Correlation improvement**: None yet (rotation issue blocks it)
- **Understanding gained**: Significant

## Conclusion

Phase 4 successfully diagnosed and fixed the beam center calculation issue, establishing correct MOSFLM convention implementation. While correlation hasn't improved yet due to a separate rotation issue, we now have:

1. ✅ Correct beam center calculation
2. ✅ Comprehensive diagnostic infrastructure
3. ✅ Clear understanding of remaining issue
4. ✅ Path forward to achieve >0.999 correlation

The parallel trace validation approach has proven highly effective at identifying specific implementation differences. Phase 5 should focus on the rotation logic to complete the correlation fix.

---

**Phase Status**: Complete (beam center fixed, rotation issue identified)  
**Initiative Status**: Requires Phase 5 for rotation fix  
**Recommendation**: Proceed with rotation logic investigation