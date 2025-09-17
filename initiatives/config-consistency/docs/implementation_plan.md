# Configuration Consistency Initiative - Implementation Plan

## Phase 1: Layer 1 - Configuration Echo (Day 1)

**Objective**: Make configuration state visible in both implementations

### 1.1 C Implementation Changes

**File**: `golden_suite_generator/nanoBragg.c`

**Location**: After parameter parsing, before main computation (around line 1400)

**Implementation**:
```c
// Add after all parameter parsing is complete
void print_configuration_state() {
    // Determine active mode
    const char* mode = (beam_convention == MOSFLM) ? "MOSFLM" : "CUSTOM";
    
    // Determine what triggered the mode
    const char* trigger = "default";
    if (beam_convention == CUSTOM) {
        if (twotheta_axis_set) trigger = "twotheta_axis parameter";
        else if (fdet_vector_set) trigger = "fdet_vector parameter";
        else if (sdet_vector_set) trigger = "sdet_vector parameter";
        // ... check other triggers
    }
    
    // Calculate configuration hash (simple version)
    unsigned int hash = 0;
    hash ^= (unsigned int)(Fbeam * 1000000);
    hash ^= (unsigned int)(Sbeam * 1000000);
    hash ^= (unsigned int)(distance * 1000);
    hash ^= beam_convention;
    
    // Output configuration state
    printf("CONFIG_MODE: %s\n", mode);
    printf("CONFIG_TRIGGER: %s\n", trigger);
    printf("CONFIG_HASH: %08x\n", hash);
    
    if (verbose) {
        printf("CONFIG_IMPACTS: ");
        if (beam_convention == CUSTOM) {
            printf("no_pixel_offset,custom_beam_center");
        } else {
            printf("mosflm_pixel_offset,standard_beam_center");
        }
        printf("\n");
    }
}
```

**Integration Point**: Call after line ~1450 (after all parameters processed)

### 1.2 PyTorch Implementation Changes

**File**: `src/nanobrag_torch/models/detector.py`

**Location**: In `__init__` method, after configuration processing

**Implementation**:
```python
def _print_configuration_state(self):
    """Output configuration state for consistency checking"""
    
    # Determine mode and trigger
    mode = self.config.detector_convention.value  # "MOSFLM" or "CUSTOM"
    trigger = self._determine_trigger()
    
    # Calculate configuration hash
    import hashlib
    hash_input = f"{self.distance}_{self.pixel_size}_{self.beam_center_s}_{self.beam_center_f}_{mode}"
    config_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
    
    # Output configuration state
    print(f"CONFIG_MODE: {mode}")
    print(f"CONFIG_TRIGGER: {trigger}")
    print(f"CONFIG_HASH: {config_hash}")
    
    if self.config.verbose:
        impacts = self._get_mode_impacts()
        print(f"CONFIG_IMPACTS: {','.join(impacts)}")

def _determine_trigger(self):
    """Determine what triggered the current mode"""
    if hasattr(self.config, 'twotheta_axis') and self.config.twotheta_axis is not None:
        return "twotheta_axis parameter"
    elif hasattr(self.config, '_mode_override'):
        return self.config._mode_override
    return "default"

def _get_mode_impacts(self):
    """List behavioral impacts of current mode"""
    if self.config.detector_convention == DetectorConvention.MOSFLM:
        return ["mosflm_pixel_offset", "standard_beam_center"]
    else:
        return ["no_pixel_offset", "custom_beam_center"]
```

### 1.3 Validation

**Test Script**: `test_config_echo.py`
```python
def test_configuration_echo():
    """Verify both implementations output configuration state"""
    
    # Run C implementation
    c_output = run_c_reference(test_params)
    assert "CONFIG_MODE:" in c_output
    assert "CONFIG_TRIGGER:" in c_output
    assert "CONFIG_HASH:" in c_output
    
    # Run PyTorch implementation
    py_output = run_pytorch(test_params)
    assert "CONFIG_MODE:" in py_output
    assert "CONFIG_TRIGGER:" in py_output
    assert "CONFIG_HASH:" in py_output
```

---

## Phase 2: Layer 2 - Critical Test (Day 2)

**Objective**: Add test that would have caught the nanoBragg issue

### 2.1 Test Implementation

**File**: `tests/test_configuration_consistency.py`

**Implementation**:
```python
import pytest
import subprocess
from pathlib import Path
from nanobrag_torch.config import DetectorConfig
from scripts.c_reference_utils import build_nanobragg_command

class TestConfigurationConsistency:
    """Tests that prevent configuration mismatch bugs"""
    
    def test_explicit_defaults_equal_implicit(self):
        """
        THE CRITICAL TEST: Explicit defaults must behave like implicit defaults
        This single test would have prevented 3-6 months of debugging.
        """
        
        # Test case 1: No parameters (implicit defaults)
        implicit_cmd = build_nanobragg_command(
            DetectorConfig(),
            crystal_config,
            beam_config,
            matrix_file
        )
        implicit_output = subprocess.run(implicit_cmd, capture_output=True, text=True)
        implicit_mode = self.extract_mode(implicit_output.stdout)
        implicit_hash = self.extract_hash(implicit_output.stdout)
        
        # Test case 2: Explicit default for twotheta_axis
        explicit_config = DetectorConfig(twotheta_axis=[0, 0, -1])  # MOSFLM default
        explicit_cmd = build_nanobragg_command(
            explicit_config,
            crystal_config,
            beam_config,
            matrix_file
        )
        explicit_output = subprocess.run(explicit_cmd, capture_output=True, text=True)
        explicit_mode = self.extract_mode(explicit_output.stdout)
        explicit_hash = self.extract_hash(explicit_output.stdout)
        
        # THE ASSERTION THAT WOULD HAVE CAUGHT THE BUG
        assert implicit_mode == explicit_mode, \
            f"CRITICAL BUG: Explicit defaults change mode! " \
            f"Implicit={implicit_mode}, Explicit={explicit_mode}"
        
        # Also check configuration hasn't changed
        assert implicit_hash == explicit_hash, \
            f"Configuration changed with explicit defaults: " \
            f"{implicit_hash} != {explicit_hash}"
    
    def test_all_default_parameters(self):
        """Test that ALL explicit defaults behave like implicit"""
        
        parameters_to_test = [
            ("twotheta_axis", [0, 0, -1]),
            ("detector_rotx_deg", 0.0),
            ("detector_roty_deg", 0.0),
            ("detector_rotz_deg", 0.0),
            ("beam_center_s", 51.25),
            ("beam_center_f", 51.25),
        ]
        
        # Get baseline with no parameters
        baseline = self.run_with_config(DetectorConfig())
        
        for param_name, default_value in parameters_to_test:
            with self.subTest(parameter=param_name):
                config = DetectorConfig(**{param_name: default_value})
                result = self.run_with_config(config)
                
                assert result.mode == baseline.mode, \
                    f"Parameter {param_name} with default value {default_value} " \
                    f"changes mode from {baseline.mode} to {result.mode}"
    
    def extract_mode(self, output):
        """Extract CONFIG_MODE from output"""
        for line in output.split('\n'):
            if line.startswith('CONFIG_MODE:'):
                return line.split(':')[1].strip()
        raise ValueError("CONFIG_MODE not found in output")
    
    def extract_hash(self, output):
        """Extract CONFIG_HASH from output"""
        for line in output.split('\n'):
            if line.startswith('CONFIG_HASH:'):
                return line.split(':')[1].strip()
        raise ValueError("CONFIG_HASH not found in output")
```

### 2.2 CI Integration

**File**: `.github/workflows/config_consistency.yml` (or equivalent CI config)

```yaml
name: Configuration Consistency Tests

on: [push, pull_request]

jobs:
  config-consistency:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup environment
      run: |
        make -C golden_suite_generator
        pip install -e .
    
    - name: Run critical configuration tests
      run: |
        pytest tests/test_configuration_consistency.py -v
      env:
        STRICT_MODE: 1  # Fail on any configuration mismatch
    
    - name: Check for configuration mismatches
      if: failure()
      run: |
        echo "::error::Configuration consistency test failed!"
        echo "This likely means explicit defaults don't match implicit defaults."
        echo "Check if any parameters trigger unexpected mode changes."
```

---

## Phase 3: Layer 3 - Pre-Flight Warning (Day 3)

**Objective**: Add pre-flight checks to catch mismatches before they cause problems

### 3.1 Pre-Flight Check Implementation

**File**: `scripts/config_preflight.py`

```python
"""
Pre-flight configuration consistency checker
Prevents configuration mismatches between C and PyTorch implementations
"""

import sys
import re
from typing import Tuple, Optional

class ConfigurationPreFlight:
    """Minimal pre-flight check that saves months of debugging"""
    
    @staticmethod
    def extract_config_info(output: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract configuration information from output"""
        mode = None
        trigger = None
        hash_val = None
        
        for line in output.split('\n'):
            if line.startswith('CONFIG_MODE:'):
                mode = line.split(':', 1)[1].strip()
            elif line.startswith('CONFIG_TRIGGER:'):
                trigger = line.split(':', 1)[1].strip()
            elif line.startswith('CONFIG_HASH:'):
                hash_val = line.split(':', 1)[1].strip()
        
        return mode, trigger, hash_val
    
    @classmethod
    def check(cls, c_output: str, py_output: str, strict: bool = False) -> bool:
        """
        Check configuration consistency between implementations
        
        Args:
            c_output: Output from C implementation
            py_output: Output from PyTorch implementation
            strict: If True, raise exception on mismatch
            
        Returns:
            True if configurations match, False otherwise
        """
        
        c_mode, c_trigger, c_hash = cls.extract_config_info(c_output)
        py_mode, py_trigger, py_hash = cls.extract_config_info(py_output)
        
        # Check if we found configuration info
        if not (c_mode and py_mode):
            print("⚠️  Warning: Could not extract configuration information")
            print("   Make sure both implementations have CONFIG_MODE output")
            return not strict
        
        # Check for mismatch
        if c_mode != py_mode:
            print("\n" + "="*60)
            print("⚠️  CONFIGURATION MISMATCH DETECTED!")
            print("="*60)
            print(f"   C implementation is in {c_mode} mode")
            print(f"   PyTorch implementation is in {py_mode} mode")
            print(f"   C trigger: {c_trigger or 'unknown'}")
            print(f"   PyTorch trigger: {py_trigger or 'unknown'}")
            print("\nThis WILL cause correlation failures!")
            print("\nCommon causes:")
            print("  1. Test script passing -twotheta_axis (forces CUSTOM mode)")
            print("  2. Different default parameters between implementations")
            print("  3. Configuration not properly synchronized")
            print("\nQuick fix:")
            print("  - Remove -twotheta_axis from C command if using MOSFLM")
            print("  - Or set PyTorch to CUSTOM mode to match")
            print("\nSee: docs/configuration_mismatch.md for details")
            print("="*60 + "\n")
            
            if strict:
                raise ConfigurationMismatchError(
                    f"Configuration mismatch: C={c_mode}, PyTorch={py_mode}"
                )
            return False
        
        # Check hash for subtle differences
        if c_hash and py_hash and c_hash != py_hash:
            print(f"⚠️  Configuration hashes differ: C={c_hash}, PyTorch={py_hash}")
            print("   Configurations are in same mode but have different parameters")
        
        return True


class ConfigurationMismatchError(Exception):
    """Raised when C and PyTorch configurations don't match"""
    pass


def main():
    """Command-line interface for pre-flight check"""
    if len(sys.argv) != 3:
        print("Usage: python config_preflight.py <c_output_file> <py_output_file>")
        sys.exit(1)
    
    with open(sys.argv[1]) as f:
        c_output = f.read()
    
    with open(sys.argv[2]) as f:
        py_output = f.read()
    
    if ConfigurationPreFlight.check(c_output, py_output, strict=True):
        print("✅ Configuration check passed")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 3.2 Integration with Existing Scripts

**File**: `scripts/verify_detector_geometry.py` (modification)

Add after running both implementations:
```python
# After line ~300 where both implementations have run
from scripts.config_preflight import ConfigurationPreFlight

# Add pre-flight check
print("\n" + "="*60)
print("Configuration Consistency Check")
print("="*60)

if not ConfigurationPreFlight.check(c_output, pytorch_output, 
                                     strict=os.environ.get('STRICT_MODE')):
    print("\n⚠️  Continuing despite configuration mismatch...")
    print("   Set STRICT_MODE=1 to fail on mismatches")
```

---

## Phase 4: Documentation Updates (Day 4)

### 4.1 Update CLAUDE.md

**Location**: Add new section after current critical warnings

```markdown
## 🔍 Configuration Consistency Checking

As of [date], the project includes automatic configuration consistency checking:

### What This Means for You

1. **Both implementations now output their configuration**:
   - Look for `CONFIG_MODE:` in the output
   - `MOSFLM` vs `CUSTOM` mode is now visible

2. **Automatic mismatch detection**:
   - Pre-flight checks warn about mismatches
   - Set `STRICT_MODE=1` to fail fast on mismatches

3. **The critical test**:
   - `test_explicit_defaults_equal_implicit` ensures explicit defaults work
   - This prevents the class of bug that cost 3-6 months of debugging

### Quick Debugging

If you see a configuration mismatch warning:
```
⚠️  CONFIGURATION MISMATCH DETECTED!
   C implementation is in CUSTOM mode
   PyTorch implementation is in MOSFLM mode
```

**Immediate fix**:
1. Check if `-twotheta_axis` is being passed to C
2. Remove it if you want MOSFLM mode
3. Or explicitly set PyTorch to CUSTOM mode

### Manual Configuration Check

```bash
# Quick check for configuration consistency
grep "CONFIG_MODE" your_output.log
```

If C and PyTorch show different modes, you've found your problem.
```

### 4.2 Create Troubleshooting Guide

**File**: `docs/configuration_mismatch.md`

```markdown
# Configuration Mismatch Troubleshooting Guide

## Symptoms
- Correlation < 0.5 when it should be > 0.99
- Different results between C and PyTorch for same parameters
- Pre-flight check shows configuration mismatch

## Quick Diagnosis

Run this command:
```bash
grep "CONFIG_MODE" your_output.log
```

If you see different modes (e.g., MOSFLM vs CUSTOM), you have a configuration mismatch.

## Common Causes and Fixes

### 1. Test Script Adding Parameters

**Cause**: The test script adds `-twotheta_axis` which triggers CUSTOM mode in C

**Fix**: 
```python
# In c_reference_utils.py, around line 145
# Don't pass twotheta_axis for MOSFLM default
if is_mosflm_default(axis):
    # Don't add to command
    pass
```

### 2. Explicit Defaults Changing Behavior

**Cause**: Passing `-twotheta_axis 0 0 -1` (the default) triggers CUSTOM mode

**Fix**: Don't pass parameters with default values

### 3. Convention Not Synchronized

**Cause**: C and PyTorch using different conventions

**Fix**: Explicitly set both to same convention

## Prevention

1. Always check CONFIG_MODE in output
2. Run configuration consistency tests
3. Use STRICT_MODE=1 in CI

## Historical Context

This issue caused 3-6 months of debugging in early 2025. The configuration consistency system was added to prevent recurrence.
```

---

## Phase 5: Testing and Validation (Day 5)

### 5.1 Validation Tests

**File**: `tests/test_initiative_validation.py`

```python
def test_config_echo_present():
    """Verify configuration echo is implemented"""
    # Test C implementation
    c_output = run_c_with_params(standard_params)
    assert "CONFIG_MODE:" in c_output
    
    # Test PyTorch implementation
    py_output = run_pytorch_with_params(standard_params)
    assert "CONFIG_MODE:" in py_output

def test_mismatch_detection():
    """Verify mismatches are detected"""
    # Create intentional mismatch
    c_output = "CONFIG_MODE: CUSTOM\n"
    py_output = "CONFIG_MODE: MOSFLM\n"
    
    # Should detect mismatch
    assert not ConfigurationPreFlight.check(c_output, py_output)

def test_explicit_defaults():
    """Verify explicit defaults test exists and passes"""
    result = pytest.main([
        'tests/test_configuration_consistency.py::TestConfigurationConsistency::test_explicit_defaults_equal_implicit',
        '-v'
    ])
    assert result == 0

def test_preflight_integration():
    """Verify pre-flight check is integrated"""
    # Run verification script
    result = subprocess.run(
        ['python', 'scripts/verify_detector_geometry.py'],
        capture_output=True,
        text=True,
        env={**os.environ, 'STRICT_MODE': '1'}
    )
    
    # Should see configuration check
    assert "Configuration Consistency Check" in result.stdout
```

### 5.2 Success Metrics Validation

```python
def validate_success_metrics():
    """Verify all success metrics are met"""
    
    metrics = {
        "detection_time": measure_detection_time(),  # Should be < 5 seconds
        "false_positives": count_false_positives(),   # Should be 0
        "test_coverage": check_test_coverage(),       # Should catch explicit/implicit
        "documentation": check_documentation(),       # Should be updated
    }
    
    assert metrics["detection_time"] < 5.0
    assert metrics["false_positives"] == 0
    assert metrics["test_coverage"] == True
    assert metrics["documentation"] == True
    
    print(f"✅ All success metrics met!")
    print(f"   Detection time: {metrics['detection_time']}s")
    print(f"   False positives: {metrics['false_positives']}")
    print(f"   ROI: 250:1 to 500:1 (3.5 hours vs 3-6 months)")
```

---

## Rollout Plan

### Day 1: Layer 1 Implementation
- [ ] Morning: Implement C configuration echo
- [ ] Afternoon: Implement PyTorch configuration echo
- [ ] End of day: Verify both work

### Day 2: Layer 2 Implementation
- [ ] Morning: Write critical test
- [ ] Afternoon: Add additional default tests
- [ ] End of day: Integrate with CI

### Day 3: Layer 3 Implementation
- [ ] Morning: Implement pre-flight check
- [ ] Afternoon: Integrate with verification scripts
- [ ] End of day: Test end-to-end

### Day 4: Documentation
- [ ] Morning: Update CLAUDE.md
- [ ] Afternoon: Create troubleshooting guide
- [ ] End of day: Review and polish

### Day 5: Validation
- [ ] Morning: Run all validation tests
- [ ] Afternoon: Fix any issues found
- [ ] End of day: Sign-off and merge