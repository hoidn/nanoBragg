# Session Review: Detector Geometry Correlation Debug

**Date**: January 9, 2025  
**Issue**: PyTorch vs C reference correlation = 0.040 (target > 0.999) for tilted detector configurations  
**Session Goal**: Implement parallel trace debugging to identify divergence point  

## What We Accomplished

### 1. Problem Analysis & Context Gathering
- Analyzed `fixplan.md` which outlined the systematic approach to fix the detector geometry issue
- Used `geminictx.py` to identify 10 most relevant files for the detector geometry problem
- Extracted historical context showing the SAMPLE pivot implementation was already fixed in previous sessions

### 2. Key Discovery from Historical Analysis
From `docs/development/detector_rotation_debugging_session.md`, we confirmed the root cause was previously identified:
- **C Implementation**: Calculates pix0_vector BEFORE rotations, then rotates it
- **PyTorch Implementation**: Was calculating pix0_vector AFTER rotations (now fixed)
- The fix was already implemented in `src/nanobrag_torch/models/detector.py` lines 270-325

### 3. Trace Infrastructure Implementation
Created comprehensive debugging scripts:

#### `scripts/trace_pixel_512_512.py`
- Traces pixel (512, 512) through entire nanoBragg pipeline
- Outputs in format matching C traces: `TRACE_PY:variable_name=value`
- Covers: detector geometry, scattering vectors, Miller indices, structure factors
- Fixed Crystal attribute errors (uses `crystal.a`, not `crystal.a_vec`)

#### `scripts/debug_pix0_calculation.py`  
- Manual step-by-step validation of SAMPLE pivot pix0_vector calculation
- Compares manual calculation vs Detector class implementation
- Identified numerical discrepancy that needs investigation

#### Updated `scripts/verify_detector_geometry.py`
- Modified to use correct tilted parameters (rotx=5°, roty=3°, rotz=2°, twotheta=20°)
- Confirms correlation issue persists at ~0.040

### 4. Current Status
- ✅ SAMPLE pivot logic is structurally correct (calculates before rotations)
- ❌ Correlation remains at 0.040 (not improved)
- 🔍 Found discrepancy in pix0_vector calculation that needs investigation

## Key Finding: Numerical Discrepancy

Despite the SAMPLE pivot fix being implemented correctly, we discovered a numerical discrepancy:

```python
# Manual calculation of pix0_vector:
[0.0965, -0.0255, -0.0099] meters

# Detector class result:
[0.1098, 0.0227, -0.0518] meters
```

The Detector class result appears more consistent with expected values, suggesting either:
1. The manual calculation has an error
2. There's a subtle difference in rotation implementation

## Proposed Next Steps

### Phase 1: Deep Debug Detector Class (2-3 hours)
1. **Instrument Detector._calculate_pix0_vector()**
   - Add detailed logging at each rotation step
   - Verify rotation matrix construction
   - Check rotation order (should be: rotx → roty → rotz → twotheta)

2. **Create minimal reproduction case**
   ```python
   # Test just the pix0 calculation in isolation
   detector = Detector(config)
   # Compare each intermediate step with manual calculation
   ```

3. **Verify rotation conventions**
   - Confirm axis definitions match C code
   - Check if rotations are active vs passive
   - Validate Rodrigues formula implementation

### Phase 2: C-Code Instrumentation (1-2 hours)
1. **Add matching trace statements to nanoBragg.c**
   ```c
   printf("TRACE_C:pix0_before_rotation=%.15g %.15g %.15g\n", ...);
   printf("TRACE_C:rotation_matrix=%.15g %.15g %.15g ...\n", ...);
   printf("TRACE_C:pix0_after_rotation=%.15g %.15g %.15g\n", ...);
   ```

2. **Generate C trace for pixel 512,512**
   ```bash
   ./nanoBragg -trace_pixel 512 512 [params] 2>&1 | grep TRACE_C > c_trace.log
   ```

3. **Direct numerical comparison**
   - Use `scripts/compare_traces.py` to find exact divergence point
   - Should pinpoint the specific calculation step that differs

### Phase 3: Fix & Validate (1 hour)
1. **Implement fix based on findings**
   - Most likely in rotation matrix construction or application order
   - May involve axis convention or sign differences

2. **Comprehensive validation**
   ```bash
   # Run full verification suite
   python scripts/verify_detector_geometry.py
   # Should achieve >0.999 correlation for all test cases
   ```

3. **Regression testing**
   - Ensure baseline (no tilt) still works
   - Test various rotation combinations
   - Verify gradient flow remains intact

## Risk Assessment

### High Confidence Areas
- SAMPLE pivot logic structure is correct
- Trace infrastructure is comprehensive and working
- Issue is isolated to numerical calculation, not algorithmic difference

### Areas Needing Attention
- Exact rotation implementation details
- Potential floating-point precision issues
- Possible convention differences (left-handed vs right-handed, etc.)

## Success Metrics
- Primary: Achieve >0.999 correlation for tilted detector configuration
- Secondary: Maintain >0.999 correlation for baseline configuration
- Bonus: Document all convention differences for future reference

## Estimated Time to Resolution
- **Optimistic**: 4-5 hours (if issue is simple rotation order/sign)
- **Realistic**: 6-8 hours (including C instrumentation and validation)
- **Pessimistic**: 10-12 hours (if multiple subtle issues compound)

## Recommendations

1. **Start with Phase 1** - Deep debug the Detector class since we already have the infrastructure
2. **Use systematic approach** - Don't guess; trace every calculation step
3. **Document findings** - Update `docs/architecture/detector.md` with any convention clarifications
4. **Consider pair debugging** - Complex rotation math benefits from multiple eyes

## Files Created/Modified This Session

### Created
- `/scripts/trace_pixel_512_512.py` - Main trace script
- `/scripts/debug_pix0_calculation.py` - Manual validation script
- `/py_trace_pixel_512.log` - Python trace output

### Modified  
- `/scripts/verify_detector_geometry.py` - Updated with correct parameters

### Next Session Should Start With
1. Run `python scripts/debug_pix0_calculation.py` to see the discrepancy
2. Examine `src/nanobrag_torch/models/detector.py` lines 299-325 (SAMPLE pivot implementation)
3. Add detailed logging to trace the exact rotation sequence

---

**Session Duration**: ~3 hours  
**Progress**: Established comprehensive debugging framework, identified numerical discrepancy  
**Blocker**: Need to resolve pix0_vector calculation difference to achieve target correlation