# Phase 6: Match C's Actual Beam Center Behavior - Implementation Checklist

**Goal**: Make PyTorch match C's actual beam center calculation, not our interpretation  
**Key Insight**: C is ground truth - we must match what it DOES, not what we think it SHOULD do  
**Target**: Achieve >0.999 correlation by matching C's beam center exactly  

## Pre-Flight Checks
- [ ] Confirm C produces `5.125e-05 m` for beam center (from Phase 5 traces)
- [ ] Confirm PyTorch expects `0.00517 m` (100x difference)
- [ ] Document that C is ground truth - any "fix" must be in PyTorch

## Section 1: Deep Trace C's Beam Center Calculation [45 min]

### 1.1 Add Comprehensive C Instrumentation
- [ ] Open `golden_suite_generator/nanoBragg.c`
- [ ] Find beam center calculation section (search for `Fclose`, `Sclose`)
- [ ] Add detailed trace statements:
  ```c
  printf("TRACE_C:=== BEAM CENTER CALCULATION START ===\n");
  printf("TRACE_C:Xbeam_raw_input=%.15g\n", Xbeam);
  printf("TRACE_C:Ybeam_raw_input=%.15g\n", Ybeam); 
  printf("TRACE_C:pixel_size_raw=%.15g\n", pixel_size);
  printf("TRACE_C:detector_thick_raw=%.15g\n", detector_thick);
  
  // Before any calculations
  printf("TRACE_C:Fclose_before_calc=%.15g\n", Fclose);
  printf("TRACE_C:Sclose_before_calc=%.15g\n", Sclose);
  
  // After calculations
  printf("TRACE_C:Fclose_final=%.15g\n", Fclose);
  printf("TRACE_C:Sclose_final=%.15g\n", Sclose);
  printf("TRACE_C:=== BEAM CENTER CALCULATION END ===\n");
  ```
- [ ] Add traces for any intermediate variables
- [ ] Ensure traces work for both BEAM and SAMPLE pivot modes

### 1.2 Compile and Run Instrumented C
- [ ] Recompile: `make -C golden_suite_generator clean all`
- [ ] Run with standard test parameters:
  ```bash
  ./nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 \
    -default_F 100 -distance 100 -detpixels 1024 \
    -Xbeam 51.2 -Ybeam 51.2 \
    -detector_rotx 5 -detector_roty 3 -detector_rotz 2 \
    -detector_twotheta 20 -pivot sample \
    -floatfile output.bin 2>&1 | grep "TRACE_C:" > c_beam_center_trace.log
  ```
- [ ] Verify trace output shows beam center calculation details

### 1.3 Analyze C's Actual Formula
- [ ] Document exact sequence of operations from trace
- [ ] Identify what units are used at each step
- [ ] Note any unexpected conversions or factors
- [ ] Check if formula differs between BEAM/SAMPLE pivots

## Section 2: Understand C's Parameter Interpretation [30 min]

### 2.1 Read C Source for Parameter Parsing
- [ ] Find where `-Xbeam` and `-Ybeam` are parsed
- [ ] Document what units C expects (pixels? mm? meters?)
- [ ] Check for any unit conversions during parsing
- [ ] Look for default values or special handling

### 2.2 Trace Parameter Flow
- [ ] Track `Xbeam` from command line to calculation
- [ ] Track `Ybeam` from command line to calculation  
- [ ] Identify any transformations applied
- [ ] Document the complete parameter pipeline

### 2.3 Compare with Python Assumptions
- [ ] List what PyTorch assumes about beam center units
- [ ] Identify where assumptions diverge from C reality
- [ ] Document the specific differences

## Section 3: Implement C's Exact Logic in PyTorch [45 min]

### 3.1 Create Test Implementation
- [ ] Create `scripts/test_c_beam_center_match.py`:
  ```python
  def calculate_beam_center_like_c(beam_x, beam_y, pixel_size):
      """
      Replicate C's exact beam center calculation.
      Based on traced values from C implementation.
      """
      # Implement whatever C actually does
      # Even if it seems counterintuitive
      pass
  ```
- [ ] Test with known C inputs/outputs
- [ ] Verify produces `5.125e-05 m` for test case

### 3.2 Update PyTorch Detector Class
- [ ] Open `src/nanobrag_torch/models/detector.py`
- [ ] Locate `_calculate_pix0_vector()` method
- [ ] Update beam center calculation for BEAM pivot:
  ```python
  # Document what C actually does
  # C interprets beam center as [actual C behavior]
  # This produces values like 5.125e-05 m
  ```
- [ ] Update beam center calculation for SAMPLE pivot similarly
- [ ] Add detailed comments explaining the C convention

### 3.3 Add Compatibility Flag (Optional)
- [ ] Consider adding a flag for C-compatible mode:
  ```python
  class DetectorConfig:
      use_c_beam_convention: bool = True  # Match C exactly
  ```
- [ ] Allow switching between "expected" and "C-actual" behavior
- [ ] Default to C-compatible for validation

## Section 4: Validate the Fix [30 min]

### 4.1 Generate Comparison Traces
- [ ] Run C with instrumentation: `./run_c_trace.sh`
- [ ] Run Python with fix: `python scripts/trace_pixel_512_512.py`
- [ ] Compare beam center values - should match exactly
- [ ] Compare pix0_vector - should match within 1e-12

### 4.2 Run Correlation Test
- [ ] Execute: `KMP_DUPLICATE_LIB_OK=TRUE python scripts/verify_detector_geometry.py`
- [ ] Check correlation for tilted case
- [ ] **Success Criterion**: Correlation > 0.999
- [ ] Verify baseline case still works

### 4.3 Run Full Test Suite
- [ ] Run detector tests: `pytest tests/test_detector_*.py -v`
- [ ] Run pivot mode tests: `pytest tests/test_pivot_mode_selection.py -v`
- [ ] Ensure no regressions introduced
- [ ] All tests should pass

## Section 5: Document and Finalize [30 min]

### 5.1 Create Fix Documentation
- [ ] Document the actual C convention discovered
- [ ] Explain why it differs from expectations
- [ ] Add to `docs/development/c_to_pytorch_config_map.md`
- [ ] Update relevant docstrings in detector.py

### 5.2 Add Regression Test
- [ ] Create test that validates beam center calculation:
  ```python
  def test_c_compatible_beam_center():
      """Ensure beam center matches C's actual behavior."""
      # Test that we produce 5.125e-05 m for standard case
      pass
  ```
- [ ] Add to test suite
- [ ] Verify test passes

### 5.3 Write Implementation Summary
- [ ] Create `history/2025-01-09_phase6_beam_center_fix.md`
- [ ] Document what was discovered
- [ ] Explain the fix
- [ ] Record correlation improvement

## Success Criteria Checklist
- [ ] Beam center values match C exactly
- [ ] pix0_vector matches within 1e-12 tolerance
- [ ] Correlation > 0.999 for tilted detector
- [ ] All existing tests still pass
- [ ] Fix is documented and tested

## Contingency Plans

### If C's Formula Still Unclear
- [ ] Add even more detailed traces
- [ ] Check for preprocessor macros affecting calculation
- [ ] Look for configuration files that might modify behavior
- [ ] Consider if C has a bug we need to replicate

### If Fix Doesn't Improve Correlation
- [ ] Verify traces match for ALL intermediate values
- [ ] Check for additional issues beyond beam center
- [ ] Consider numerical precision differences
- [ ] Look for other parameter mismatches

### If Tests Break
- [ ] The broken tests might have been compensating for the error
- [ ] Update tests to match correct behavior
- [ ] Document why tests needed updating

## Final Verification
- [ ] C and PyTorch produce identical beam center values
- [ ] C and PyTorch produce identical pix0_vector
- [ ] Correlation meets target (>0.999)
- [ ] Documentation complete
- [ ] Tests passing
- [ ] Ready to close parallel-trace-validation initiative

---

**Estimated Time**: 3 hours total  
**Confidence Level**: High - we know exactly what to fix  
**Risk Level**: Low - surgical change to match C behavior