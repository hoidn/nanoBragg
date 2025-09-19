# -twotheta_axis Parameter Documentation Template

## What This Parameter SHOULD Say

### Current (Inadequate) Documentation
```
-twotheta_axis x y z    Rotation axis for detector twotheta angle (default: convention-dependent)
```

### Improved Documentation

```
-twotheta_axis x y z    🚨 CRITICAL: Rotation axis for detector twotheta angle
                        
                        ⚠️  WARNING: Specifying this parameter has HIDDEN SIDE EFFECTS:
                        
                        AUTOMATIC BEHAVIOR CHANGE:
                        • Switches from MOSFLM/XDS convention to CUSTOM convention
                        • Removes +0.5 pixel offset from beam center calculations  
                        • Can cause 5mm systematic errors vs. reference implementations
                        
                        DEFAULTS (when parameter is NOT specified):
                        • MOSFLM convention: [0, 0, -1] (negative Z-axis)
                        • XDS convention: [1, 0, 0] (positive X-axis)
                        
                        SAFE USAGE:
                        • For standard workflows: DON'T specify this parameter
                        • For custom geometry: Use -convention CUSTOM explicitly
                        • For debugging: Compare with/without this parameter
                        
                        EXAMPLES:
                        # ✅ RECOMMENDED: Use convention defaults
                        ./nanoBragg -twotheta 20
                        
                        # ❌ DANGEROUS: Implicit convention switching  
                        ./nanoBragg -twotheta 20 -twotheta_axis 0 0 -1
                        
                        # ✅ SAFE: Explicit convention control
                        ./nanoBragg -convention CUSTOM -twotheta 20 -twotheta_axis 0 0 -1
                        
                        See: docs/critical_behaviors.md for detailed explanation
```

## Parameter Documentation Template

Use this template for ANY parameter that has hidden side effects:

### Parameter Name: `-parameter_name`

**Syntax**: `-parameter_name value1 [value2 ...]`

**Purpose**: [Brief description of primary function]

**🚨 CRITICAL SIDE EFFECTS**:
- **Hidden Behavior**: [Exact description of what happens automatically]
- **System Changes**: [List of systems/calculations that are affected]
- **Error Magnitude**: [Quantified impact - e.g., "5mm offset", "10% error"]

**Default Behavior** (when parameter is NOT specified):
- **Convention A**: [Default value and behavior]
- **Convention B**: [Default value and behavior]  
- **Context Dependency**: [When defaults change based on other parameters]

**Safe Usage Patterns**:
```bash
# ✅ RECOMMENDED: [Safest approach with explanation]
./executable [recommended_approach]

# ❌ AVOID: [Pattern that triggers hidden behavior]  
./executable [dangerous_pattern]

# ✅ EXPLICIT: [How to use safely when needed]
./executable [explicit_control_approach]
```

**Verification Commands**:
```bash
# Check what convention/mode was selected:
./executable [params] | grep [status_indicator]

# Compare with/without parameter:
diff <(./executable [base_params]) <(./executable [base_params] -parameter_name [value])
```

**Related Parameters**:
- `-related_param1`: [How they interact]
- `-related_param2`: [Interaction effects]

**Common Pitfalls**:
1. **Pitfall Name**: [Description and how to avoid]
2. **Migration Issues**: [Problems when adding this parameter to existing configs]

**References**:
- Source code: [file:line_numbers]
- Related documentation: [links]
- Debugging sessions: [where this was discovered]

---

## Examples of Well-Documented Parameters

### Example 1: Parameter with Mode Switching

```
-enable_feature          Enable advanced feature processing
                        
                        🚨 SIDE EFFECT: Changes memory allocation strategy
                        • Increases memory usage by ~200MB
                        • Enables different algorithm with different numerical precision
                        • May affect reproducibility vs. reference implementations
                        
                        DEFAULT: Disabled (uses standard algorithm)
                        
                        USAGE:
                        # Standard processing (recommended for validation):
                        ./tool input.dat
                        
                        # Advanced processing (for production):
                        ./tool -enable_feature input.dat
```

### Example 2: Parameter with Unit Dependencies

```
-scale_factor value      Scaling factor for output values
                        
                        🚨 UNIT DEPENDENCY: Effect depends on input format
                        • With .img files: Applied to raw pixel values
                        • With .mtz files: Applied after unit conversion  
                        • With .bin files: Applied before format conversion
                        
                        DEFAULT: 1.0 (no scaling)
                        RANGE: 0.001 to 1000.0
                        
                        EXAMPLES:
                        # Same scale factor, different effects:
                        ./tool -scale 10.0 data.img    # 10x raw pixels
                        ./tool -scale 10.0 data.mtz    # 10x after conversion
```

### Example 3: Parameter Order Dependency

```  
-param1 value1           First parameter in sensitive sequence
-param2 value2           Second parameter in sensitive sequence
                        
                        🚨 ORDER DEPENDENCY: param2 overwrites param1 calculations
                        
                        CORRECT ORDER:
                        ./tool -param1 val1 -param2 val2    # param1 applied first
                        
                        INCORRECT ORDER:  
                        ./tool -param2 val2 -param1 val1    # param2 gets overwritten
```

## Implementation Guidelines

### For Documentation Writers

1. **Lead with Danger**: Put warnings and side effects FIRST, not buried in details
2. **Quantify Impact**: Give specific error magnitudes, not vague warnings
3. **Provide Examples**: Show both correct and incorrect usage
4. **Cross-Reference**: Link to related docs and debugging resources

### For CLI Designers

```python
@click.option('--dangerous-param',
              help='Parameter description. '
                   'WARNING: This parameter has side effects. '
                   'See docs/critical_behaviors.md for details.')
def command(dangerous_param):
    if dangerous_param and not click.confirm(
        f'Using --dangerous-param will switch to CUSTOM mode. Continue?'
    ):
        raise click.Abort()
```

### For Test Writers

```python
def test_parameter_side_effects():
    """Test that hidden side effects are properly documented and controlled."""
    
    # Test default behavior
    result_default = run_tool([])
    assert result_default.convention == 'MOSFLM'
    
    # Test hidden side effect
    result_with_param = run_tool(['--twotheta-axis', '0', '0', '-1'])
    assert result_with_param.convention == 'CUSTOM'
    
    # Test explicit override
    result_explicit = run_tool([
        '--convention', 'MOSFLM',
        '--twotheta-axis', '0', '0', '-1'
    ])
    assert result_explicit.convention == 'MOSFLM'
```

---

**Maintenance**: Review parameter documentation whenever:
- Hidden behaviors are discovered
- Side effects change between versions  
- Common user errors are reported
- Test failures reveal documentation gaps

**Last Updated**: [DATE]  
**Template Version**: 1.0