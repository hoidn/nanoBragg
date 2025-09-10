# Phase 8 Implementation Checklist: Fix Y-Component (43mm Error)

**Target**: Fix Y-component of pix0_vector (currently 43mm off)  
**Success Metric**: pix0_vector difference < 1e-12 meters → Correlation > 99.9%  
**Time Estimate**: 2-4 hours  

## 🔴 CRITICAL: The Y-Component Problem

```
         X        Y        Z
C:     0.1121   0.0653  -0.0556  (reference)
Py:    0.1098   0.0227  -0.0518  (current)
Diff:  2.3mm    42.6mm   3.8mm
       ✓        ✗✗✗      ✓
```

**Only Y is catastrophically wrong!**

## Phase 8.1: Isolate the Y Error [45 min]

### Test A: No Rotations (Baseline)
- [ ] Create `scripts/test_y_without_rotations.py`
- [ ] Set all rotations to 0 degrees
- [ ] Compare C and Python pix0_vector
- [ ] Document Y-component values
- [ ] **Decision Point**: 
  - If Y still wrong → Initial calculation issue
  - If Y correct → Rotation-related issue

### Test B: Single Rotation Tests
- [ ] Test with ONLY rotx=5° (all others 0)
  - [ ] Record Y value
  - [ ] Compare with C
- [ ] Test with ONLY roty=3° (all others 0)
  - [ ] Record Y value
  - [ ] Compare with C
- [ ] Test with ONLY rotz=2° (all others 0)
  - [ ] Record Y value
  - [ ] Compare with C
- [ ] Test with ONLY twotheta=20° (all others 0)
  - [ ] Record Y value
  - [ ] Compare with C
- [ ] **Identify**: Which rotation introduces Y error?

### Test C: Progressive Build-Up
- [ ] Start with working config (likely no rotations)
- [ ] Add rotx=5° → Check Y
- [ ] Add roty=3° → Check Y
- [ ] Add rotz=2° → Check Y
- [ ] Add twotheta=20° → Check Y
- [ ] **Find**: Exact point where Y diverges

## Phase 8.2: Trace Y Through Calculations [45 min]

### C-Side Instrumentation
- [ ] Add Y-specific traces to nanoBragg.c:
  ```c
  printf("TRACE_Y: Initial beam_center_y=%.15g\n", ...);
  printf("TRACE_Y: Y after offset calc=%.15g\n", ...);
  printf("TRACE_Y: Y component of pix0 before rot=%.15g\n", ...);
  printf("TRACE_Y: Y after rotx=%.15g\n", ...);
  printf("TRACE_Y: Y after roty=%.15g\n", ...);
  printf("TRACE_Y: Y after rotz=%.15g\n", ...);
  printf("TRACE_Y: Y after twotheta=%.15g\n", ...);
  ```
- [ ] Compile and run with test config
- [ ] Save Y trace values

### Python-Side Instrumentation
- [ ] Create `scripts/trace_y_component.py`
- [ ] Add identical trace points
- [ ] Track Y at each calculation step
- [ ] Compare with C trace values
- [ ] **Find**: Exact line where Y diverges

### Direct Y Calculation Check
- [ ] Manually calculate expected Y value
- [ ] Use known inputs and rotation matrices
- [ ] Compare with both C and Python
- [ ] Verify which one is actually correct

## Phase 8.3: Test Specific Hypotheses [30 min]

### Hypothesis 1: Sign Flip
- [ ] Test if Y should be negative
- [ ] Calculate: -py_y vs c_y
- [ ] Check if difference becomes small
- [ ] Test in actual code

### Hypothesis 2: Axis Swap
- [ ] Check if Y is using wrong axis data
- [ ] Test if sdet/fdet are swapped for Y
- [ ] Verify MOSFLM axis conventions
- [ ] Check if Y calculation uses X or Z data

### Hypothesis 3: Matrix Element Error
- [ ] Print rotation matrix [1,1] element (Y→Y)
- [ ] Compare C and Python matrices
- [ ] Check if Y row or column is wrong
- [ ] Verify matrix multiplication order

### Hypothesis 4: Double Application
- [ ] Check if any Y rotation applied twice
- [ ] Verify rotation sequence
- [ ] Look for accidental Y modification
- [ ] Test with roty=0 to isolate

## Phase 8.4: Implement the Fix [30 min]

### Based on Finding, Apply Fix:

#### If Sign Flip Issue:
- [ ] Identify where sign should change
- [ ] Add sign correction for Y
- [ ] Document why sign was wrong
- [ ] Test with single sign change

#### If Axis Swap Issue:
- [ ] Correct axis mapping for Y
- [ ] Fix sdet/fdet confusion
- [ ] Update axis conventions
- [ ] Test axis correction

#### If Rotation Issue:
- [ ] Fix rotation application for Y
- [ ] Correct rotation order if needed
- [ ] Fix matrix element if wrong
- [ ] Test rotation fix

#### If Initial Calculation Issue:
- [ ] Fix beam center Y calculation
- [ ] Correct offset calculation
- [ ] Fix unit conversion for Y
- [ ] Test initial value fix

## Phase 8.5: Validation [30 min]

### Component-Level Tests
- [ ] Y-component difference < 1mm
- [ ] X-component still < 2mm
- [ ] Z-component still < 4mm
- [ ] Overall pix0_vector < 1e-12 m

### Integration Tests
- [ ] Run `verify_detector_geometry.py`
- [ ] Check tilted correlation > 0.999
- [ ] Check baseline still > 0.99
- [ ] Save final metrics

### Regression Tests
- [ ] Run detector test suite
- [ ] Fix any broken tests
- [ ] Document any behavior changes
- [ ] Ensure no new issues

## Phase 8.6: Documentation [15 min]

### Code Documentation
- [ ] Add comments explaining Y fix
- [ ] Document why Y was wrong
- [ ] Add warning about Y calculation
- [ ] Update detector.md if needed

### Create Regression Test
- [ ] Add test for Y-component
- [ ] Test prevents future Y errors
- [ ] Add to test suite
- [ ] Verify test passes

### Update Logs
- [ ] Add to undocumented_conventions.md
- [ ] Update debugging checklist
- [ ] Document in phase report
- [ ] Create fix summary

## Quick Debug Commands

```bash
# Test Y without rotations
python scripts/test_y_without_rotations.py

# Test single rotations
python scripts/test_single_rotation_y.py

# Trace Y component
python scripts/trace_y_component.py

# Check correlation
python scripts/verify_detector_geometry.py | grep tilted
```

## Decision Points

### After Test A (No Rotations):
- **Y Correct** → Focus on rotations (go to Test B)
- **Y Wrong** → Fix initial calculation (skip to Phase 8.4)

### After Test B (Single Rotations):
- **One rotation breaks Y** → Focus on that rotation
- **All rotations affect Y** → Check rotation application method
- **No single rotation breaks Y** → Check combinations

### After Trace:
- **Found divergence point** → Implement targeted fix
- **No clear divergence** → Check for accumulation of small errors

## Success Criteria

### Critical (Must Have)
- [ ] ✅ Y-component error < 1mm (currently 43mm)
- [ ] ✅ Overall pix0_vector < 1e-12 m
- [ ] ✅ Tilted correlation > 0.999
- [ ] ✅ All components accurate

### Important (Should Have)  
- [ ] Understand root cause
- [ ] Document the fix
- [ ] Add regression test
- [ ] No performance impact

## Emergency Procedures

### If Y Still Wrong After Fix:
1. Check for multiple Y errors
2. Verify fix was applied correctly
3. Look for compensating errors
4. Test with different configurations

### If Correlation Still Low:
1. Verify pix0 is actually fixed
2. Check for issues beyond pix0
3. Look at pixel coordinate generation
4. Consider other geometry issues

### If Tests Break:
1. Check if tests had wrong expectations
2. Verify fix is correct
3. Update tests to match correct behavior
4. Document why tests changed

---

**Remember**: The Y-component is 43mm off while X and Z are fine. This is not subtle - something is fundamentally wrong with Y calculations. Find it, fix it, and we're done!