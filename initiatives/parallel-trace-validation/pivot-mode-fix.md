# Sub-Initiative: Pivot Mode Configuration Fix

**Parent Initiative**: Parallel Trace Validation  
**Issue**: C code requires explicit `-pivot sample` parameter when twotheta≠0  
**Impact**: Causes 0.040 correlation vs target >0.999  
**Estimated Time**: 1-2 hours  
**Priority**: CRITICAL - Blocking detector geometry validation  

## Problem Statement

Through parallel trace debugging, we discovered that the C reference implementation does not automatically switch to SAMPLE pivot mode when `twotheta != 0`, while the Python implementation does. This configuration mismatch causes:

1. Different detector geometries between implementations
2. C code produces physically meaningless results (zero scattering vectors)
3. Correlation of 0.040 instead of >0.999

## Root Cause Analysis

### Evidence from Traces
```
C trace output: "pivoting detector around direct beam spot" (BEAM mode)
Python behavior: Automatically uses SAMPLE pivot when twotheta=20°

Result:
- C pixel (512,512): (0.1, 0, 0) meters - wrong
- Python pixel (512,512): (0.095, -0.031, -0.005) meters - correct
```

### The Configuration Gap
- **C behavior**: Requires explicit `-pivot sample` parameter
- **Python behavior**: Auto-selects SAMPLE when `detector_twotheta_deg != 0`
- **Current code**: `c_reference_utils.py` doesn't add `-pivot sample`

## Solution Design

### Approach: Fix Parameter Generation Layer

**Rationale**: 
- Don't modify C code (it's the reference implementation)
- Don't modify Python auto-selection (it's a good feature)
- Fix the translation layer that generates C commands

### Implementation Strategy

The fix is surgical and focused:

1. **Modify `scripts/c_reference_utils.py`**:
   ```python
   # In generate_command() or equivalent:
   if abs(config.detector_twotheta_deg) > 1e-6:
       cmd.extend(["-pivot", "sample"])
   ```

2. **Update `scripts/c_reference_runner.py`** if needed to ensure pivot parameter is passed correctly

3. **No changes to core implementations** - This preserves both the C reference and Python behavior

## Implementation Plan

### Phase 1: Apply Configuration Fix (30 min)

#### 1.1 Locate parameter generation code
```bash
grep -n "twotheta" scripts/c_reference_utils.py
grep -n "pivot" scripts/c_reference_utils.py
```

#### 1.2 Add pivot mode logic
- Find where C command is built
- Add conditional: if twotheta != 0, add `-pivot sample`
- Ensure parameter order is correct

#### 1.3 Test command generation
```python
# Quick test script
from scripts.c_reference_utils import generate_command
config = DetectorConfig(detector_twotheta_deg=20.0)
cmd = generate_command(config)
assert "-pivot sample" in cmd
```

### Phase 2: Verify Fix (30 min)

#### 2.1 Run correlation test
```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/verify_detector_geometry.py
```
**Expected**: Correlation > 0.999 for tilted configuration

#### 2.2 Generate new parallel traces
```bash
# With fixed parameter generation
./run_c_trace.sh
python scripts/trace_pixel_512_512.py > py_trace_new.log
python scripts/compare_c_python_traces.py c_trace_new.log py_trace_new.log
```
**Expected**: Traces should match within tolerance

#### 2.3 Check pixel positions
- C pixel (512,512) should now be ~(0.095, -0.031, -0.005) meters
- Scattering vectors should be non-zero
- Both should report SAMPLE pivot mode

### Phase 3: Add Regression Tests (30 min)

#### 3.1 Create test for pivot mode selection
```python
# tests/test_pivot_mode_config.py
def test_twotheta_implies_sample_pivot():
    """Verify that non-zero twotheta triggers SAMPLE pivot in C commands."""
    config = DetectorConfig(detector_twotheta_deg=20.0)
    cmd = generate_c_command(config)
    assert "-pivot sample" in cmd
    
def test_zero_twotheta_uses_beam_pivot():
    """Verify that zero twotheta uses BEAM pivot (default)."""
    config = DetectorConfig(detector_twotheta_deg=0.0)
    cmd = generate_c_command(config)
    assert "-pivot sample" not in cmd
```

#### 3.2 Add integration test
```python
def test_tilted_detector_correlation():
    """Verify tilted detector achieves >0.999 correlation."""
    result = run_verification(tilted_config)
    assert result.correlation > 0.999
```

### Phase 4: Documentation Update (30 min)

#### 4.1 Update configuration map
File: `docs/development/c_to_pytorch_config_map.md`

Add section:
```markdown
## Critical Convention: Pivot Mode Auto-Selection

**Python Behavior**: Automatically selects SAMPLE pivot when detector_twotheta_deg != 0

**C Behavior**: Requires explicit `-pivot sample` parameter

**Resolution**: The c_reference_utils.py module automatically adds `-pivot sample` 
when generating C commands with non-zero twotheta to maintain behavioral parity.
```

#### 4.2 Update CLAUDE.md
Add to implementation rules:
```markdown
### Pivot Mode Convention
When detector_twotheta != 0:
- Python: Auto-selects SAMPLE pivot
- C: Requires explicit `-pivot sample` parameter
- Bridge: c_reference_utils.py handles this automatically
```

## Success Criteria

✅ **Primary**: Tilted detector correlation > 0.999  
✅ **Secondary**: All existing tests still pass  
✅ **Tertiary**: Parallel traces match within 1e-12 tolerance  

## Validation Checklist

- [ ] c_reference_utils.py adds `-pivot sample` when twotheta != 0
- [ ] verify_detector_geometry.py shows correlation > 0.999
- [ ] Parallel traces show matching pivot modes
- [ ] Pixel positions match between C and Python
- [ ] Regression tests pass
- [ ] Documentation updated

## Risk Assessment

**Risk Level**: LOW
- Surgical change to parameter generation only
- No modification to core implementations
- Easy to revert if needed
- Clear validation criteria

## Rollback Plan

If the fix causes issues:
1. Remove the pivot mode logic from c_reference_utils.py
2. Document that C and Python have different pivot conventions
3. Consider adding explicit pivot mode parameter to Python

## Timeline

- **Start**: Immediately after plan approval
- **Phase 1**: 30 minutes - Apply fix
- **Phase 2**: 30 minutes - Verify correlation
- **Phase 3**: 30 minutes - Add tests
- **Phase 4**: 30 minutes - Update docs
- **Total**: 2 hours maximum

## Next Steps After Success

1. Close the parallel-trace-validation initiative as successful
2. Run full test suite to ensure no regressions
3. Consider adding more detector configuration test cases
4. Document lessons learned about configuration debugging

---

**Ready to Execute**: This plan provides a focused, low-risk fix that should immediately resolve the correlation issue.