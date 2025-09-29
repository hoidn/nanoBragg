# Convention Selection Flowchart

## Purpose
This flowchart prevents the "hidden convention switching" nightmare by making explicit how conventions are determined.

## Convention Selection Logic

```mermaid
flowchart TD
    A[Start: Parse Command Line] --> B{Explicit -convention flag?}
    
    B -->|Yes| C[Use Specified Convention]
    B -->|No| D{Any vector parameters specified?}
    
    D -->|Yes| E[🚨 HIDDEN: Switch to CUSTOM]
    D -->|No| F{Check specific triggers}
    
    F --> G{-twotheta_axis specified?}
    G -->|Yes| E
    G -->|No| H{-fdet_vector specified?}
    H -->|Yes| E
    H -->|No| I{-sdet_vector specified?}
    I -->|Yes| E
    I -->|No| J{-odet_vector specified?}
    J -->|Yes| E
    J -->|No| K{-beam_vector specified?}
    K -->|Yes| E
    K -->|No| L{-polar_vector specified?}
    L -->|Yes| E
    L -->|No| M{-spindle_axis specified?}
    M -->|Yes| E
    M -->|No| N{-pix0_vector specified?}
    N -->|Yes| E
    N -->|No| O[Use Default Convention]
    
    O --> P{Legacy mode detection}
    P -->|ADXV mode| Q[Convention: ADXV]
    P -->|XDS mode| R[Convention: XDS]
    P -->|Default| S[Convention: MOSFLM]
    
    E --> T[Convention: CUSTOM<br/>⚠️ Removes +0.5 pixel offset]
    C --> U{Validate convention choice}
    
    U -->|MOSFLM| V[✅ MOSFLM: +0.5 pixel offset<br/>twotheta_axis: [0,0,-1]]
    U -->|XDS| W[✅ XDS: No +0.5 offset<br/>twotheta_axis: [1,0,0]]
    U -->|CUSTOM| T
    
    Q --> X[Output: Selected convention]
    R --> X
    S --> V
    T --> X
    V --> X
    W --> X
    
    style E fill:#ff9999
    style T fill:#ff9999
    style A fill:#e1f5fe
    style X fill:#c8e6c9
```

## Critical Decision Points

### 🚨 Hidden Trigger Warning

**ANY of these parameters automatically switch to CUSTOM convention:**
- `-twotheta_axis x y z`
- `-fdet_vector x y z`  
- `-sdet_vector x y z`
- `-odet_vector x y z`
- `-beam_vector x y z`
- `-polar_vector x y z`
- `-spindle_axis x y z`
- `-pix0_vector x y z`

**Impact of CUSTOM Convention:**
- ❌ **Removes +0.5 pixel offset** (MOSFLM has this offset)
- ❌ **Changes beam center calculation**
- ❌ **Different coordinate system assumptions**

### Safe Explicit Convention Setting

```bash
# ✅ SAFE: Explicitly specify convention
./nanoBragg -convention MOSFLM -twotheta_axis 0 0 -1

# ❌ DANGEROUS: Implicit convention switching
./nanoBragg -twotheta_axis 0 0 -1  # Automatically becomes CUSTOM!

# ✅ SAFE: Use defaults when possible  
./nanoBragg -twotheta 20  # Uses MOSFLM default axis [0,0,-1]
```

## Verification Commands

### Check What Convention Was Selected
```bash
# See what convention is active:
./nanoBragg [your_params] | grep "convention selected"

# Expected outputs:
# "mosflm convention selected."  ← Good for most cases
# "custom convention selected."  ← ⚠️ Check if intentional
```

### Test Convention Switching
```bash
# Test 1: Without vector parameters (should be MOSFLM)
./nanoBragg -distance 100 -twotheta 20 | grep convention

# Test 2: With vector parameters (will be CUSTOM)
./nanoBragg -distance 100 -twotheta 20 -twotheta_axis 0 0 -1 | grep convention

# These should show different conventions despite similar physics
```

## Implementation Requirements

### For CLI Tools
```python
def determine_convention(args):
    """Explicit convention determination with warnings."""
    
    # Check for explicit setting first
    if args.convention:
        return args.convention
    
    # Check for vector parameters that trigger CUSTOM
    vector_params = [
        'twotheta_axis', 'fdet_vector', 'sdet_vector', 
        'odet_vector', 'beam_vector', 'polar_vector',
        'spindle_axis', 'pix0_vector'
    ]
    
    for param in vector_params:
        if getattr(args, param, None) is not None:
            warnings.warn(
                f"Parameter '--{param}' automatically switches to CUSTOM convention. "
                f"This removes the +0.5 pixel offset. "
                f"Use '--convention MOSFLM' to override if needed."
            )
            return Convention.CUSTOM
    
    # Default behavior
    return Convention.MOSFLM
```

### For Test Harnesses
```python
def build_command(config):
    """Build command with explicit convention control."""
    cmd = [executable]
    
    # Always specify convention explicitly in tests
    cmd.extend(['--convention', config.convention.name])
    
    # Add other parameters
    if config.twotheta_axis is not None:
        cmd.extend(['--twotheta_axis'] + list(config.twotheta_axis))
        
    return cmd
```

## Common Pitfall Scenarios

### Scenario 1: "Equivalent" Parameter Sets
```bash
# User thinks these are equivalent:
./nanoBragg -twotheta 20                    # Uses MOSFLM default axis
./nanoBragg -twotheta 20 -twotheta_axis 0 0 -1  # Switches to CUSTOM!

# Result: 5mm beam center offset between the two
```

### Scenario 2: Testing Different Axes
```bash
# User wants to test different rotation axes:
./nanoBragg -twotheta_axis 0 0 -1   # CUSTOM convention
./nanoBragg -twotheta_axis 0 1 0    # CUSTOM convention  
./nanoBragg -twotheta_axis 1 0 0    # CUSTOM convention

# All use CUSTOM, but user expected to compare MOSFLM vs XDS conventions
```

### Scenario 3: Configuration Migration
```bash
# Legacy config works:
./nanoBragg -distance 100 -twotheta 20

# Adding "equivalent" explicit parameters breaks it:
./nanoBragg -distance 100 -twotheta 20 -twotheta_axis 0 0 -1
```

## Decision Tree for Developers

```
Question: Should I specify vector parameters explicitly?
│
├─> For testing/debugging specific geometry? 
│   └─> YES: Use -convention CUSTOM explicitly
│
├─> For production runs with standard conventions?
│   └─> NO: Let defaults apply (MOSFLM/XDS)  
│
├─> For validation against reference implementation?
│   └─> DEPENDS: Check what convention reference used
│
└─> Unsure?
    └─> SAFE: Always specify -convention explicitly
```

## Maintenance

### Add New Hidden Triggers
When you discover a new parameter that triggers CUSTOM convention:

1. **Update the flowchart** (add new decision diamond)
2. **Update the vector_params list** in code examples
3. **Add verification command** to test the new trigger
4. **Document the impact** of the convention switch

### Version Control
- Version this flowchart with software releases
- Include convention selection logic tests in CI/CD
- Validate flowchart accuracy against actual code behavior

---

**Last Updated**: 2025-09-29  
**Verified Against**: nanoBragg.c (golden_suite_generator) as of 2025-09-29  
**Critical Behaviors Documented**: 8 automatic CUSTOM triggers
