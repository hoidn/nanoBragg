# Debugging Decision Tree for Hidden Behavior Issues

## Purpose
This decision tree guides developers through systematic debugging when encountering unexpected behavior, particularly focusing on the types of hidden issues that caused the nanoBragg convention switching nightmare.

## Quick Start: Symptoms → Root Cause

### Use This Tree When You See:
- ✅ Same parameters, different results when specified differently
- ✅ Perfect correlation for simple cases, complete failure for complex cases  
- ✅ Systematic offsets that match physical constants (0.5 pixels, etc.)
- ✅ Manual commands work, automated tests fail (or vice versa)
- ✅ Parameter order affects output
- ✅ Adding "equivalent" parameters breaks existing functionality

---

## Decision Tree

```
🔍 START: Unexpected behavior detected
│
├─── 📊 Correlation Analysis
│    │
│    ├─> >99% correlation?
│    │   └─> ✅ No geometry issues → Look elsewhere (not this tree)
│    │
│    ├─> 90-99% correlation?
│    │   └─> 🟡 Minor issue → Check Section A: Unit System Issues
│    │
│    ├─> 10-90% correlation?
│    │   └─> 🟠 Moderate issue → Check Section B: Convention/Mode Issues
│    │
│    ├─> <10% correlation?
│    │   └─> 🔴 Major issue → Check Section C: System State Issues
│    │
│    └─> ~0% or negative correlation?
│        └─> 🚨 Fundamental issue → Check Section D: Coordinate System Issues

│
├─── 📈 Error Pattern Analysis  
│    │
│    ├─> Error exactly 10x, 100x, 0.1x expected?
│    │   └─> 🎯 Unit conversion error → Section A
│    │
│    ├─> Error ~0.5 * some_physical_constant?
│    │   └─> 🎯 Pixel offset / convention issue → Section B
│    │
│    ├─> Error systematic across all outputs?
│    │   └─> 🎯 Global mode switch → Section C
│    │
│    └─> Error pattern matches coordinate transformation?
│        └─> 🎯 Basis vector / coordinate issue → Section D
│
└─── 🔄 Behavioral Consistency Check
     │
     ├─> Manual vs automated results differ?
     │   └─> 🎯 Test harness issue → Section E
     │
     ├─> Parameter order affects output?
     │   └─> 🎯 Parsing dependency issue → Section F
     │
     └─> Adding explicit parameters breaks working case?
         └─> 🎯 Hidden trigger behavior → Section G (MOST COMMON)
```

---

## Section A: Unit System Issues (10-100x errors)

### Symptoms
- Values off by exact powers of 10 (10x, 100x, 1000x)
- Distance/position values seem way too large or small
- Physics calculations give impossible results

### Diagnosis Steps
1. **Check component documentation for internal units**:
   ```bash
   grep -r "internal.*unit\|meter\|angstrom" docs/
   ```

2. **Compare expected vs actual magnitudes**:
   ```python
   print(f"Expected: {expected_value}, Actual: {actual_value}")
   print(f"Ratio: {actual_value / expected_value}")
   # Look for ratios: 10.0, 100.0, 1000.0, 0.1, 0.01, 0.001
   ```

3. **Trace unit conversions**:
   ```python
   # Add logging at conversion points
   print(f"Input (mm): {input_mm}")
   print(f"Converted (m): {input_mm / 1000}")
   print(f"Internal (Å): {input_mm * 10}")
   ```

### Solutions
- [ ] Use explicit unit conversion functions
- [ ] Document unit expectations in function signatures
- [ ] Add unit tests with known physical magnitudes
- [ ] Include units in variable names at boundaries

---

## Section B: Convention/Mode Issues (~5mm systematic offsets)

### Symptoms  
- Systematic offset exactly matching pixel_size * 0.5
- Beam center calculations differ by small constant amount
- Error appears/disappears when changing conventions

### Diagnosis Steps
1. **Check what convention was actually selected**:
   ```bash
   ./executable [params] | grep -i "convention selected"
   ```

2. **Compare convention-sensitive calculations**:
   ```python
   # MOSFLM: beam_center + 0.5 * pixel_size
   # XDS: beam_center (no offset)
   # CUSTOM: varies
   ```

3. **Test with explicit convention control**:
   ```bash
   # Test all conventions explicitly
   ./executable -convention mosflm [params]
   ./executable -convention xds [params]  
   ./executable -convention custom [params]
   ```

### Solutions
- [ ] Always specify convention explicitly
- [ ] Check for vector parameters that trigger CUSTOM mode
- [ ] Verify convention defaults in documentation
- [ ] Use convention-aware test cases

---

## Section C: System State Issues (Complete mode changes)

### Symptoms
- Completely different algorithm behavior
- Parameter presence (not value) changes results
- Global system behavior switches

### Diagnosis Steps
1. **Find state variables that change**:
   ```bash
   grep -r "mode.*=\|convention.*=\|state.*=" source_code/
   ```

2. **Compare system state with/without parameters**:
   ```bash
   ./executable -debug [minimal_params] > state1.log
   ./executable -debug [minimal_params] -extra_param value > state2.log
   diff state1.log state2.log
   ```

3. **Check for global variable assignments during parsing**:
   ```c
   // Look for patterns like:
   if(strstr(argv[i], "-param")) {
       global_mode = DIFFERENT_MODE;  // Hidden state change!
   }
   ```

### Solutions
- [ ] Document all parameters that change system mode
- [ ] Use explicit mode selection parameters
- [ ] Validate system state after parameter parsing
- [ ] Create regression tests for mode consistency

---

## Section D: Coordinate System Issues (Reflection/inversion patterns)

### Symptoms
- Mirror image outputs
- Negative correlation coefficients
- 90° rotation in diff images
- Sign flips in coordinates

### Diagnosis Steps
1. **Check coordinate system handedness**:
   ```python
   # Test with simple known geometry
   test_vector = [1, 0, 0]
   result = transform(test_vector)
   print(f"X-axis maps to: {result}")
   ```

2. **Verify axis conventions**:
   ```bash
   # Check if fast/slow axes are swapped
   # Check if origin is top-left vs bottom-left
   ```

3. **Compare coordinate transforms step-by-step**:
   ```python
   # Log each transformation step
   print(f"Input: {input_coords}")
   print(f"After rotation: {rotated}")
   print(f"After translation: {final}")
   ```

### Solutions
- [ ] Use consistent coordinate system throughout
- [ ] Document axis conventions clearly
- [ ] Add coordinate system validation tests
- [ ] Use right-handed coordinate systems consistently

---

## Section E: Test Harness Issues (Manual vs automated differences)

### Symptoms
- Manual commands work, tests fail
- Different results for "identical" parameter sets
- Inconsistent behavior between test environments

### Diagnosis Steps
1. **Compare exact commands being generated**:
   ```bash
   echo "Manual command: $MANUAL_CMD"
   echo "Test command: $TEST_CMD"
   diff <(echo "$MANUAL_CMD" | tr ' ' '\n' | sort) \
        <(echo "$TEST_CMD" | tr ' ' '\n' | sort)
   ```

2. **Check parameter formatting differences**:
   ```python
   # Look for differences in:
   # - Floating point precision
   # - String vs numeric parameters  
   # - Path separators
   # - Working directory
   ```

3. **Validate test environment**:
   ```bash
   # Check if executables are the same version
   # Check if input files match
   # Check if environment variables differ
   ```

### Solutions
- [ ] Log exact commands in tests
- [ ] Validate generated commands against known working examples
- [ ] Use identical parameter formatting between manual and automated
- [ ] Include environment validation in test suite

---

## Section F: Parameter Order Dependencies

### Symptoms
- Different results when parameters are reordered
- Works with hand-crafted order, fails with alphabetical sort
- Later parameters override earlier ones unexpectedly

### Diagnosis Steps
1. **Test parameter order sensitivity**:
   ```bash
   ./executable -param1 val1 -param2 val2 > result1.txt
   ./executable -param2 val2 -param1 val1 > result2.txt  
   diff result1.txt result2.txt
   ```

2. **Find order-dependent parsing code**:
   ```c
   // Look for patterns like:
   for(i=0; i<argc; i++) {
       if(strstr(argv[i], "-param1")) {
           // This might depend on param2 being parsed first
       }
   }
   ```

### Solutions
- [ ] Use order-independent parameter parsing
- [ ] Document required parameter order if unavoidable
- [ ] Validate parameter combinations after all parsing is complete
- [ ] Use structured configuration objects instead of global variables

---

## Section G: Hidden Trigger Behaviors (MOST COMMON ISSUE)

### Symptoms
- Adding explicit parameters breaks working configurations
- "Equivalent" parameter specifications give different results
- Parameter presence triggers unexpected mode switches

### Diagnosis Steps
1. **Identify trigger parameters**:
   ```bash
   # Test each parameter individually
   for param in param1 param2 param3; do
     echo "Testing $param..."
     diff <(./executable -base_params) \
          <(./executable -base_params -$param default_value)
   done
   ```

2. **Check for automatic mode switches**:
   ```bash
   # Look for output like "switching to mode X" or "using convention Y"
   ./executable [params] 2>&1 | grep -i "mode\|convention\|switch\|using"
   ```

3. **Find the hidden trigger code**:
   ```c
   // Common pattern:
   if(strstr(argv[i], "-seemingly_innocent_param")) {
       hidden_mode = COMPLETELY_DIFFERENT_MODE;  // ← The problem!
   }
   ```

### Solutions
- [ ] **Document all hidden trigger behaviors in CRITICAL_BEHAVIORS.md**
- [ ] **Use explicit mode selection parameters**
- [ ] **Validate that explicit parameters match expected defaults**
- [ ] **Create regression tests for each hidden trigger**

**This is the section that would have prevented the nanoBragg months-long debugging nightmare!**

---

## Quick Reference: Emergency Debugging

### When Everything Fails (10-minute diagnosis)

```bash
# 1. Check for obvious hidden behaviors
./your_command 2>&1 | grep -i "convention\|mode\|switch\|using\|detect"

# 2. Test minimal vs explicit parameters
./your_command -minimal > minimal.out 2>&1
./your_command -minimal -explicit_defaults > explicit.out 2>&1
diff minimal.out explicit.out

# 3. Check parameter order sensitivity
./your_command -A val1 -B val2 > order1.out
./your_command -B val2 -A val1 > order2.out  
diff order1.out order2.out

# 4. Look for systematic numerical patterns
# Calculate ratios of unexpected vs expected values
# Look for: 10x, 100x, 0.1x (units), 0.5x (pixels), etc.
```

### Red Flag Patterns (Stop and investigate immediately)
- [ ] **"convention selected" message different than expected**
- [ ] **Parameters work individually but fail when combined**
- [ ] **Error magnitude exactly matches a physical constant**
- [ ] **Manual success, automated failure (or vice versa)**

---

## Decision Tree Maintenance

### When to Update This Tree
- New hidden behavior discovered → Add new section
- Common debugging pattern identified → Add quick reference
- Systematic error patterns found → Update symptom descriptions

### How to Validate the Tree
- Test decision tree with known issues from project history
- Verify each section leads to correct diagnosis
- Update based on actual debugging sessions

---

**Last Updated**: 2025-09-29  
**Validated Against**: nanoBragg convention switching issue (would have saved 3-6 months)  
**Usage Stats**: [Track how often each section is used to prioritize improvements]
