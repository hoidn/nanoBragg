# Common Pitfalls Section Template

## Purpose
This template provides a standardized way to document common mistakes and their prevention. Each pitfall should include detection methods and specific solutions.

## Template Format

### Pitfall Categories

#### 🚨 CRITICAL: Convention/Mode Switching
**Pattern**: Parameter appears innocent but changes core system behavior

#### ⚠️ HIGH: Unit System Confusion  
**Pattern**: Same values, different units depending on context

#### 🔴 MODERATE: Parameter Interaction
**Pattern**: Parameters affect each other in unexpected ways

#### 🟡 LOW: Input Format Dependencies
**Pattern**: Same operation behaves differently based on input format

---

## Pitfall Template

### Pitfall N: [Descriptive Name]

**Risk Level**: 🚨 CRITICAL | ⚠️ HIGH | 🔴 MODERATE | 🟡 LOW

**What Goes Wrong**:
[Clear description of the mistake and its consequences]

**How It Manifests**:
- **Symptoms**: [Observable signs of this pitfall]
- **Error Magnitude**: [Quantified impact when possible]
- **Frequency**: [How often users hit this]

**Why It Happens**:
[Root cause - usually an assumption that seems reasonable but is wrong]

**Detection**:
```bash
# Commands to detect if you've hit this pitfall:
command_to_check | grep "indicator"
```

**Solution**:
```bash
# Correct approach:
correct_command --with --proper --flags

# What to avoid:
wrong_command --that --causes --problems
```

**Prevention**:
- [Checklist item 1]
- [Checklist item 2]  
- [Verification step]

**References**:
- Related documentation: [links]
- Debugging session where discovered: [link to issue]

---

## Real Examples from nanoBragg

### Pitfall 1: "Equivalent" Parameter Specification

**Risk Level**: 🚨 CRITICAL

**What Goes Wrong**:
Adding explicit parameter values that match system defaults changes behavior due to hidden convention switching.

**How It Manifests**:
- **Symptoms**: 5mm systematic offset in beam center calculations
- **Error Magnitude**: Exactly 0.5 * pixel_size_mm in beam positioning
- **Frequency**: ~80% of users hit this when trying to be "explicit"

**Why It Happens**:
Users assume that explicitly specifying a parameter with its default value is equivalent to not specifying it. In reality, the act of specification triggers a mode switch.

**Detection**:
```bash
# Check if convention switched unexpectedly:
./nanoBragg [params] | grep "custom convention selected"

# If you see "custom" but didn't intend it, you hit this pitfall
```

**Solution**:
```bash
# ✅ Correct: Let defaults apply
./nanoBragg -distance 100 -twotheta 20

# ❌ Wrong: Explicit "default" value
./nanoBragg -distance 100 -twotheta 20 -twotheta_axis 0 0 -1

# ✅ Correct: Explicit convention control if needed
./nanoBragg -convention MOSFLM -distance 100 -twotheta 20 -twotheta_axis 0 0 -1
```

**Prevention**:
- [ ] Never specify vector parameters unless you want CUSTOM convention
- [ ] Use -convention flag explicitly when specifying any vector parameter
- [ ] Test configurations both with and without explicit parameters
- [ ] Check "convention selected" output in logs

**References**:
- Hidden behavior documentation: `docs/debugging/CRITICAL_BEHAVIORS.md`
- Convention flowchart: `docs/debugging/convention_selection_flowchart.md`

---

### Pitfall 2: Unit System Assumption Errors

**Risk Level**: ⚠️ HIGH

**What Goes Wrong**:
Assuming all components use the same unit system leads to 10x or 100x errors in calculations.

**How It Manifests**:
- **Symptoms**: Positions off by factors of 10, 100, or 1000
- **Error Magnitude**: Exactly 10x, 100x, or 0.1x expected values
- **Frequency**: ~60% of new users hit this

**Why It Happens**:
The system uses a hybrid unit system where different components use different internal units (Angstroms vs meters vs mm).

**Detection**:
```bash
# Check if values are off by powers of 10:
python -c "print('Ratio:', actual_value / expected_value)"
# Common ratios: 10.0, 100.0, 1000.0, 0.1, 0.01, 0.001
```

**Solution**:
```python
# ✅ Correct: Check component documentation for internal units
detector_distance_m = config.distance_mm / 1000.0  # mm → meters
physics_distance_A = config.distance_mm * 10.0     # mm → Angstroms

# ❌ Wrong: Assuming units match between components  
distance = config.distance_mm  # Could be wrong units for target component
```

**Prevention**:
- [ ] Check component documentation for internal unit system before using
- [ ] Use explicit unit conversion functions at component boundaries
- [ ] Verify expected vs. actual value magnitudes in tests
- [ ] Include units in variable names when crossing boundaries

---

### Pitfall 3: Test Harness Configuration Mismatch

**Risk Level**: 🔴 MODERATE

**What Goes Wrong**:
Test harness builds command-line arguments differently than your manual testing, leading to false passes/failures.

**How It Manifests**:
- **Symptoms**: Manual commands work, automated tests fail (or vice versa)
- **Error Magnitude**: Complete correlation breakdown (>99% → <10%)
- **Frequency**: ~40% of test implementations

**Why It Happens**:
Test harness makes different assumptions about parameter formatting, defaults, or required flags than manual usage.

**Detection**:
```bash
# Compare exact commands being generated:
echo "Manual: $MANUAL_COMMAND"
echo "Test:   $TEST_GENERATED_COMMAND"
diff <(echo "$MANUAL_COMMAND" | tr ' ' '\n' | sort) \
     <(echo "$TEST_GENERATED_COMMAND" | tr ' ' '\n' | sort)
```

**Solution**:
```python
# ✅ Correct: Log exact command being executed
def run_c_reference(config):
    cmd = build_command(config)
    print(f"Executing: {' '.join(cmd)}")  # Critical for debugging
    result = subprocess.run(cmd, ...)
    return result

# ❌ Wrong: Silent command execution
def run_c_reference(config):
    cmd = build_command(config)
    return subprocess.run(cmd, ...)  # Can't debug when this fails
```

**Prevention**:
- [ ] Always log the exact command being executed in tests
- [ ] Manually verify generated commands work from command line
- [ ] Include parameter validation in test harness
- [ ] Test the test harness with known-good manual examples

---

### Pitfall 4: Pivot Mode Implicit Selection

**Risk Level**: 🔴 MODERATE

**What Goes Wrong**:
System selects wrong pivot mode based on parameter presence, not user intent.

**How It Manifests**:
- **Symptoms**: Zero or very low correlation with tilted detector configurations
- **Error Magnitude**: Complete geometry mismatch
- **Frequency**: ~50% of tilted detector use cases

**Why It Happens**:
Pivot mode is determined by parameter presence heuristics that don't match user expectations.

**Detection**:
```bash
# Check what pivot mode was selected:
./nanoBragg [params] | grep -i pivot

# For tilted detectors, should usually be "sample" pivot
```

**Solution**:
```python
# ✅ Correct: Explicit pivot mode specification
if abs(detector_config.detector_twotheta_deg) > 1e-6:
    cmd.extend(["-pivot", "sample"])

# ❌ Wrong: Relying on implicit selection
# (No explicit pivot specification)
```

**Prevention**:
- [ ] Always specify pivot mode explicitly for non-zero twotheta
- [ ] Understand the parameter → pivot mode mapping rules
- [ ] Test both BEAM and SAMPLE pivot modes when debugging geometry
- [ ] Verify pivot mode in test output logs

---

## Maintenance Guidelines

### Adding New Pitfalls

1. **Document Immediately**: As soon as a pitfall is discovered, document it
2. **Quantify Impact**: Include specific error magnitudes and time lost
3. **Provide Examples**: Real commands that demonstrate the problem
4. **Test Prevention**: Verify prevention steps actually work

### Pitfall Discovery Process

When you encounter unexpected behavior:

1. **Is it a new pitfall?**
   - [ ] Does it fit a pattern of user assumptions vs. reality?
   - [ ] Would documentation have prevented it?
   - [ ] Is it likely to affect other users?

2. **Document the pitfall**:
   - [ ] Use the template above
   - [ ] Include exact reproduction steps
   - [ ] Quantify the impact
   - [ ] Provide detection and prevention methods

3. **Update related documentation**:
   - [ ] Add to critical behaviors list
   - [ ] Update parameter documentation
   - [ ] Enhance test suite to catch this pitfall

### Review Schedule

- **Weekly**: Review recent issues for new pitfall patterns
- **Monthly**: Update frequency statistics based on user reports
- **Per Release**: Verify all documented pitfalls still apply to current version

---

**Last Updated**: [DATE]  
**Total Pitfalls Documented**: [COUNT]  
**Estimated Time Saved**: [Hours saved by documenting these pitfalls]
