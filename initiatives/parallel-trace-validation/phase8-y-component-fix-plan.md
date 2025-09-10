# Phase 8: Fix Y-Component Calculation Error - The 43mm Mystery

**Status**: Critical - Final barrier to >99.9% correlation  
**Issue**: Y-component of pix0_vector differs by 43mm between C and PyTorch  
**Confidence**: High - issue precisely localized to Y-component  
**Expected Time**: 2-4 hours  

## The Smoking Gun

After Phase 7, we have a very specific problem:

```
Component    C Reference    PyTorch      Difference
X:           0.1121 m      0.1098 m     2.3mm  ✓ (acceptable)
Y:           0.0653 m      0.0227 m     42.6mm ✗ (HUGE!)
Z:          -0.0556 m     -0.0518 m     3.8mm  ✓ (acceptable)
```

**The Y-component is off by 43mm while X and Z are nearly correct!**

## Critical Observations

1. **Not a convention issue**: Both using MOSFLM, same +0.5 pixel offset
2. **Not a unit issue**: All values in meters, same scale
3. **Not a small error**: 43mm is ~400 pixels - this is catastrophic
4. **Y-specific**: Only Y is dramatically wrong

## Hypothesis Priority (Ranked by Probability)

### H1: Sign Flip in Y Calculations (40%)
The Y difference (0.0653 vs 0.0227) suggests possible sign error:
- If PyTorch Y should be negative: -0.0227 + 0.0653 ≈ 0.043 (close to difference)
- Could be in rotation application or basis vector

### H2: Wrong Axis Used for Y (30%)
PyTorch might be using wrong component for Y calculations:
- Accidentally using X or Z data for Y
- MOSFLM axis mapping confusion (sdet vs fdet)

### H3: Missing/Extra Y Rotation (20%)
One implementation might skip or double-apply a Y-affecting rotation:
- detector_roty not applied correctly
- Y-component of twotheta rotation wrong

### H4: Row vs Column Vector Issue (10%)
Matrix multiplication order affecting Y specifically:
- C might use row vectors, PyTorch column vectors
- Would affect middle component most

## Surgical Investigation Plan

### Phase 8.1: Isolate Y-Component Error [1 hour]

#### Test 1: No Rotations
```python
# Set all rotations to 0
config = DetectorConfig(
    detector_rotx_deg=0, detector_roty_deg=0,
    detector_rotz_deg=0, detector_twotheta_deg=0
)
# If Y still wrong: Initial calculation issue
# If Y correct: Rotation-related issue
```

#### Test 2: Single Rotations
```python
# Test each rotation individually
rotations = [
    {"rotx": 5, "roty": 0, "rotz": 0, "twotheta": 0},  # Only X
    {"rotx": 0, "roty": 3, "rotz": 0, "twotheta": 0},  # Only Y
    {"rotx": 0, "roty": 0, "rotz": 2, "twotheta": 0},  # Only Z
    {"rotx": 0, "roty": 0, "rotz": 0, "twotheta": 20}, # Only twotheta
]
# Find which rotation breaks Y
```

#### Test 3: Y-Component Tracking
```python
# Trace Y through entire calculation
print(f"Initial Y calculation:")
print(f"  beam_center_s = {beam_center_s}")
print(f"  beam_center_f = {beam_center_f}")
print(f"  Y before rotation = {y_initial}")
print(f"  Y after rotx = {y_after_rotx}")
print(f"  Y after roty = {y_after_roty}")
print(f"  Y after rotz = {y_after_rotz}")
print(f"  Y after twotheta = {y_final}")
```

### Phase 8.2: Deep Trace Y Calculation [1 hour]

#### Step 1: Instrument C Code for Y
```c
// Add to nanoBragg.c
printf("TRACE_C:Y_COMPONENT_DEBUG:\n");
printf("  Initial Y from beam center: %.15g\n", y_initial);
printf("  Y after detector_rotx: %.15g\n", y_after_rotx);
printf("  Y after detector_roty: %.15g\n", y_after_roty);
printf("  Y after detector_rotz: %.15g\n", y_after_rotz);
printf("  Y after twotheta: %.15g\n", y_final);
```

#### Step 2: Match in PyTorch
```python
# Create identical trace
def trace_y_component():
    # Track Y at each step
    # Compare with C values
    # Find divergence point
```

#### Step 3: Binary Search the Error
- Start with working config (no rotations)
- Gradually add rotations
- Find exact point where Y diverges

### Phase 8.3: Implement the Fix [30 min]

Based on findings, likely fixes:

#### Fix A: Sign Correction
```python
# If sign flip found
if self._needs_y_sign_flip():
    pix0_vector[1] = -pix0_vector[1]
```

#### Fix B: Axis Correction
```python
# If wrong axis used
if self._is_mosflm_y_swap():
    # Swap Y calculation source
```

#### Fix C: Rotation Fix
```python
# If rotation issue
def _apply_y_rotation_correctly():
    # Fix the specific rotation
```

### Phase 8.4: Validate [30 min]

#### Immediate Check
```bash
# Y-component should match
python scripts/test_y_component.py
# Expected: Y difference < 1e-12
```

#### Full Validation
```bash
# Run complete test
python scripts/verify_detector_geometry.py
# Expected: Correlation > 0.999
```

## Implementation Checklist

### Setup [10 min]
- [ ] Create `scripts/debug_y_component.py`
- [ ] Create `scripts/test_y_isolation.py`
- [ ] Set up C tracing for Y component
- [ ] Document current Y values

### Investigation [90 min]
- [ ] Test with no rotations
- [ ] Test with single rotations
- [ ] Test with rotation pairs
- [ ] Identify which operation breaks Y
- [ ] Trace Y through that operation
- [ ] Compare C and Python Y calculations
- [ ] Find exact divergence point

### Root Cause Analysis [30 min]
- [ ] Determine if sign flip
- [ ] Check for axis swap
- [ ] Verify rotation direction
- [ ] Test matrix multiplication order
- [ ] Document the exact issue

### Implementation [30 min]
- [ ] Implement targeted fix
- [ ] Add only necessary code
- [ ] Preserve all working components
- [ ] Add comments explaining fix

### Validation [30 min]
- [ ] Y-component matches (< 1e-12)
- [ ] All components match (< 1e-12)
- [ ] pix0_vector matches (< 1e-12)
- [ ] Correlation > 0.999
- [ ] All tests pass

## Specific Test Scripts

### Script 1: `debug_y_component.py`
```python
"""Isolate and debug Y-component calculation."""

def test_y_component_isolation():
    # Test configurations that isolate Y
    configs = [
        # No rotations - baseline
        {"rotx": 0, "roty": 0, "rotz": 0, "twotheta": 0},
        # Add one rotation at a time
        {"rotx": 5, "roty": 0, "rotz": 0, "twotheta": 0},
        {"rotx": 5, "roty": 3, "rotz": 0, "twotheta": 0},
        # Full configuration
        {"rotx": 5, "roty": 3, "rotz": 2, "twotheta": 20},
    ]
    
    for config in configs:
        c_pix0 = run_c_with_config(config)
        py_pix0 = run_python_with_config(config)
        y_diff = c_pix0[1] - py_pix0[1]
        print(f"Config {config}: Y difference = {y_diff*1000:.1f}mm")
```

### Script 2: `test_sign_flip.py`
```python
"""Test if Y has sign flip issue."""

def test_sign_possibilities():
    py_y = 0.0227
    c_y = 0.0653
    
    tests = [
        ("No change", py_y, c_y),
        ("Flip PyTorch", -py_y, c_y),
        ("Flip C", py_y, -c_y),
        ("Flip both", -py_y, -c_y),
    ]
    
    for name, py, c in tests:
        diff = abs(py - c)
        print(f"{name}: diff = {diff*1000:.1f}mm")
```

### Script 3: `trace_rotation_effect.py`
```python
"""Trace how each rotation affects Y."""

def trace_rotation_effects():
    # Start with initial vector
    vec = torch.tensor([x_initial, y_initial, z_initial])
    
    print(f"Initial: Y = {vec[1]:.6f}")
    
    # Apply rotations one by one
    vec = apply_rotx(vec, 5)
    print(f"After rotx(5°): Y = {vec[1]:.6f}")
    
    vec = apply_roty(vec, 3)
    print(f"After roty(3°): Y = {vec[1]:.6f}")
    
    # Compare with C at each step
```

## Success Criteria

### Must Fix
- [ ] Y-component difference < 1mm
- [ ] All components < 1mm difference
- [ ] pix0_vector < 1e-12 difference
- [ ] Correlation > 0.999

### Should Understand
- [ ] Why Y was wrong
- [ ] How to prevent similar issues
- [ ] Document the fix clearly

## Risk Mitigation

### If No Single Rotation Causes Issue
- Test rotation combinations
- Check rotation order
- Verify matrix construction

### If Y Correct Without Rotations
- Focus entirely on rotation logic
- Check rotation matrices element by element
- Verify rotation application method

### If Sign Flip Not the Issue
- Check coordinate system conventions
- Verify axis definitions
- Look for preprocessing differences

## Expected Outcome

Once we fix the Y-component:
1. pix0_vector difference drops from 23mm to < 1mm
2. Correlation jumps from 4% to > 99.9%
3. Can close the parallel-trace-validation initiative

## Decision Tree

```
Is Y wrong without rotations?
├─> YES: Initial calculation issue
│   └─> Check beam center, axis mapping
└─> NO: Rotation-related
    ├─> Which rotation breaks Y?
    ├─> Is it sign flip? → Fix sign
    ├─> Is it wrong axis? → Fix axis
    └─> Is it rotation order? → Fix order
```

---

**Focus**: Y-component has 43mm error while X,Z are fine  
**Strategy**: Surgical isolation of Y calculation  
**Confidence**: Very high - error is precisely localized