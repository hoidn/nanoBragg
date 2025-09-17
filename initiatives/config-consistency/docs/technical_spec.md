# Technical Specification - Configuration Consistency Initiative

## Overview

This specification defines the technical implementation of the three-layer configuration consistency system to prevent mode mismatch issues between C and PyTorch implementations.

## Design Principles

1. **Minimal Intrusion**: Changes should be additive, not modify existing behavior
2. **Zero False Positives**: Only flag actual mismatches, not implementation differences
3. **Immediate Visibility**: Problems should be obvious within 5 seconds
4. **Backward Compatible**: Existing scripts continue to work

## Layer 1: Configuration Echo Specification

### Output Format

Both implementations MUST output the following lines to stdout:

```
CONFIG_MODE: <mode_name>
CONFIG_TRIGGER: <trigger_description>
CONFIG_HASH: <8_char_hex>
```

### Field Definitions

#### CONFIG_MODE
- **Type**: String
- **Values**: "MOSFLM" | "CUSTOM" | "XDS" | "UNKNOWN"
- **Required**: Yes
- **Description**: Active configuration mode/convention

#### CONFIG_TRIGGER
- **Type**: String
- **Format**: Human-readable description
- **Required**: Yes
- **Examples**:
  - "default"
  - "twotheta_axis parameter"
  - "fdet_vector parameter"
  - "explicit mode setting"

#### CONFIG_HASH
- **Type**: Hexadecimal string
- **Length**: 8 characters
- **Required**: Yes
- **Calculation**: Hash of critical parameters that affect behavior
- **Must Include**:
  - Beam center values (Fbeam, Sbeam)
  - Distance
  - Active mode
  - Pixel size

### Implementation Requirements

1. **Timing**: Output after all configuration processing, before computation
2. **Stream**: Standard output (stdout)
3. **Conditional**: Always output in normal mode, suppress only with --quiet flag
4. **Order**: Must appear before any computation output

## Layer 2: Critical Test Specification

### Test Requirements

#### Primary Test: Explicit Defaults Equal Implicit

**Test ID**: `test_explicit_defaults_equal_implicit`

**Purpose**: Verify that explicitly passing default values doesn't change behavior

**Implementation**:
```python
def test_explicit_defaults_equal_implicit():
    # Step 1: Run with no parameters (implicit defaults)
    implicit_result = run_with_config({})
    
    # Step 2: Run with explicit default values
    explicit_result = run_with_config({
        "twotheta_axis": [0, 0, -1],  # MOSFLM default
        "detector_rotx_deg": 0.0,
        "detector_roty_deg": 0.0,
        # ... all other defaults
    })
    
    # Step 3: Verify identical behavior
    assert implicit_result.mode == explicit_result.mode
    assert implicit_result.hash == explicit_result.hash
```

**Pass Criteria**:
- Mode must be identical
- Configuration hash must be identical
- No warnings about mode changes

**Failure Handling**:
- Clear error message indicating which parameter caused mode change
- Suggestion for fix

### Secondary Tests

#### Test: All Parameters Default Equivalence
- Test each parameter individually with its default value
- Verify none trigger mode changes

#### Test: Mode Detection Accuracy
- Verify we correctly identify active mode from output
- Test both MOSFLM and CUSTOM modes

### CI Integration

**Requirements**:
1. Run on every commit to main/master
2. Run on all pull requests
3. Block merge on failure
4. Generate clear failure reports

## Layer 3: Pre-Flight Warning Specification

### Check Algorithm

```python
def preflight_check(c_output, py_output):
    # Step 1: Extract configuration from both outputs
    c_config = extract_config(c_output)
    py_config = extract_config(py_output)
    
    # Step 2: Check for mode mismatch
    if c_config.mode != py_config.mode:
        return MismatchResult(
            severity="CRITICAL",
            message="Mode mismatch detected",
            c_mode=c_config.mode,
            py_mode=py_config.mode,
            recommendation="Check for -twotheta_axis parameter"
        )
    
    # Step 3: Check for hash mismatch (warning only)
    if c_config.hash != py_config.hash:
        return MismatchResult(
            severity="WARNING",
            message="Configuration differs but mode matches",
            details="Parameters may differ between implementations"
        )
    
    return SuccessResult()
```

### Integration Points

#### Verification Scripts
- Add check after both implementations run
- Before correlation calculation
- Display results prominently

#### Environment Variables
- `STRICT_MODE=1`: Fail on any mismatch
- `SUPPRESS_PREFLIGHT=1`: Skip checks (debugging only)
- `PREFLIGHT_VERBOSE=1`: Show detailed comparison

### Error Messages

#### Critical Mismatch
```
========================================================
⚠️  CONFIGURATION MISMATCH DETECTED!
========================================================
   C implementation is in CUSTOM mode
   PyTorch implementation is in MOSFLM mode
   
This WILL cause correlation failures!

Common causes:
  1. Test script passing -twotheta_axis
  2. Different default parameters
  
Quick fix:
  Remove -twotheta_axis from C command
  
See: docs/configuration_mismatch.md
========================================================
```

#### Warning
```
⚠️  Configuration Warning: Hashes differ
   Both implementations in MOSFLM mode
   But parameters may differ slightly
   Continue with caution
```

## Performance Requirements

1. **Detection Time**: < 5 seconds from run start
2. **Overhead**: < 1% additional runtime
3. **Memory**: Negligible (< 1KB for config storage)
4. **Output Size**: < 200 bytes additional output

## Testing Requirements

### Unit Tests
- Configuration extraction from output
- Hash calculation consistency
- Mode detection accuracy
- Mismatch detection

### Integration Tests
- End-to-end with real C and PyTorch
- CI pipeline integration
- Various configuration combinations
- False positive prevention

### Regression Tests
- Original nanoBragg issue scenario
- Known problematic configurations
- Edge cases (empty output, malformed config)

## Maintenance

### Monitoring
- Track frequency of mismatches in CI
- Log which parameters cause issues
- Measure time saved by early detection

### Updates
- Document any new mode triggers
- Update hash calculation if critical params change
- Maintain troubleshooting guide with new cases

## Security Considerations

- No sensitive information in configuration output
- Hashes are non-reversible
- No user data exposed

## Backward Compatibility

1. **Existing Scripts**: Continue to work without modification
2. **Output Parsing**: New lines don't break existing parsers
3. **Opt-in Strict Mode**: Failures only with STRICT_MODE=1
4. **Gradual Adoption**: Can be rolled out incrementally

## Success Metrics

1. **False Positive Rate**: 0% (no incorrect warnings)
2. **Detection Rate**: 100% of mode mismatches detected
3. **Time to Detection**: < 5 seconds
4. **Developer Satisfaction**: Reduce debugging time by >90%
5. **ROI**: 250:1 minimum (3.5 hours implementation vs months saved)