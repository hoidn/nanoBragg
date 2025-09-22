# Behavioral Discovery Checklist

## Purpose
This checklist helps systematically discover hidden behaviors in new codebases BEFORE they cause debugging nightmares. Follow this checklist when working with any legacy or poorly-documented codebase.

## ⏱️ Time Investment
- **Upfront Cost**: 4-8 hours of systematic exploration
- **Savings**: Prevents weeks/months of debugging hidden behaviors later
- **ROI**: Typically 5:1 to 20:1 time savings

## Phase 1: Static Code Analysis (1-2 hours)

### 1.1 Find Hidden State Changes
- [ ] **Search for mode/convention variables**:
  ```bash
  grep -r "mode\|convention\|state" --include="*.c" --include="*.h"
  grep -r "enum.*{" --include="*.c" --include="*.h"
  ```
- [ ] **Find variable assignments in parameter parsing**:
  ```bash
  grep -A5 -B5 "argc.*argv" source_file.c
  grep -A10 "if.*strstr.*argv" source_file.c
  ```
- [ ] **Look for assignments triggered by parameter presence**:
  ```bash
  grep -A3 "argv.*=" source_file.c
  grep -A3 "strstr.*argv.*=" source_file.c
  ```

### 1.2 Identify Implicit Logic Patterns
- [ ] **Find default value assignments**:
  ```bash
  grep -r "default.*=" --include="*.c"
  grep -r "if.*isnan.*=" source_file.c  # NaN checks often indicate implicit defaults
  ```
- [ ] **Look for parameter interdependencies**:
  ```bash
  grep -A5 -B5 "if.*&&.*if" source_file.c  # Complex conditions
  grep -A5 "else.*if.*=" source_file.c     # Cascading assignments
  ```
- [ ] **Check for global variable modifications**:
  ```bash
  grep -n "^[a-zA-Z_][a-zA-Z0-9_]*.*=" source_file.c | head -20
  ```

### 1.3 Document Initial Findings
- [ ] **Create a list of suspicious patterns**:
  - Parameters that trigger assignments to unrelated variables
  - Global variables that get modified during parsing
  - Enum/mode variables that change based on parameter presence
  - Functions called conditionally during parameter processing

## Phase 2: Parameter Behavior Testing (2-3 hours)

### 2.1 Systematic Parameter Testing
- [ ] **List all command-line parameters**:
  ```bash
  ./executable --help 2>&1 || ./executable -h 2>&1 || strings executable | grep "^-"
  ```
- [ ] **Test minimal vs. explicit parameter sets**:
  ```bash
  # Minimal:
  ./executable -required_param1 value1
  
  # Explicit (add parameters that should be "equivalent" to defaults):
  ./executable -required_param1 value1 -optional_param default_value
  ```

### 2.2 Difference Detection
- [ ] **Compare outputs with/without each parameter**:
  ```bash
  ./executable -basic_params > output1.txt 2>&1
  ./executable -basic_params -extra_param default > output2.txt 2>&1
  diff output1.txt output2.txt
  ```
- [ ] **Check for "debug" or "verbose" output modes**:
  ```bash
  ./executable -debug 2>&1 | head -50
  ./executable -verbose 2>&1 | head -50  
  ./executable [params] 2>&1 | grep -i "mode\|convention\|selected"
  ```

### 2.3 Parameter Order Testing
- [ ] **Test parameter order sensitivity**:
  ```bash
  ./executable -param1 val1 -param2 val2 > order1.txt
  ./executable -param2 val2 -param1 val1 > order2.txt
  diff order1.txt order2.txt
  ```

## Phase 3: Behavioral Pattern Recognition (1-2 hours)

### 3.1 Mode/Convention Detection
- [ ] **Look for mode announcement messages**:
  ```bash
  ./executable [various_params] 2>&1 | grep -i "mode\|convention\|selected\|using\|detected"
  ```
- [ ] **Test all permutations of key parameters**:
  ```bash
  # Create a test matrix of important parameter combinations
  for param in param1 param2 param3; do
    echo "Testing $param..."
    ./executable -basic_params -$param test_value 2>&1 | grep -i convention
  done
  ```

### 3.2 Numerical Output Analysis
- [ ] **Look for systematic differences in numerical output**:
  ```python
  # Compare output arrays/files for patterns
  import numpy as np
  
  output1 = load_output("minimal_params.dat") 
  output2 = load_output("explicit_params.dat")
  
  # Check for systematic offsets
  diff = output2 - output1
  print(f"Mean difference: {np.mean(diff)}")
  print(f"Systematic offset: {np.std(diff) < 1e-10}")  # Nearly constant diff
  ```

### 3.3 Configuration State Inspection
- [ ] **Check if executable dumps internal state**:
  ```bash
  # Look for debugging flags that show internal configuration
  ./executable -debug -dump_config [other_params] 2>&1
  ./executable -show_config [other_params] 2>&1
  strings executable | grep -i debug
  ```

## Phase 4: Documentation of Findings (30 minutes)

### 4.1 Create Behavior Documentation
- [ ] **Document each hidden behavior found**:
  - Parameter that triggers it
  - What changes in system state
  - How to detect it
  - Quantified impact on output

- [ ] **Use the Critical Behaviors template**:
  ```markdown
  ### Hidden Behavior: [Name]
  **Trigger**: -parameter_name value
  **Effect**: Changes [system_component] from [mode_A] to [mode_B]
  **Detection**: Look for "[detection_string]" in output
  **Impact**: [quantified_difference] in output values
  ```

### 4.2 Create Test Cases
- [ ] **Write regression tests for each hidden behavior**:
  ```bash
  # Test that hidden behavior still triggers as expected
  test_hidden_behavior_1() {
    output=$(./executable -trigger_param value 2>&1)
    echo "$output" | grep -q "expected_mode_switch_message"
  }
  ```

## Phase 5: Integration with Development Workflow (30 minutes)

### 5.1 Update Project Documentation
- [ ] **Add to project README/docs**:
  - Link to CRITICAL_BEHAVIORS.md
  - Reference behavioral discovery findings
  - Warn about parameter order sensitivity

### 5.2 Enhance Testing Infrastructure
- [ ] **Add hidden behavior checks to test suite**:
  ```python
  def test_no_unexpected_mode_switches():
      """Verify that adding 'equivalent' parameters doesn't change behavior."""
      minimal_output = run_executable(minimal_params)
      explicit_output = run_executable(minimal_params + default_explicit_params)
      assert_outputs_equivalent(minimal_output, explicit_output)
  ```

## Red Flags: Stop and Investigate Immediately

If you see any of these patterns, there are likely hidden behaviors:

🚨 **CRITICAL RED FLAGS**:
- [ ] Different output for same physical setup but different parameter specification
- [ ] Global variables assigned during parameter parsing  
- [ ] Parameter presence (not value) affects unrelated calculations
- [ ] Messages like "detected mode", "switching convention", "using [X] method"

🔍 **INVESTIGATION TRIGGERS**:
- [ ] Parameter order affects output
- [ ] Adding "equivalent" explicit parameters changes results
- [ ] Simple cases work, complex cases fail dramatically
- [ ] Systematic numerical offsets that match physical constants (e.g., 0.5 pixels)

## Checklist Completion

### Before Proceeding with Development:
- [ ] All major parameters tested for hidden side effects
- [ ] Mode/convention switching behaviors documented
- [ ] Parameter order sensitivity identified
- [ ] Numerical output consistency verified
- [ ] Critical behaviors added to project documentation
- [ ] Test suite updated to catch behavioral regressions

### Time Tracking:
- **Start Time**: ________
- **Phase 1 Completion**: ________ (Target: +1-2 hours)
- **Phase 2 Completion**: ________ (Target: +2-3 hours)  
- **Phase 3 Completion**: ________ (Target: +1-2 hours)
- **Phase 4 Completion**: ________ (Target: +30 minutes)
- **Total Time**: ________ (Target: 4-8 hours)

### Findings Summary:
- **Hidden behaviors discovered**: _______
- **Critical parameters identified**: _______
- **Mode switches documented**: _______
- **Estimated debugging time saved**: _______ hours

---

**Usage Notes**:
- Use this checklist for ANY legacy codebase integration
- Update checklist based on new patterns discovered
- Share findings with team to prevent duplicate discovery work
- Consider this time as "debugging debt prevention" investment

**Last Updated**: [DATE]  
**Checklist Version**: 1.0  
**Tested On**: nanoBragg.c (prevented 3-6 month debugging cycle)