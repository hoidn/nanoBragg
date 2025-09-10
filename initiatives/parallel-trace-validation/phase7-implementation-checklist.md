# Phase 7 Implementation Checklist: Fix Basis Vector Calculation

**Goal**: Implement CUSTOM convention handling to fix 39mm pix0_vector discrepancy  
**Target**: Achieve >99.9% correlation for tilted detector  
**Time Estimate**: 2-3 hours  

## Pre-Implementation Setup [15 min]
- [ ] Clear working directory of test files
- [ ] Verify current correlation is ~0.04 for tilted case
- [ ] Create backup branch or note current commit
- [ ] Set up terminal windows for C and Python testing

## Step 1: Investigate CUSTOM Convention Behavior [45 min]

### 1.1 Test Convention Switching
- [ ] Create `scripts/test_custom_convention.py`
- [ ] Test C behavior WITHOUT `-twotheta_axis` (MOSFLM mode)
- [ ] Test C behavior WITH `-twotheta_axis 0 0 -1` (CUSTOM mode)
- [ ] Compare pix0_vector values between modes
- [ ] Document the exact difference

### 1.2 Trace Basis Vector Initialization
- [ ] Add C traces for initial basis vectors (before any rotations)
- [ ] Check if CUSTOM changes initial fdet, sdet, odet vectors
- [ ] Compare with MOSFLM initial vectors
- [ ] Document any differences

### 1.3 Trace Rotation Sequence
- [ ] Add detailed rotation traces to C code
- [ ] Trace fdet after each rotation (rotx, roty, rotz, twotheta)
- [ ] Generate traces for both MOSFLM and CUSTOM modes
- [ ] Identify where vectors diverge

## Step 2: Implement CUSTOM Convention in PyTorch [45 min]

### 2.1 Add Convention Detection
- [ ] Add method to detect CUSTOM mode trigger:
  ```python
  def _is_custom_convention(self):
      return self.config.twotheta_axis is not None
  ```
- [ ] Add logging to confirm detection works

### 2.2 Modify pix0_vector Calculation
- [ ] Update `_calculate_pix0_vector()` method
- [ ] Add CUSTOM convention branch
- [ ] Remove +0.5 pixel offset for CUSTOM mode
- [ ] Test pix0_vector calculation

### 2.3 Adjust Basis Vector Handling (if needed)
- [ ] If initial vectors differ, add CUSTOM initialization
- [ ] If rotation sequence differs, add CUSTOM rotation path
- [ ] Ensure all changes preserve differentiability

## Step 3: Validate the Fix [30 min]

### 3.1 Direct pix0_vector Comparison
- [ ] Run `python scripts/compare_c_python_pix0.py`
- [ ] Verify difference < 1e-12 meters
- [ ] Check both MOSFLM and CUSTOM modes
- [ ] Document final values

### 3.2 Correlation Test
- [ ] Run `python scripts/verify_detector_geometry.py`
- [ ] Check tilted correlation (target > 0.999)
- [ ] Check baseline still works (> 0.99)
- [ ] Save correlation metrics

### 3.3 Regression Testing
- [ ] Run `pytest tests/test_detector_geometry.py -v`
- [ ] Run `pytest tests/test_pivot_mode_selection.py -v`
- [ ] Ensure no tests break
- [ ] Fix any broken tests (may need updates for CUSTOM)

## Step 4: Edge Case Testing [20 min]

### 4.1 Test Various Configurations
- [ ] Test with different rotation angles
- [ ] Test with twotheta_axis = [0, 1, 0] (Y-axis)
- [ ] Test with twotheta_axis = [1, 0, 0] (X-axis)
- [ ] Test without any rotations but with twotheta_axis set

### 4.2 Test Convention Consistency
- [ ] Verify BEAM pivot + CUSTOM convention
- [ ] Verify SAMPLE pivot + CUSTOM convention
- [ ] Ensure XDS convention still works
- [ ] Check that omitting twotheta_axis preserves MOSFLM

## Step 5: Documentation and Cleanup [20 min]

### 5.1 Update Documentation
- [ ] Add CUSTOM convention to `detector.md`
- [ ] Update `undocumented_conventions.md`
- [ ] Add docstrings explaining CUSTOM mode
- [ ] Update any affected test documentation

### 5.2 Create Regression Test
- [ ] Add test for CUSTOM convention:
  ```python
  def test_custom_convention_pix0():
      """Verify CUSTOM convention removes +0.5 pixel offset."""
  ```
- [ ] Add to test suite
- [ ] Verify test passes

### 5.3 Clean Up
- [ ] Remove debug print statements
- [ ] Remove temporary test files
- [ ] Format code with black/ruff
- [ ] Review changes with `git diff`

## Step 6: Final Validation [15 min]

### 6.1 End-to-End Verification
- [ ] Run complete verification one more time
- [ ] Confirm correlation > 0.999 for tilted
- [ ] Confirm correlation > 0.99 for baseline
- [ ] Generate final comparison plots

### 6.2 Performance Check
- [ ] Time the verification script
- [ ] Ensure no performance regression
- [ ] Check memory usage is reasonable

## Success Criteria Checklist

### Must Pass
- [ ] ✅ pix0_vector difference < 1e-12 meters
- [ ] ✅ Tilted correlation > 0.999
- [ ] ✅ Baseline correlation still > 0.99
- [ ] ✅ All existing tests pass

### Should Have
- [ ] CUSTOM convention documented
- [ ] Regression test for CUSTOM mode
- [ ] Clear code comments explaining logic

## Contingency Checks

### If pix0 Still Doesn't Match
- [ ] Check for additional CUSTOM changes
- [ ] Verify rotation matrix construction
- [ ] Look for hidden preprocessing
- [ ] Consider floating point precision

### If Correlation Doesn't Improve
- [ ] Verify pix0 is actually the issue
- [ ] Check pixel coordinate generation
- [ ] Look for issues beyond detector geometry
- [ ] Consider if C has a bug we're replicating

## Quick Verification Commands

```bash
# Check current state
python scripts/verify_detector_geometry.py | grep correlation

# After implementation
python scripts/compare_c_python_pix0.py
python scripts/verify_detector_geometry.py

# Run tests
pytest tests/test_detector_*.py -xvs
```

## Sign-Off

- [ ] Implementation complete
- [ ] All tests passing
- [ ] Correlation target achieved
- [ ] Documentation updated
- [ ] Ready for review

---

**Start Time**: ___________  
**End Time**: ___________  
**Actual Duration**: ___________  
**Final Correlation**: ___________