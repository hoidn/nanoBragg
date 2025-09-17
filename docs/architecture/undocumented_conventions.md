# Undocumented Conventions Discovery Log

**Purpose**: Document conventions and behaviors discovered through debugging that were not in the original C code documentation.  
**Importance**: These undocumented behaviors cause significant debugging time if unknown.

## CUSTOM Convention (Discovered 2025-01-09)

### Discovery Context
- **Found During**: Phase 6 of detector geometry correlation debugging
- **Time Spent**: ~8 hours total debugging session
- **Impact**: Caused 4% vs 99.9% correlation issue

### The Undocumented Behavior

The C code (`nanoBragg.c`) automatically switches from MOSFLM to CUSTOM convention when the `-twotheta_axis` parameter is explicitly specified:

```c
// Pseudocode of the hidden logic (not explicitly documented):
if (twotheta_axis_specified_on_command_line) {
    convention = CUSTOM;  // Silently switches convention!
    // CUSTOM convention does NOT add the +0.5 pixel offset
} else {
    convention = MOSFLM;  // Default
    // MOSFLM convention adds +0.5 pixel offset to beam center
}
```

### Impact on Calculations

This convention switch affects beam center calculations:

| Convention | Beam Center Calculation | Example Result |
|------------|------------------------|----------------|
| MOSFLM (default) | `Fbeam = (Ybeam + 0.5*pixel_size)` | 51.25 mm |
| CUSTOM (when axis specified) | `Fbeam = Ybeam` | 51.2 mm |

The 0.5 pixel difference (~0.05 mm) compounds through the geometry calculations.

### How to Detect This

**Command that triggers CUSTOM**:
```bash
./nanoBragg ... -twotheta_axis 0 0 -1  # Explicitly sets axis → CUSTOM mode
```

**Command that keeps MOSFLM**:
```bash
./nanoBragg ... -detector_twotheta 20   # No explicit axis → MOSFLM mode
```

### PyTorch Implementation Note

The PyTorch implementation must replicate this behavior for C-code parity:
```python
if config.twotheta_axis is not None:
    # User explicitly set axis - use CUSTOM convention
    use_pixel_offset = False
else:
    # Using default axis - use MOSFLM convention
    use_pixel_offset = True
```

---

## Beam Center Logging Bug (Discovered 2025-01-09)

### Location
File: `nanoBragg.c`, Line: 1806

### The Bug
```c
// BUG: Double-converts meters to meters
printf("TRACE_C:beam_center_m=X:%.15g Y:%.15g pixel_mm:%.15g\n",
       Xbeam/1000.0, Ybeam/1000.0, pixel_mm);
//     ^^^^^^^^^^^^  ^^^^^^^^^^^^
//     Problem: Xbeam and Ybeam are already in meters!
```

### Impact
- **Logged value**: `5.125e-05` (incorrect - divided by 1000 twice)
- **Actual value**: `0.05125` (correct in calculation)
- **Debugging impact**: Sent investigators down wrong path for hours

### Workaround
Ignore the logged `beam_center_m` value in traces. Instead, check `Fclose` and `Sclose` values which are correctly logged.

---

## Basis Vector Calculation Divergence (Discovered 2025-01-09)

### Discovery Context
- **Found During**: Phase 6, after fixing pivot mode and beam center issues
- **Remaining Issue**: 39mm difference in pix0_vector for tilted configurations

### The Issue
When rotations are applied (rotx=5°, roty=3°, rotz=2°, twotheta=20°), C and Python produce different basis vectors:

```
Python pix0_vector: [0.109814, 0.022698, -0.051758] m
C pix0_vector:      [0.095234, 0.058827, -0.051702] m
Difference:         39mm (destroys correlation)
```

### Status
- **Not Yet Resolved**: Root cause still under investigation
- **Impact**: Prevents achieving >99.9% correlation for tilted detectors
- **Next Steps**: Deep comparison of rotation matrix construction and application

---

## Pivot Mode Auto-Selection (Partially Documented)

### The Implicit Rules
While some pivot mode logic is documented, the complete set of rules was discovered through testing:

| Condition | Resulting Pivot Mode | Documentation Status |
|-----------|---------------------|---------------------|
| `-distance` only | BEAM | ✅ Documented |
| `-detector_twotheta` ≠ 0 | SAMPLE | ⚠️ Partially documented |
| `-Xclose` or `-Yclose` set | SAMPLE | ❌ Not documented |
| `-ORGX` or `-ORGY` set | SAMPLE | ❌ Not documented |
| Convention = XDS | SAMPLE | ❌ Not documented |
| `-detector_pivot` explicit | As specified | ✅ Documented |

### Implementation Note
The c_reference_utils.py must implement these rules:
```python
def determine_pivot_mode(config):
    if config.detector_twotheta_deg != 0:
        return "sample"
    if config.Xclose is not None or config.Yclose is not None:
        return "sample"
    if config.convention == "XDS":
        return "sample"
    return "beam"  # Default
```

---

## C Trace Output Units (Discovered Through Testing)

### Not Explicitly Documented Units

| Trace Variable | Unit | Example | Discovery Method |
|---------------|------|---------|------------------|
| `DETECTOR_PIX0_VECTOR` | meters | `0.1 0.0257 -0.0257` | Value analysis |
| `pixel_pos_meters` | meters | `0.095 -0.031 -0.005` | Variable name + testing |
| `Fclose`/`Sclose` | meters | `0.05125` | Comparison with calculations |
| `beam_center_m`* | meters | `5.125e-05` | *Has logging bug |
| `detector_thick` | millimeters | `0.0` | Default value analysis |

### Discovery Process
These units were determined through:
1. Comparing trace values with known inputs
2. Analyzing variable names
3. Testing with different input scales
4. Cross-referencing with PyTorch outputs

---

## Lessons Learned

### Time Cost of Undocumented Behaviors
- **CUSTOM convention discovery**: ~3 hours
- **Beam center logging bug confusion**: ~2 hours
- **Basis vector divergence**: ~2 hours (ongoing)
- **Total debugging time**: ~8 hours

### Prevention Strategies
1. **Always instrument C code** when debugging geometry
2. **Don't trust logged values** - verify with calculations
3. **Test with and without** explicit parameters
4. **Document discoveries immediately** in this file

### Future Investigation Needed
1. Complete understanding of basis vector rotation differences
2. Document any preprocessor-dependent behaviors
3. Catalog all implicit parameter interactions

---

**Last Updated**: January 9, 2025  
**Contributors**: Debugging session findings  
**Time Saved for Future Developers**: 4-8 hours per issue