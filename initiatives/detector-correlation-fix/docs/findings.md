# Detector Correlation Fix - Findings Log

## Summary of Findings

*This document will be updated as the investigation progresses.*

---

## Previous Knowledge (from historical debugging)

### Confirmed Fixed Issues
1. **F/S Mapping Bug** ✅ - Fixed MOSFLM convention mapping (beam_center_s → Xbeam, beam_center_f → Ybeam)
2. **+0.5 Pixel Adjustment** ✅ - Added MOSFLM pixel leading edge reference
3. **Twotheta Axis** ✅ - Corrected to [0, 0, -1] for MOSFLM
4. **Parameter Passing** ✅ - Fixed C reference runner parameter names

### Remaining Mystery
Despite these fixes and apparently correct SAMPLE pivot implementation, correlation remains at 0.040 for tilted configurations.

---

## Investigation Findings

### Priority 1.1: Parameter Verification
**Date**: TBD  
**Status**: Not Started  
**Finding**: 

### Priority 1.2: Single Pixel Trace Comparison  
**Date**: TBD  
**Status**: Not Started  
**Finding**:

### Priority 2.1: Rotation Matrix Comparison
**Date**: TBD  
**Status**: Not Started  
**Finding**:

### Priority 2.2: Twotheta Rotation Verification
**Date**: TBD  
**Status**: Not Started  
**Finding**:

### Priority 3.1: Basis Vector Conventions
**Date**: TBD  
**Status**: Not Started  
**Finding**:

### Priority 4.1: Progressive Rotation Tests
**Date**: TBD  
**Status**: Not Started  
**Finding**:

---

## Root Cause Analysis

*To be completed after investigation*

### Primary Cause
TBD

### Contributing Factors
TBD

### Why Previous Fixes Didn't Resolve
TBD

---

## Lessons Learned

*To be documented after fix is validated*

1. 
2. 
3.