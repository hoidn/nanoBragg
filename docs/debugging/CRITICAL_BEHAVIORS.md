# CRITICAL_BEHAVIORS.md Template

## Purpose
This file documents **hidden, undocumented, or non-obvious behaviors** that can cause major debugging issues. Every behavior listed here has caused significant developer time loss in the past.

## ⚠️ MANDATORY READING
**Before integrating with [SOFTWARE_NAME], read this entire document.** Each entry represents hours or days of debugging that future developers can avoid.

## Critical Behavior Inventory

### 1. [BEHAVIOR_NAME]: Hidden Convention Switching

**Risk Level**: 🔴 EXTREME (Months of debugging)

**What Happens**: 
- Setting `-parameter_name value` appears to just set a parameter
- **Hidden Effect**: Automatically switches entire system from Convention A to Convention B
- **Impact**: Convention B has completely different calculation rules (e.g., no +0.5 pixel offset)

**When It Triggers**:
```bash
# This looks innocent but triggers hidden behavior:
./executable -twotheta_axis 0 0 -1

# Expected: Uses MOSFLM convention with specified axis
# Reality: Switches to CUSTOM convention, removes +0.5 pixel offset
# Result: 5mm systematic error in beam center calculations
```

**Detection Signs**:
- Systematic offset in key measurements (exact magnitude: X mm)
- Perfect correlation for simple cases, complete failure for complex ones
- Error magnitude matches exactly 0.5 * pixel_size * some_scaling_factor

**Verification Commands**:
```bash
# Check what convention is actually being used:
./executable [params] | grep "convention selected"

# Compare with/without the problematic parameter:
diff <(./executable -param1 val1) <(./executable -param1 val1 -hidden_trigger val2)
```

**Workaround**:
```bash
# Force explicit convention if needed:
./executable -param1 val1 -convention explicit_name
```

---

### 2. [BEHAVIOR_NAME]: Parameter Order Dependency

**Risk Level**: 🟡 MODERATE (Days of debugging)

**What Happens**:
- Parameter order affects final behavior despite CLI parsers typically being order-independent
- Later parameters can override earlier ones in unexpected ways

**When It Triggers**:
```bash
# These produce different results:
./executable -param1 val1 -param2 val2
./executable -param2 val2 -param1 val1
```

**Detection Signs**:
- Identical parameter lists give different results when reordered
- Test harnesses fail when parameters are alphabetically sorted vs. original order

**Verification Commands**:
```bash
# Test parameter order sensitivity:
./test_param_order.sh param_file.txt
```

---

### 3. [BEHAVIOR_NAME]: Implicit Mode Selection

**Risk Level**: 🔴 HIGH (Weeks of debugging)

**What Happens**:
- Presence of certain parameters implicitly selects calculation mode
- Mode selection affects completely different parts of the system

**When It Triggers**:
```bash
# Setting distance implies MODE_A:
./executable -distance 100

# Setting angle implies MODE_B (even with same distance):
./executable -distance 100 -angle 20
```

**Detection Signs**:
- Same physical setup gives different results based on which parameters are specified
- Parameter combinations that should be equivalent produce different outputs

---

## Template for New Critical Behaviors

### X. [BEHAVIOR_NAME]: [Brief Description]

**Risk Level**: 🔴 EXTREME | 🟠 HIGH | 🟡 MODERATE | 🟢 LOW

**What Happens**: 
[Detailed description of the hidden behavior]

**When It Triggers**:
```bash
# Exact command or parameter combination that triggers it
```

**Detection Signs**:
- [Specific symptoms that indicate this behavior is active]
- [Quantitative measures if possible]

**Verification Commands**:
```bash
# Commands to verify this behavior is happening
```

**Workaround**:
```bash
# How to work around or explicitly control this behavior
```

**References**:
- [Source code location if known]
- [Documentation that should mention this but doesn't]
- [Issues or debugging sessions where this was discovered]

---

## Quick Reference Decision Tree

```
Start: Unexpected behavior detected
│
├─> Same inputs, different outputs?
│   └─> Check Parameter Order Dependency (#2)
│
├─> Simple cases work, complex cases fail?
│   └─> Check Hidden Convention Switching (#1)
│
├─> Adding parameters changes unrelated results?
│   └─> Check Implicit Mode Selection (#3)
│
└─> [Add more decision paths as behaviors are discovered]
```

## Maintenance Guidelines

### Adding New Critical Behaviors
1. **Immediate Documentation**: Document as soon as discovered, even before fixing
2. **Quantify Impact**: Include specific error magnitudes, time wasted
3. **Provide Examples**: Real command-line examples that reproduce the issue
4. **Reference Sources**: Link to code locations and debugging sessions

### Verification Schedule
- **Weekly**: Run verification commands for all EXTREME risk behaviors
- **Monthly**: Review and update detection signs based on recent issues
- **Per Release**: Verify all behaviors still trigger as documented

## Integration Checklist

Before integrating with [SOFTWARE_NAME], verify you understand:
- [ ] Hidden convention switching triggers and detection
- [ ] Parameter order sensitivity areas
- [ ] Implicit mode selection rules
- [ ] Verification commands for each critical behavior
- [ ] Workarounds for high-risk behaviors

---

**Last Updated**: [DATE]  
**Total Debugging Time Saved**: [Estimated hours saved by this documentation]  
**Contributors**: [Names of people who discovered these behaviors]