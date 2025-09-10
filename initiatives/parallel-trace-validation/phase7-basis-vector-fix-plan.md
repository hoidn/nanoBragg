# Phase 7: Fix Basis Vector Calculation - The Final Mile

**Status**: Ready to implement  
**Confidence**: High - issue precisely localized  
**Expected Time**: 2-3 hours  
**Success Metric**: Correlation > 99.9% for tilted detector  

## Current Situation

### What We Know ✅
1. **Root cause identified**: 39mm difference in pix0_vector for tilted configurations
2. **Not the problem**: Beam center (correct), rotation matrices (perfect), pivot mode (fixed)
3. **The problem**: Basis vector calculations produce different results between C and Python
4. **Key discovery**: CUSTOM convention triggers when `-twotheta_axis` is specified

### The Evidence
```
Configuration: rotx=5°, roty=3°, rotz=2°, twotheta=20°
Python pix0: [0.109814, 0.022698, -0.051758] m
C pix0:      [0.095234, 0.058827, -0.051702] m
Difference:  39mm (causes 4% correlation)
```

## Hypothesis: CUSTOM Convention Changes More Than Expected

Based on Phase 6 findings, when `-twotheta_axis` is specified:
1. C switches to CUSTOM convention
2. This removes the +0.5 pixel offset (we know this)
3. **But it might also change**: Basis vector initialization or rotation sequence

## Implementation Plan

### Step 1: Trace CUSTOM vs MOSFLM Basis Vectors (30 min)

#### 1.1 Create Comparison Script
```python
# scripts/test_custom_vs_mosflm.py
def test_convention_differences():
    # Test 1: Without twotheta_axis (MOSFLM)
    run_c_without_axis()
    
    # Test 2: With twotheta_axis (CUSTOM)
    run_c_with_axis()
    
    # Compare basis vectors, not just pix0
```

#### 1.2 Check What Changes
- Initial basis vectors (before rotation)?
- Rotation sequence?
- Rotation matrices themselves?
- Order of operations?

### Step 2: Deep Trace the Rotation Sequence (45 min)

#### 2.1 Instrument Rotation Application
Add traces to C code showing:
```c
printf("TRACE_C:fdet_before_rotx=%.15g %.15g %.15g\n", ...);
printf("TRACE_C:fdet_after_rotx=%.15g %.15g %.15g\n", ...);
printf("TRACE_C:fdet_after_roty=%.15g %.15g %.15g\n", ...);
printf("TRACE_C:fdet_after_rotz=%.15g %.15g %.15g\n", ...);
printf("TRACE_C:fdet_after_twotheta=%.15g %.15g %.15g\n", ...);
```

#### 2.2 Match in Python
Create identical traces in PyTorch Detector to find divergence point.

### Step 3: Implement the Fix (45 min)

Based on findings, likely fixes:

#### Option A: CUSTOM Convention Logic
```python
class Detector:
    def _calculate_pix0_vector(self):
        if self._is_custom_convention():
            # Different initialization or calculation
            # No +0.5 pixel offset
            # Possibly different basis vectors
```

#### Option B: Rotation Sequence Adjustment
```python
def _apply_rotations(self):
    if self._is_custom_convention():
        # Different rotation order or method
```

#### Option C: Basis Vector Initialization
```python
def _initialize_basis_vectors(self):
    if self._is_custom_convention():
        # Different starting basis vectors
```

### Step 4: Validate the Fix (30 min)

#### 4.1 Check pix0_vector Match
```bash
# Should see < 1e-12 difference
python scripts/compare_c_python_pix0.py
```

#### 4.2 Run Full Correlation Test
```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/verify_detector_geometry.py
```
**Target**: > 99.9% correlation for tilted configuration

#### 4.3 Verify No Regressions
```bash
pytest tests/test_detector_*.py -v
```

## Specific Investigation Areas

### A. The CUSTOM Convention Trigger
```python
def _is_custom_convention(self):
    # Check if twotheta_axis was explicitly set
    # This triggers CUSTOM mode in C
    return self.config.twotheta_axis is not None
```

### B. The Axis Convention
CUSTOM might use different axis definitions:
- Different handedness?
- Different axis assignment?
- Different rotation direction?

### C. The Operation Order
CUSTOM might apply operations differently:
1. Calculate pix0 with/without offset
2. Apply rotations in different sequence
3. Use different basis vector origins

## Success Criteria

### Must Have
- [ ] pix0_vector matches C within 1e-12 m
- [ ] Correlation > 99.9% for tilted detector
- [ ] All existing tests pass

### Nice to Have
- [ ] Document CUSTOM convention fully
- [ ] Add regression test for CUSTOM mode
- [ ] Performance unchanged or improved

## Risk Mitigation

### If CUSTOM Convention Not the Issue
1. Check for preprocessor directives in C code
2. Look for hidden state variables
3. Consider numerical precision differences
4. Check for context-dependent calculations

### If Fix Breaks Other Tests
1. The tests might have been compensating
2. Add configuration flag for compatibility
3. Document the behavioral change

## Implementation Checklist

### Pre-Implementation
- [ ] Review Phase 6 findings
- [ ] Set up trace infrastructure
- [ ] Create backup of current code

### Implementation
- [ ] Test CUSTOM vs MOSFLM conventions
- [ ] Trace rotation sequence in detail
- [ ] Identify exact divergence point
- [ ] Implement targeted fix
- [ ] Add CUSTOM convention handling

### Validation
- [ ] pix0_vector matches (< 1e-12)
- [ ] Correlation > 99.9%
- [ ] All tests pass
- [ ] No performance regression

### Documentation
- [ ] Update detector.md
- [ ] Document CUSTOM convention
- [ ] Add to undocumented_conventions.md
- [ ] Create regression test

## Quick Test Commands

### Check Current State
```bash
# Quick correlation check
python scripts/verify_detector_geometry.py | grep tilted
# Expected: ~0.04
```

### After Fix
```bash
# Should show > 0.999
python scripts/verify_detector_geometry.py | grep tilted
```

### Direct pix0 Comparison
```bash
# Should show < 1e-12 difference
python scripts/compare_c_python_pix0.py
```

## Decision Tree

```
Is CUSTOM convention changing basis vectors?
├─> YES: Implement CUSTOM handling in Detector
└─> NO: Check rotation sequence
    ├─> Different order? Fix sequence
    └─> Same order? Check for hidden transforms
```

## Expected Outcome

Once we match the CUSTOM convention behavior:
1. pix0_vector difference drops from 39mm to < 1nm
2. Correlation jumps from 4% to > 99.9%
3. Initiative can be closed as successful

---

**Confidence Level**: 85% - CUSTOM convention is likely the key  
**Backup Plan**: Deep trace every calculation if CUSTOM not the issue  
**Time to Resolution**: 2-3 hours