# Documentation Updates Plan

## Overview

Documentation updates required to support the Configuration Consistency Initiative and prevent future configuration mismatch issues.

## Priority 1: Critical User-Facing Documentation

### 1. CLAUDE.md Updates

**Location**: `/CLAUDE.md`

**Add at the top (line ~10)**:
```markdown
## 🚨 NEW: Configuration Consistency System (Added [DATE])

**Before debugging ANY correlation issue**, check for configuration mismatches:

```bash
grep "CONFIG_MODE" your_output.log
```

If C shows `CUSTOM` and PyTorch shows `MOSFLM` (or vice versa), you've found your problem. 
[Jump to fix](#configuration-mismatch-quick-fix)
```

**Add new section** (after existing warnings):
```markdown
## Configuration Mismatch Quick Fix

If you see this warning:
```
⚠️  CONFIGURATION MISMATCH DETECTED!
   C implementation is in CUSTOM mode
   PyTorch implementation is in MOSFLM mode
```

**Immediate fix**:
1. Remove `-twotheta_axis` from your C command
2. Or add `convention="CUSTOM"` to your PyTorch config

**Why this happens**: The C code switches to CUSTOM convention when certain parameters are present, even with default values. This system now detects and warns about these mismatches.

**Prevention**: Our tests now verify that explicit defaults equal implicit defaults, preventing this class of bug.
```

### 2. README.md Updates

**Location**: `/README.md`

**Add to Quick Start section**:
```markdown
### Configuration Consistency

This project includes automatic configuration consistency checking between C and PyTorch implementations:

- ✅ Both implementations output their active configuration (`CONFIG_MODE`)
- ✅ Automatic mismatch detection before correlation calculation
- ✅ Tests ensure explicit defaults behave like implicit defaults

If you encounter correlation issues, first check for configuration mismatches:
```bash
grep "CONFIG_MODE" output.log
```

See [Configuration Troubleshooting](docs/configuration_mismatch.md) for details.
```

## Priority 2: Debugging Documentation

### 3. Create Configuration Mismatch Guide

**New File**: `/docs/configuration_mismatch.md`

```markdown
# Configuration Mismatch Troubleshooting Guide

## Quick Check

```bash
# See what mode each implementation is using
grep "CONFIG_MODE" your_output.log
```

If they differ, you have a configuration mismatch.

## The 30-Second Fix

**Problem**: C shows `CUSTOM`, PyTorch shows `MOSFLM`

**Solution**: 
```python
# Option 1: Fix C command (remove the trigger)
# Remove: -twotheta_axis 0 0 -1
# This parameter forces CUSTOM mode even with default values

# Option 2: Match PyTorch to C
config = DetectorConfig(convention="CUSTOM")
```

## Why This Happens

The C implementation switches conventions based on parameter presence:
- `-twotheta_axis` → Forces CUSTOM convention
- `-fdet_vector` → Forces CUSTOM convention  
- `-sdet_vector` → Forces CUSTOM convention
- (and others)

Even passing default values triggers the switch!

## Historical Context

This issue caused 3-6 months of debugging in 2025 before the configuration consistency system was added. The system now:
1. Makes configurations visible (`CONFIG_MODE` output)
2. Detects mismatches automatically
3. Tests prevent the issue from recurring

## Common Scenarios

### Scenario 1: Test Script Adding Parameters
**Symptom**: Works manually, fails in test
**Cause**: Test script adds `-twotheta_axis`
**Fix**: Update `c_reference_utils.py` to not pass default values

### Scenario 2: Explicit Defaults
**Symptom**: Adding "harmless" parameters breaks correlation
**Cause**: Explicit defaults trigger mode switch
**Fix**: Don't pass parameters with default values

### Scenario 3: Copy-Pasted Commands
**Symptom**: Example command doesn't work
**Cause**: Example includes `-twotheta_axis`
**Fix**: Remove vector parameters unless needed

## Prevention

1. **Always check output for CONFIG_MODE**
2. **Run with STRICT_MODE=1 in CI**
3. **Don't pass default values explicitly**

## Need More Help?

If configuration is matched but correlation still poor:
1. Check basis vectors
2. Verify rotation order
3. See main debugging guide
```

### 4. Update Debugging Checklist

**File**: `/docs/debugging/detector_geometry_checklist.md`

**Add at the top**:
```markdown
## ⚡ Quick Check (Do This First!)

Before following this checklist, verify configuration consistency:

```bash
# Check if both implementations are in the same mode
grep "CONFIG_MODE" output.log
```

- If modes differ (MOSFLM vs CUSTOM), [fix that first](../configuration_mismatch.md)
- If modes match, continue with checklist below
```

## Priority 3: Developer Documentation

### 5. Update Development Guide

**File**: `/docs/development/testing_strategy.md`

**Add new section**:
```markdown
## Configuration Consistency Testing

### The Critical Test

We maintain a critical test that would have prevented months of debugging:

```python
def test_explicit_defaults_equal_implicit():
    """Explicit defaults must behave like implicit defaults"""
    implicit = run_with_no_params()
    explicit = run_with_default_params()
    assert implicit.mode == explicit.mode
```

This test MUST pass for any parameter changes.

### Adding New Parameters

When adding new parameters:
1. Ensure explicit default equals implicit behavior
2. Document any mode/convention triggers
3. Add to configuration consistency tests

### Pre-Flight Checks

All comparison scripts include pre-flight configuration checks:
- Automatic in normal mode (warnings)
- Strict in CI (failures)
- Suppressible for debugging only
```

### 6. Update Architecture Documentation

**File**: `/docs/architecture/detector.md`

**Add warning box**:
```markdown
⚠️ **Critical Convention Behavior**

The detector implementation has two conventions:
- **MOSFLM**: Default, includes +0.5 pixel offset
- **CUSTOM**: Triggered by vector parameters, no pixel offset

Vector parameters (`twotheta_axis`, `fdet_vector`, etc.) force CUSTOM convention in C code, even with default values. The PyTorch implementation must match the C convention for correct results.

Configuration consistency is now automatically checked - both implementations output `CONFIG_MODE` for verification.
```

## Priority 4: API Documentation

### 7. Update Config Documentation

**File**: `/src/nanobrag_torch/config.py` (docstrings)

```python
class DetectorConfig:
    """
    Detector configuration parameters.
    
    Warning:
        The C implementation switches to CUSTOM convention when certain
        parameters are specified (even with default values). The configuration
        consistency system will detect and warn about mismatches.
    
    Attributes:
        convention: Detector convention (MOSFLM/CUSTOM). Must match C implementation.
        twotheta_axis: Rotation axis. WARNING: Specifying this in C triggers CUSTOM mode.
    """
```

### 8. Update Test Documentation

**File**: `/tests/README.md`

**Add section**:
```markdown
## Configuration Consistency Tests

Critical tests that prevent configuration mismatches:

- `test_explicit_defaults_equal_implicit`: Ensures explicit defaults don't change behavior
- `test_configuration_echo`: Verifies both implementations output configuration
- `test_preflight_check`: Tests mismatch detection

These tests prevent the class of bug that caused 3-6 months of debugging.

### Running Configuration Tests

```bash
# Run only configuration consistency tests
pytest tests/test_configuration_consistency.py -v

# Run with strict mode (fail on any mismatch)
STRICT_MODE=1 pytest tests/
```
```

## Documentation Maintenance

### Update Triggers

Document updates needed when:
1. New parameters added that affect conventions
2. New mode/convention added
3. Configuration logic changes
4. New troubleshooting scenarios discovered

### Review Schedule

- **Monthly**: Review troubleshooting guide for new issues
- **Quarterly**: Update examples and scenarios
- **Annually**: Full documentation audit

## Success Metrics

Documentation is successful when:
1. Developers find configuration issues in < 5 minutes
2. No support tickets about configuration mismatches
3. New developers understand system from docs alone
4. CI catches configuration issues before merge

## Rollout Communication

### Announcement Template

```markdown
Subject: New Configuration Consistency System - Prevents Debugging Nightmares

Team,

We've added a configuration consistency system that prevents the type of issue that cost us 3-6 months of debugging.

What's New:
- Both C and PyTorch now output CONFIG_MODE
- Automatic mismatch detection
- Tests prevent explicit defaults from changing behavior

What You Need to Do:
1. Update to latest code
2. Check for CONFIG_MODE in output if debugging
3. Set STRICT_MODE=1 in your CI

This change is backward compatible but will save hours of debugging.

Details: [link to initiative]
```

## Documentation Testing

### Validation Checklist

- [ ] New developer can understand configuration system in 10 minutes
- [ ] Troubleshooting guide resolves issue in < 5 minutes  
- [ ] Examples are copy-pasteable and work
- [ ] No broken links or references
- [ ] Searchable keywords included (mismatch, correlation, CONFIG_MODE)