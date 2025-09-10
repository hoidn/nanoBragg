# Phase 5: Rotation Hypothesis Test Plan

**Hypothesis**: The remaining 3cm pix0_vector offset is caused by differences in rotation logic between C and Python implementations  
**Status**: UNPROVEN - This is a hypothesis based on observation, not confirmed fact  
**Goal**: Definitively prove or disprove this hypothesis through systematic testing  

## Observable Facts (What We Know)

1. **No rotations = Perfect match**: Basic BEAM pivot (no rotations) matches with ~1e-18 precision
2. **With rotations = 3cm offset**: All rotated configurations show ~0.03m systematic offset
3. **Offset is consistent**: Both BEAM and SAMPLE pivots show similar offset magnitude
4. **Correlation stuck at 0.040**: This offset propagates to all pixels

## Test Strategy: Systematic Isolation

### Test 1: Individual Rotation Components
**Purpose**: Identify if ONE specific rotation is wrong

```python
# Test configurations (all with BEAM pivot for simplicity):
test_cases = [
    {"name": "baseline", "rotx": 0, "roty": 0, "rotz": 0, "twotheta": 0},
    {"name": "only_rotx", "rotx": 5, "roty": 0, "rotz": 0, "twotheta": 0},
    {"name": "only_roty", "rotx": 0, "roty": 3, "rotz": 0, "twotheta": 0},
    {"name": "only_rotz", "rotx": 0, "roty": 0, "rotz": 2, "twotheta": 0},
    {"name": "only_twotheta", "rotx": 0, "roty": 0, "rotz": 0, "twotheta": 20},
]
```

**Expected Outcome**: 
- If ONE rotation is wrong, only that test case will show offset
- If ALL show offset, the issue is in rotation infrastructure itself

### Test 2: Rotation Pairs
**Purpose**: Check if rotation COMBINATION is the issue

```python
pair_tests = [
    {"name": "rotx_roty", "rotx": 5, "roty": 3, "rotz": 0, "twotheta": 0},
    {"name": "rotx_rotz", "rotx": 5, "roty": 0, "rotz": 2, "twotheta": 0},
    {"name": "roty_rotz", "rotx": 0, "roty": 3, "rotz": 2, "twotheta": 0},
    {"name": "rotx_twotheta", "rotx": 5, "roty": 0, "rotz": 0, "twotheta": 20},
]
```

**Expected Outcome**:
- If offset appears only with pairs, rotation order/combination is wrong
- If offset scales with number of rotations, accumulation error exists

### Test 3: Rotation Order Verification
**Purpose**: Verify rotation multiplication order

**Method A: Direct Matrix Extraction**
```python
# Extract from C trace
C_matrix = parse_c_rotation_matrix()

# Extract from Python
Rx = rotation_x(5°)
Ry = rotation_y(3°) 
Rz = rotation_z(2°)
Python_matrix = Rz @ Ry @ Rx  # or is it Rx @ Ry @ Rz?

# Compare
difference = C_matrix - Python_matrix
```

**Method B: Apply Different Orders**
```python
orders = [
    ("xyz", lambda: Rz @ Ry @ Rx),
    ("zyx", lambda: Rx @ Ry @ Rz),
    ("yxz", lambda: Rz @ Rx @ Ry),
    # ... all 6 permutations
]
```

### Test 4: Convention Testing
**Purpose**: Check active vs passive rotations

```python
def test_rotation_conventions():
    # Active rotation: rotate vector
    v_active = R @ v
    
    # Passive rotation: rotate coordinate system
    v_passive = R.T @ v
    
    # Check which matches C
```

### Test 5: Progressive Build-Up
**Purpose**: Find exact point where offset appears

```python
# Start with working baseline
config = {"rotx": 0, "roty": 0, "rotz": 0, "twotheta": 0}
verify_pix0_matches()  # Should pass

# Add rotations one at a time
config["rotx"] = 5
verify_pix0_matches()  # Does offset appear here?

config["roty"] = 3  
verify_pix0_matches()  # Or here?

config["rotz"] = 2
verify_pix0_matches()  # Or here?

config["twotheta"] = 20
verify_pix0_matches()  # Or only with all four?
```

### Test 6: Numerical Analysis of Offset
**Purpose**: Understand the 3cm offset pattern

```python
def analyze_offset_pattern():
    # Is 3cm related to any input parameter?
    # 0.03m = 30mm = 300 pixels * 0.1mm/pixel
    # 0.03m ≈ sin(2°) * distance?
    # 0.03m ≈ some trig function of angles?
    
    # Test with different angles
    for angle in [1, 2, 5, 10, 20]:
        offset = measure_pix0_offset(angle)
        print(f"Angle: {angle}°, Offset: {offset}m")
        # Look for pattern: linear? sin? tan?
```

### Test 7: Sign Convention Testing
**Purpose**: Check if angle signs are interpreted differently

```python
sign_tests = [
    {"rotx": +5, "roty": +3},  # Both positive
    {"rotx": -5, "roty": +3},  # Mixed signs
    {"rotx": +5, "roty": -3},  # Mixed signs
    {"rotx": -5, "roty": -3},  # Both negative
]
```

## Implementation Checklist

### Script 1: `test_rotation_isolation.py`
```python
def test_each_rotation_individually():
    """Test rotx, roty, rotz, twotheta separately"""
    
def test_rotation_pairs():
    """Test combinations of two rotations"""
    
def test_progressive_buildup():
    """Add rotations one at a time"""
```

### Script 2: `test_rotation_order.py`
```python
def test_matrix_multiplication_order():
    """Try all 6 permutations of Rx, Ry, Rz"""
    
def extract_c_rotation_matrix():
    """Parse C trace for actual matrix values"""
```

### Script 3: `test_rotation_conventions.py`
```python
def test_active_vs_passive():
    """Check if rotations are active or passive"""
    
def test_coordinate_system_handedness():
    """Verify right-handed vs left-handed"""
```

### Script 4: `analyze_offset_pattern.py`
```python
def measure_offset_vs_angle():
    """Plot offset as function of rotation angle"""
    
def find_offset_formula():
    """Try to derive mathematical relationship"""
```

## Success Criteria

### Primary: Identify Root Cause
- [ ] Know exactly which rotation(s) cause the offset
- [ ] Understand why (order, convention, sign, etc.)
- [ ] Have mathematical proof of the difference

### Secondary: Fix Validation
- [ ] Can predict offset for any rotation combination
- [ ] Can implement fix that eliminates offset
- [ ] Achieve >0.999 correlation

## Expected Outcomes

### If Rotation Hypothesis is TRUE:
- One or more tests will show clear rotation-related pattern
- We'll identify specific rotation issue (order, convention, etc.)
- Fix will be straightforward (change order, transpose matrix, etc.)

### If Rotation Hypothesis is FALSE:
- All rotation tests will show consistent behavior
- Offset might appear even without rotations in some edge case
- Need to look elsewhere (unit conversions, coordinate origins, etc.)

## Risk Mitigation

### If Tests Are Inconclusive:
1. Add more granular tracing to C code
2. Use symbolic math to verify formulas
3. Consider numerical precision issues
4. Check for hidden transformations in C

### If Multiple Issues Found:
1. Fix one at a time
2. Verify each fix independently
3. Document all issues found
4. Create regression tests for each

## Execution Time Estimate

- Test implementation: 1 hour
- Test execution: 30 minutes  
- Analysis: 30 minutes
- Fix implementation (if confirmed): 30 minutes
- Total: 2.5 hours

## Decision Tree

```
Run isolation tests
├─> Single rotation causes offset
│   └─> Fix that specific rotation
├─> All rotations cause offset  
│   └─> Check rotation infrastructure
├─> Only combinations cause offset
│   └─> Fix rotation order/combination
└─> No clear pattern
    └─> Hypothesis is false, look elsewhere
```

---

**Important**: This is a systematic test plan to prove or disprove a hypothesis, not a fix implementation. We must gather evidence before concluding rotation logic is the actual cause.