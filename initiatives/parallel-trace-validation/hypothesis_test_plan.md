# Hypothesis Testing Plan for 28mm Systematic Offset

**Date**: 2025-01-09  
**Objective**: Systematically test and validate hypotheses for the 28mm offset and MOSFLM beam center convention issue  
**Target**: Achieve >0.999 correlation for tilted detector configurations  

---

## Executive Summary

This document provides a comprehensive testing plan to validate the 6 hypotheses for the 28mm systematic offset observed in detector geometry calculations. The plan includes specific test configurations, quantitative measurements, and decision criteria for each hypothesis.

## Test Priority Order

Based on probability and ease of testing:

1. **Hypothesis 1**: Different Rotation Centers (60% probability) - HIGHEST PRIORITY
2. **Hypothesis 2**: Beam Position Interpretation (40% probability) 
3. **Hypothesis 3**: Distance Definition Mismatch (30% probability)
4. **Hypothesis 4**: Missing Coordinate Transformation (25% probability)
5. **Hypothesis 5**: Detector Thickness/Parallax (20% probability)
6. **Hypothesis 6**: Integer vs Fractional Pixel (15% probability)

---

## Hypothesis 1: Different Rotation Centers (60% probability)

### Theory
C and PyTorch rotate around different points in space, creating a ~28mm offset.

### Test Checklist
- [ ] **Test 1.1**: Search C code for rotation center offsets
  - Search for terms: `28`, `280`, `0.028`, `0.28`
  - Check rotation matrix application points
  - Look for translation before/after rotations

- [ ] **Test 1.2**: Scale with distance test
  - Run with distances: 50mm, 100mm, 200mm, 400mm
  - Measure if 28mm error scales proportionally
  - Expected: Constant 28mm if absolute offset, scales if percentage

- [ ] **Test 1.3**: Trace rotation center coordinates
  - Add logging for rotation pivot point in C
  - Compare exact pivot coordinates C vs PyTorch
  - Look for systematic offset in pivot location

- [ ] **Test 1.4**: Different rotation angles
  - Test with rotx=0, roty=0, rotz=0, twotheta=15
  - Test with rotx=10, roty=10, rotz=10, twotheta=15
  - Check if error redistributes or changes magnitude

### Success Criteria
- [ ] Identify exact rotation center difference
- [ ] Error behavior matches expected pattern
- [ ] Can predict error from rotation angles

### Validation Script
```bash
# Test different distances
for dist in 50 100 200 400; do
    python scripts/verify_detector_geometry.py \
        --distance $dist \
        --rotx 5 --roty 3 --rotz 2 --twotheta 15 \
        --output "test_h1_dist_${dist}.json"
done
```

---

## Hypothesis 2: Beam Position Interpretation (40% probability)

### Theory
Beam position has systematic 280-pixel offset related to detector center vs corner reference.

### Test Checklist
- [ ] **Test 2.1**: Pixel offset analysis
  - Calculate exact offset in pixels: 28mm / 0.1mm/pixel = 280 pixels
  - Check if offset is exactly 280 pixels or close
  - Compare detector center (512,512) vs corner (0,0) reference

- [ ] **Test 2.2**: Different beam centers
  - Test beam centers: (0,0), (256,256), (512,512), (768,768)
  - Measure how error changes with beam position
  - Expected: Error moves with beam center if related

- [ ] **Test 2.3**: MOSFLM convention verification
  - Verify F↔Y and S↔X axis swapping
  - Check +0.5 pixel adjustment application
  - Trace exact beam center calculation in C

- [ ] **Test 2.4**: Beam center scaling
  - Test with different pixel sizes: 0.05mm, 0.1mm, 0.2mm
  - Check if error scales with pixel size
  - Expected: Proportional scaling if pixel-related

### Success Criteria
- [ ] Error is ~280 pixels (within 10%)
- [ ] Error changes predictably with beam center
- [ ] MOSFLM convention fully understood

### Validation Script
```bash
# Test different beam centers
for beam in "0 0" "256 256" "512 512" "768 768"; do
    python scripts/verify_detector_geometry.py \
        --beam $beam \
        --rotx 5 --roty 3 --rotz 2 --twotheta 15 \
        --output "test_h2_beam_${beam// /_}.json"
done
```

---

## Hypothesis 3: Distance Definition Mismatch (30% probability)

### Theory
"Distance" means different things between C and PyTorch (surface vs center vs pixel(0,0)).

### Test Checklist
- [ ] **Test 3.1**: Distance definition in C
  - Trace exact meaning of distance parameter
  - Check if distance is to detector surface, center, or corner
  - Look for distance adjustments or corrections

- [ ] **Test 3.2**: Distance scaling test
  - Test distances: 50mm, 100mm, 200mm, 400mm
  - Plot error vs distance
  - Expected: Linear relationship if distance-related

- [ ] **Test 3.3**: Detector thickness check
  - Search for detector thickness parameters
  - Check if 28mm could be detector thickness
  - Look for parallax corrections

- [ ] **Test 3.4**: Zero-distance extrapolation
  - Plot error vs distance and extrapolate to zero
  - Check intercept value
  - Expected: Non-zero intercept if offset-based

### Success Criteria
- [ ] Distance definition clearly identified
- [ ] Error behavior matches distance hypothesis
- [ ] Can calculate exact offset from distance

### Validation Script
```bash
# Distance scaling analysis
python scripts/analyze_distance_scaling.py \
    --distances 50,100,200,400 \
    --output distance_scaling_analysis.json
```

---

## Hypothesis 4: Missing Coordinate Transformation (25% probability)

### Theory
Additional coordinate transformation in C not applied in PyTorch.

### Test Checklist
- [ ] **Test 4.1**: Coordinate system analysis
  - Map all coordinate transformations in C
  - Check for lab→detector frame conversions
  - Look for origin shifts

- [ ] **Test 4.2**: Transformation order test
  - Test with single rotations only
  - Test with combined rotations
  - Check if error pattern matches missing transformation

- [ ] **Test 4.3**: Translation search
  - Search C for translation matrices
  - Check for coordinate offsets
  - Look for frame-specific adjustments

- [ ] **Test 4.4**: Identity configuration
  - Test with all rotations = 0
  - Check if error persists
  - Expected: Error disappears if rotation-dependent

### Success Criteria
- [ ] Missing transformation identified
- [ ] Can replicate transformation in PyTorch
- [ ] Error eliminated with transformation

### Validation Script
```bash
# Test identity configuration
python scripts/verify_detector_geometry.py \
    --rotx 0 --roty 0 --rotz 0 --twotheta 0 \
    --output test_h4_identity.json
```

---

## Hypothesis 5: Detector Thickness/Parallax (20% probability)

### Theory
C accounts for detector thickness or parallax correction creating apparent offset.

### Test Checklist
- [ ] **Test 5.1**: Thickness parameters
  - Search for detector thickness in C
  - Check for penetration depth calculations
  - Look for parallax correction terms

- [ ] **Test 5.2**: Angle dependence
  - Test various incident angles
  - Measure error vs angle
  - Expected: Angle-dependent if parallax

- [ ] **Test 5.3**: Energy dependence
  - Test different wavelengths/energies
  - Check if error changes with penetration depth
  - Expected: Energy-dependent if thickness-related

- [ ] **Test 5.4**: Literature comparison
  - Check if 28mm is typical detector thickness
  - Compare with standard detector specs
  - Validate against known detectors

### Success Criteria
- [ ] Thickness/parallax code found in C
- [ ] Error shows expected angle dependence
- [ ] 28mm matches physical detector property

---

## Hypothesis 6: Integer vs Fractional Pixel (15% probability)

### Theory
280-pixel offset from integer truncation or rounding differences.

### Test Checklist
- [ ] **Test 6.1**: Pixel calculation precision
  - Check for integer casts in C pixel calculations
  - Compare float vs int pixel positions
  - Look for accumulation of rounding errors

- [ ] **Test 6.2**: Detector size dependence
  - Test with detector sizes: 512, 1024, 2048
  - Check if error scales with detector size
  - Expected: Different pattern for different sizes

- [ ] **Test 6.3**: Sub-pixel analysis
  - Test beam centers at integer vs fractional positions
  - Measure difference in error
  - Expected: Discontinuous behavior if integer-related

- [ ] **Test 6.4**: Accumulation pattern
  - Trace pixel calculations for multiple pixels
  - Check if errors accumulate
  - Expected: Systematic accumulation if rounding

### Success Criteria
- [ ] Integer truncation identified in C
- [ ] Error pattern matches rounding hypothesis
- [ ] Can replicate with integer math

---

## Quantitative Measurements Required

### For All Hypotheses
1. **Exact error magnitude**: In mm and pixels
2. **Error vector components**: X, Y, Z breakdown
3. **Correlation value**: Before and after hypothesis fix
4. **Pivot mode impact**: BEAM vs SAMPLE comparison

### Key Metrics to Track
```python
metrics = {
    "error_magnitude_mm": float,
    "error_magnitude_pixels": float,
    "error_vector": [x, y, z],
    "correlation": float,
    "pivot_mode": str,
    "configuration": dict,
    "hypothesis": str
}
```

---

## Implementation Checklist

### Phase 1: Diagnostic Infrastructure
- [ ] Create hypothesis testing framework script
- [ ] Implement automated test runner for all configurations
- [ ] Set up data collection and analysis pipeline
- [ ] Create visualization tools for results

### Phase 2: Systematic Testing
- [ ] Execute Hypothesis 1 tests (rotation centers)
- [ ] Execute Hypothesis 2 tests (beam position)
- [ ] Execute Hypothesis 3 tests (distance definition)
- [ ] Execute remaining hypothesis tests in order
- [ ] Collect all quantitative measurements

### Phase 3: Analysis and Validation
- [ ] Analyze test results for each hypothesis
- [ ] Identify which hypothesis explains observations
- [ ] Validate hypothesis with additional tests
- [ ] Document findings and root cause

### Phase 4: Implementation
- [ ] Implement fix based on validated hypothesis
- [ ] Test fix with all configurations
- [ ] Verify correlation improvement to >0.999
- [ ] Add regression tests

---

## Test Execution Script

```bash
#!/bin/bash
# Master test execution script

# Create results directory
mkdir -p hypothesis_test_results

# Run all hypothesis tests
echo "Testing Hypothesis 1: Rotation Centers"
./test_hypothesis_1.sh > hypothesis_test_results/h1_results.log

echo "Testing Hypothesis 2: Beam Position"  
./test_hypothesis_2.sh > hypothesis_test_results/h2_results.log

# ... continue for all hypotheses

# Analyze results
python scripts/analyze_hypothesis_results.py \
    --input hypothesis_test_results \
    --output hypothesis_analysis.json

# Generate report
python scripts/generate_hypothesis_report.py \
    --input hypothesis_analysis.json \
    --output HYPOTHESIS_TEST_REPORT.md
```

---

## Success Criteria for Resolution

### The correct hypothesis must explain:
- [x] Why error is ~28mm (documented in hypotheses.md)
- [ ] Why it redistributes between axes based on pivot mode
- [ ] Why magnitude is preserved across configurations
- [ ] How to implement the fix
- [ ] Why correlation improves to >0.999 after fix

### Validation Requirements:
- [ ] Multiple test configurations confirm hypothesis
- [ ] Fix eliminates error to <0.1mm
- [ ] Correlation achieves >0.999 for all test cases
- [ ] No regression in working configurations
- [ ] Solution is mathematically sound

---

## Risk Assessment

### High Risk Items
1. **Multiple contributing factors**: Error might be combination of hypotheses
2. **Hidden conventions**: Undocumented C behavior not yet discovered
3. **Numerical precision**: Floating point differences masking true cause

### Mitigation Strategies
1. Test hypotheses in isolation and combination
2. Extensive C code instrumentation and tracing
3. Use high-precision arithmetic for validation

---

## Timeline Estimate

### Phase 1: Infrastructure (1-2 hours)
- Set up testing framework
- Create analysis tools
- Prepare test configurations

### Phase 2: Testing (3-4 hours)
- Execute all hypothesis tests
- Collect measurements
- Initial analysis

### Phase 3: Validation (1-2 hours)
- Deep dive on likely hypothesis
- Additional confirmation tests
- Root cause documentation

### Phase 4: Implementation (2-3 hours)
- Implement fix
- Test and validate
- Update documentation

**Total Estimated Time**: 7-11 hours

---

## Conclusion

This systematic testing plan provides a structured approach to identify and validate the root cause of the 28mm systematic offset. By testing each hypothesis with specific, measurable criteria, we can definitively determine the source of the error and implement the appropriate fix to achieve >0.999 correlation.

The plan prioritizes hypotheses by probability and ease of testing, ensuring efficient use of debugging time while maintaining thoroughness. The comprehensive checklist and validation scripts ensure reproducible results and clear documentation of findings.