# Phase 4: Fix pix0_vector Calculation Discrepancy

**Initiative**: Parallel Trace Validation  
**Previous Phase**: Phase 3 fixed pivot mode configuration  
**Remaining Issue**: pix0_vector calculations differ between C and Python  
**Current Correlation**: 0.040 (target >0.999)  
**Estimated Time**: 2-4 hours  

## Problem Statement

After fixing the pivot mode configuration, both C and Python now correctly use SAMPLE pivot when twotheta≠0. However, they calculate different pix0_vector values:

- **C Result**: `[0.09523, 0.05882, -0.05170]` meters
- **Python Result**: `[0.1098, 0.0227, -0.0518]` meters

This ~15% difference in pix0_vector propagates through all pixel calculations, causing the 0.040 correlation.

## Root Cause Analysis

### Known Facts
1. Both implementations now use SAMPLE pivot mode ✓
2. Both claim to follow the same algorithm:
   - Calculate pix0 BEFORE rotations
   - Apply rotations to pix0
3. The results differ significantly

### Hypothesis Ranking

**H1: Different Rotation Order (60% probability)**
- C might apply rotations in different order than Python
- Or might combine rotations differently
- Evidence: Y-component differs most (0.0588 vs 0.0227)

**H2: Different Initial Values (25% probability)**
- Beam center interpretation might differ
- Pixel size or distance units might be handled differently
- Evidence: All components differ, not just rotated ones

**H3: Missing/Extra Rotation (10% probability)**
- One implementation might skip or add a rotation
- Evidence: The difference seems systematic

**H4: Convention Difference (5% probability)**
- Active vs passive rotations
- Left-handed vs right-handed coordinate system
- Evidence: Would cause more dramatic differences

## Investigation Strategy

### Step 1: Deep Trace pix0 Calculation (1 hour)

Create ultra-detailed traces showing every single step of pix0 calculation.

#### 1.1 Enhanced C Instrumentation
Add to `nanoBragg.c` SAMPLE pivot section:
```c
// Before any calculations
printf("TRACE_C:beam_center_input=Xbeam:%.15g Ybeam:%.15g\n", Xbeam, Ybeam);
printf("TRACE_C:pixel_size_mm=%.15g\n", pixel_size * 1000);
printf("TRACE_C:distance_mm=%.15g\n", distance * 1000);

// Initial vector components
printf("TRACE_C:Fclose_mm=%.15g\n", Fclose * 1000);
printf("TRACE_C:Sclose_mm=%.15g\n", Sclose * 1000);

// Before rotation
printf("TRACE_C:pix0_before_rotation=%.15g %.15g %.15g\n", 
       pix0_vector[1], pix0_vector[2], pix0_vector[3]);

// After each rotation
printf("TRACE_C:pix0_after_rotx=%.15g %.15g %.15g\n", ...);
printf("TRACE_C:pix0_after_roty=%.15g %.15g %.15g\n", ...);
printf("TRACE_C:pix0_after_rotz=%.15g %.15g %.15g\n", ...);
printf("TRACE_C:pix0_after_twotheta=%.15g %.15g %.15g\n", ...);
```

#### 1.2 Enhanced Python Trace
Create `scripts/trace_pix0_detailed.py`:
```python
def trace_pix0_calculation_step_by_step():
    # Log every single intermediate value
    # Show matrix multiplications explicitly
    # Display values at each rotation stage
```

### Step 2: Matrix-Level Comparison (1 hour)

#### 2.1 Extract Rotation Matrices
Compare the actual rotation matrices used:
```python
# scripts/compare_rotation_matrices.py
def compare_c_and_python_matrices():
    # Extract rotation matrices from both traces
    # Compare element by element
    # Check multiplication order
```

#### 2.2 Manual Calculation Verification
```python
# scripts/verify_pix0_manually.py
def calculate_pix0_step_by_step():
    # Start with known initial values
    # Apply each rotation manually
    # Compare with both C and Python
```

### Step 3: Fix Implementation (30 min)

Based on findings, implement the fix. Most likely scenarios:

#### Fix A: Rotation Order
```python
# In detector.py _calculate_pix0_vector():
# Change rotation application order
```

#### Fix B: Initial Value Calculation
```python
# Adjust how Fclose/Sclose are calculated
# Or fix unit conversion issue
```

#### Fix C: Matrix Construction
```python
# Fix rotation matrix construction
# Or rotation combination method
```

### Step 4: Validation (30 min)

#### 4.1 Immediate Verification
```bash
# Run enhanced traces
./run_c_trace.sh
python scripts/trace_pix0_detailed.py
python scripts/compare_traces.py c_trace.log py_trace.log
```
**Expected**: pix0_vector values match within 1e-12

#### 4.2 Correlation Test
```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/verify_detector_geometry.py
```
**Expected**: Correlation > 0.999

#### 4.3 Comprehensive Test
```bash
# Test multiple configurations
python scripts/test_detector_configurations.py
```

## Implementation Plan

### Phase 4.1: Diagnostic Deep Dive (1.5 hours)

1. **Add granular C instrumentation**
   - Log every variable in pix0 calculation
   - Show rotation matrices explicitly
   - Display intermediate rotation results

2. **Create detailed Python tracer**
   - Mirror C instrumentation exactly
   - Use same variable names and order
   - Show all matrix operations

3. **Run side-by-side comparison**
   - Generate both traces
   - Find first divergence point
   - Identify the specific operation that differs

### Phase 4.2: Root Cause Identification (30 min)

1. **Analyze divergence point**
   - What calculation differs?
   - Is it a formula difference or parameter difference?
   - Can we reproduce it manually?

2. **Test hypothesis**
   - Create minimal reproduction
   - Verify the specific issue
   - Document the exact problem

### Phase 4.3: Fix Implementation (30 min)

1. **Apply targeted fix**
   - Modify only the identified issue
   - Preserve all working code
   - Add comments explaining the fix

2. **Verify fix locally**
   - Check pix0_vector matches
   - Ensure no regressions
   - Test edge cases

### Phase 4.4: Full Validation (30 min)

1. **Run complete test suite**
   ```bash
   pytest tests/test_detector_geometry.py -v
   pytest tests/test_pivot_mode_selection.py -v
   ```

2. **Verify correlation target**
   - Must achieve > 0.999
   - Test multiple configurations
   - Document results

3. **Update documentation**
   - Add fix to CLAUDE.md
   - Update detector.md if needed
   - Create fix summary

## Success Criteria

### Primary Goals
✅ pix0_vector values match within 1e-12 tolerance  
✅ Correlation > 0.999 for tilted detector  
✅ All existing tests still pass  

### Secondary Goals
✅ Clear documentation of the issue and fix  
✅ Regression test to prevent recurrence  
✅ Understanding of why the discrepancy existed  

## Risk Mitigation

### If Unable to Match Exactly
1. Check for legitimate algorithmic differences
2. Consider if C implementation has a bug
3. Document acceptable tolerance if small difference remains

### If Fix Breaks Other Tests
1. The fix might reveal other hidden issues
2. May need to fix multiple related problems
3. Consider if tests had compensating errors

### If Correlation Still Low
1. There may be additional issues beyond pix0
2. Check pixel coordinate generation
3. Verify scattering calculations

## Tools & Scripts Needed

### New Scripts to Create
1. `scripts/trace_pix0_detailed.py` - Ultra-detailed pix0 tracing
2. `scripts/compare_rotation_matrices.py` - Matrix comparison tool
3. `scripts/verify_pix0_manually.py` - Manual calculation verification

### Existing Scripts to Use
1. `scripts/compare_c_python_traces.py` - Trace comparison
2. `scripts/verify_detector_geometry.py` - Correlation test
3. `run_c_trace.sh` - C trace generation

## Detailed Trace Format

For maximum clarity, use this format for both C and Python:

```
TRACE_X:==== PIX0_VECTOR CALCULATION START ====
TRACE_X:input_beam_center_s=51.2
TRACE_X:input_beam_center_f=51.2
TRACE_X:pixel_size_mm=0.1
TRACE_X:distance_mm=100.0

TRACE_X:== Initial Calculation ==
TRACE_X:Fclose=(51.2 + 0.5) * 0.1 = 5.17 mm = 0.00517 m
TRACE_X:Sclose=(51.2 + 0.5) * 0.1 = 5.17 mm = 0.00517 m
TRACE_X:pix0_initial=[-0.00517*fdet - 0.00517*sdet + 0.1*odet]
TRACE_X:pix0_initial=[0.1, 0.00517, -0.00517]

TRACE_X:== Rotation Application ==
TRACE_X:rotx_matrix=[[1,0,0],[0,0.996,-0.087],[0,0.087,0.996]]
TRACE_X:pix0_after_rotx=[0.1, 0.00561, -0.00469]
...
```

## Expected Timeline

- **Hour 1**: Deep instrumentation and trace generation
- **Hour 2**: Analysis and root cause identification  
- **Hour 3**: Fix implementation and initial validation
- **Hour 4**: Full validation and documentation

## Decision Points

### After Step 1 (Deep Trace)
- If traces don't show clear difference → Check trace completeness
- If difference is in input values → Fix parameter handling
- If difference is in rotation → Fix rotation implementation

### After Step 2 (Matrix Comparison)
- If matrices differ → Fix matrix construction
- If order differs → Fix application sequence
- If both match → Look for numerical precision issues

### After Step 3 (Fix)
- If pix0 matches but correlation still low → Other issues exist
- If pix0 still differs → Re-examine assumptions
- If tests break → Fix may be correct, tests may have been compensating

## Completion Checklist

- [ ] Enhanced C instrumentation added
- [ ] Detailed Python tracer created
- [ ] Traces compared and divergence found
- [ ] Root cause identified and documented
- [ ] Fix implemented and tested
- [ ] pix0_vector values match (< 1e-12 difference)
- [ ] Correlation > 0.999 achieved
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Initiative can be closed

---

**Ready to Execute**: This plan provides a systematic approach to identify and fix the remaining pix0_vector calculation discrepancy.