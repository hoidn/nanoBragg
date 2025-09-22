# Detector Geometry Debugging: A Case Study

**Date:** January 2025  
**Issue:** Triclinic simulation correlation catastrophically dropped from 0.957 to 0.004  
**Root Cause:** Detector geometry calculations using wrong unit system (Angstroms instead of meters)  
**Resolution:** Updated Detector class to use hybrid unit system matching C-code conventions

## Executive Summary

This document captures the debugging journey that led to fixing a critical regression in the PyTorch nanoBragg implementation. A seemingly simple detector refactoring caused a complete failure of the triclinic test case. Through systematic debugging and parallel trace analysis, we discovered that the detector geometry system was using the wrong unit system, producing pixel positions that were off by 9 orders of magnitude.

## The Problem

After implementing the general detector geometry system (Phase 2), the triclinic test correlation dropped catastrophically:
- **Before:** 0.957 (excellent match)
- **After:** 0.004 (complete failure)

The simple_cubic test remained mostly functional, creating a confusing situation where one test passed and another failed completely.

## The Debugging Journey

### 1. Initial Misdiagnosis: Detector Configuration

**First Hypothesis:** Wrong detector parameters in the test configuration.

**What We Found:**
- Test was using `-detsize 1024` instead of `-detpixels 512`
- This created a 10240×10240 detector instead of 512×512
- **Fix Applied:** Updated triclinic test configuration

**Result:** Still broken! Correlation improved slightly but remained near zero.

### 2. Red Herring #1: F_latt Calculation

**Second Hypothesis:** The F_latt calculation was using wrong Miller indices.

**Investigation:**
- Noticed simulator was using `F_latt(h)` instead of `F_latt(h-h0)`
- Created a "fix" to use fractional indices
- **Discovery:** Both approaches gave identical results!

**Lesson:** The shape transform naturally zeroes out at integer values, making this a non-issue.

### 3. Red Herring #2: Numerical Precision

**Third Hypothesis:** The sincg function had numerical precision issues.

**Investigation:**
- Created comprehensive numerical validation tests
- Compared PyTorch vs NumPy vs C implementations
- **Result:** Perfect agreement to machine precision

**Lesson:** Don't blame numerical precision without evidence.

### 4. The Breakthrough: Parallel Trace Analysis

**Key Insight:** Stop guessing and directly compare calculations step-by-step.

**Method:**
1. Generated C-code trace: `./nanoBragg -trace_pixel 372 289 ...`
2. Created Python trace script to output identical format
3. Compared outputs line by line

**The Smoking Gun:**
```
Component         | C-Code (Correct)      | PyTorch (Broken)     | Error
------------------|-----------------------|----------------------|--------
Pixel Position    | 0.1 -0.011525 0.003225| 0.1 0.2193 -0.2276  | 70×
Diffracted Vector | 0.993 -0.114 0.032    | 0.302 0.662 -0.687  | Wrong!
Miller Indices    | 2.21, 0.36, 10.3      | 6.62, 61.5, -57.1   | Wrong!
```

The pixel positions were off by orders of magnitude, causing everything downstream to fail.

## Root Cause Analysis

### The Unit System Mismatch

**Global Rule (CLAUDE.md):** "All internal physics calculations MUST use Angstroms"

**Hidden Exception:** The C-code detector geometry calculations use **meters**, not Angstroms!

**Evidence:**
- C-code output: `DETECTOR_PIX0_VECTOR 0.1 0.0257 -0.0257` (meters)
- PyTorch output: `pix0_vector: [1.0e+09, 5.1e+08, -5.1e+08]` (Angstroms)

### Why This Happened

1. **Over-generalization:** Applied the global "Angstroms everywhere" rule to detector geometry
2. **Missing Documentation:** No explicit documentation that detector uses meters
3. **Subtle C-code Convention:** The C-code doesn't explicitly state units in most places

## The Fix

### Code Changes

```python
# BEFORE (Wrong):
self.distance = mm_to_angstroms(config.distance_mm)      # 100mm → 1e9 Å
self.pixel_size = mm_to_angstroms(config.pixel_size_mm)  # 0.1mm → 1e6 Å

# AFTER (Correct):
self.distance = config.distance_mm / 1000.0      # 100mm → 0.1 m
self.pixel_size = config.pixel_size_mm / 1000.0  # 0.1mm → 0.0001 m
```

### Verification

After the fix:
- Pixel positions matched C-code within 25 micrometers
- Triclinic correlation restored to 0.957
- All downstream calculations (Miller indices, structure factors) became correct

## Lessons Learned

### 1. Parallel Trace Debugging is Powerful

**The Technique:**
1. Instrument both implementations to output identical trace formats
2. Run the same test case through both
3. Compare outputs to find first divergence
4. Fix that specific calculation
5. Repeat until traces match

**Why It Works:**
- Eliminates guesswork
- Pinpoints exact location of bugs
- Provides ground truth for every calculation

### 2. Component-Specific Documentation is Critical

**What We Needed:**
- Explicit statement that detector geometry uses meters
- Warning about exception to global Angstrom rule
- Examples showing expected values for validation

**What We Had:**
- Global rule saying "use Angstroms everywhere"
- No detector-specific unit documentation
- No warning about this exception

### 3. Test Suite Design Matters

**Why This Bug Survived:**
- Simple_cubic test had high tolerance (correlation > 0.99)
- Detector geometry error was partially masked by other factors
- Only triclinic test was sensitive enough to catch the issue

**Better Approach:**
- Add explicit unit tests for detector geometry
- Test pixel coordinates against known values
- Don't rely solely on end-to-end correlation tests

### 4. Debugging Methodology

**What Worked:**
1. Systematic hypothesis testing
2. Creating minimal reproduction cases
3. Parallel trace comparison
4. Following the data flow from first principles

**What Didn't Work:**
1. Guessing based on symptoms
2. Making multiple changes at once
3. Assuming the bug was in complex physics (it was in simple geometry)

## Recommendations for Future Development

### 1. Mandatory Trace Validation

For any new component implementation:
1. Generate C-code trace for test case
2. Implement equivalent trace in PyTorch
3. Validate numerical agreement before proceeding

### 2. Explicit Unit Documentation

Every component should document:
- Input units (user-facing)
- Internal calculation units
- Output units (to other components)
- Any exceptions to global rules

### 3. Component Contracts

Before implementing any component:
1. Write complete technical specification
2. Document all conventions and units
3. Identify any non-standard behaviors
4. Get review from team

### 4. Regression Test Design

For critical paths:
- Test intermediate calculations, not just final results
- Include strict numerical tolerances where appropriate
- Add "canary" tests that fail loudly on specific bugs

## Conclusion

This debugging journey revealed that a simple unit conversion error can cascade into complete system failure. The fix was trivial once identified, but finding it required systematic debugging methodology and the right tools. The parallel trace technique proved invaluable and should be standard practice for scientific computing ports.

The key lesson: **Never assume conventions are universal. Always verify with ground truth data.**