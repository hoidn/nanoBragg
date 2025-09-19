# Detector Geometry Debugging Checklist

**⚠️ MANDATORY READING**: Read this BEFORE debugging any detector correlation issues.  
**Time Saved**: Following this checklist can save 4-8 hours of debugging.

## Quick Diagnosis Table

| Symptom | Correlation | Likely Cause | Section |
|---------|------------|--------------|---------|
| Works without rotations, fails with | >99% → <10% | Convention switching or pivot mode | §3, §4 |
| Systematic offset in beam center | Any | MOSFLM +0.5 pixel adjustment | §2.1 |
| 10x or 100x position errors | Any | Unit confusion (mm/m/Å) | §1 |
| ~3-4cm offset in pixel positions | <10% | Basis vector calculation difference | §5 |
| Zero scattering vectors | ~0% | Wrong pivot mode (BEAM vs SAMPLE) | §3 |
| Reflection/inversion pattern | Negative | Coordinate system handedness | §2.3 |

## §1: Unit System (pointer)

Canonical unit rules and the detector’s hybrid exception are defined in `specs/spec-a.md` (Units & Conversions; Geometry & Conventions) and summarized in `docs/architecture/detector.md`. Refer there for detailed tables and examples.

## §2: Convention-Specific Behaviors (pointer)

Beam/detector conventions (MOSFLM/XDS), +0.5 pixel adjustments, axis mappings, and the CUSTOM switch are defined in `specs/spec-a.md` and elaborated in `docs/architecture/undocumented_conventions.md`. This checklist avoids restating those rules.

## §3: Pivot Mode Determination

### Implicit Rules (C Code Behavior)

The pivot mode is determined by command-line parameters:

| If You Set... | Pivot Mode | Why |
|--------------|------------|-----|
| `-distance` only | BEAM | Default behavior |
| `-detector_twotheta` ≠ 0 | SAMPLE | Twotheta implies sample pivot |
| `-Xclose`/`-Yclose` | SAMPLE | Close position → sample pivot |
| Convention = XDS | SAMPLE | XDS always uses sample pivot |

### Common Pivot Mode Bug

**Symptom**: Correlation ~0% with tilted detector  
**Cause**: C using BEAM pivot instead of SAMPLE  
**Fix**: Explicitly add `-pivot sample` when twotheta ≠ 0

```python
# In c_reference_utils.py
if abs(config.detector_twotheta_deg) > 1e-6:
    cmd.extend(["-pivot", "sample"])  # Force SAMPLE pivot
```

## §4: Rotation and Basis Vectors (pointer)

Rotation order, basis initializations, and known pitfalls are specified in `specs/spec-a.md` and `docs/architecture/detector.md`. Use the trace workflow below to validate your specific configuration.

## §5: Step-by-Step Debugging Process

### Phase 1: Check Configuration Parity
```python
# 1. Print what you're sending to C
print(f"C command: {' '.join(cmd)}")

# 2. Verify pivot mode
assert "-pivot sample" in cmd if twotheta != 0 else True

# 3. Check parameter format
# WRONG: -beam 51.2 51.2
# RIGHT: -Xbeam 51.2 -Ybeam 51.2
```

### Phase 2: Generate Parallel Traces
```bash
# C trace
./nanoBragg [params] 2>&1 | grep "TRACE_C:" > c_trace.log

# Python trace  
python scripts/trace_pixel_512_512.py > py_trace.log

# Compare
python scripts/compare_traces.py c_trace.log py_trace.log
```

### Phase 3: Check Key Values
```python
# 1. Beam center (should be ~0.05125 m for 51.2mm input)
assert abs(Fbeam - 0.05125) < 1e-6

# 2. pix0_vector (should match C within 1e-12)
assert torch.allclose(py_pix0, c_pix0, atol=1e-12)

# 3. Basis vectors (should be identical)
assert torch.allclose(py_fdet, c_fdet, atol=1e-12)
```

## §6: Known C Code Issues

### Logging Bug (Line 1806)
```c
// BUG: Double-converts to meters
printf("beam_center_m=X:%.15g Y:%.15g\n", 
       Xbeam/1000.0, Ybeam/1000.0);  // Xbeam already in meters!
```
**Impact**: Shows `5.125e-05` instead of correct `0.05125`  
**Workaround**: Ignore logged value, check actual calculation

### Convention Switching Not Documented
The C code's automatic CUSTOM mode switching when `-twotheta_axis` is specified is not documented in the original code.

## §7: Required Reading Before Debugging

1. **[Detector Component Spec](../architecture/detector.md)** - Explains hybrid unit system
2. **[Global Conventions](../architecture/conventions.md)** - Project-wide rules
3. **[C Parameter Dictionary](../architecture/c_parameter_dictionary.md)** - All C parameters
4. **[Config Mapping](../development/c_to_pytorch_config_map.md)** - C↔Python mapping

## §8: Debugging Decision Tree

```
Start: Check correlation value
│
├─> >99% correlation?
│   └─> ✅ No geometry issues, look elsewhere
│
├─> 90-99% correlation?
│   └─> Minor issue: Check unit conversions, pixel offsets
│
├─> 10-90% correlation?
│   └─> Moderate issue: Check pivot mode, conventions
│
├─> <10% correlation?
│   └─> Major issue: Check basis vectors, rotation order
│
└─> ~0% or negative?
    └─> Fundamental issue: Wrong coordinate system or pivot
```

## §9: Time-Saving Commands

### Quick Correlation Check
```bash
# Just check the correlation value
python scripts/verify_detector_geometry.py | grep "correlation"
```

### Quick Parameter Audit
```bash
# See what C is actually receiving
./nanoBragg [params] -debug 2>&1 | head -50
```

### Quick Trace Comparison
```bash
# One-liner to find first difference
diff <(grep "pix0_vector" c_trace.log) <(grep "pix0_vector" py_trace.log)
```

## §10: If All Else Fails

1. **Generate fresh Golden Suite data** - The reference might be outdated
2. **Check C code for preprocessor flags** - Some behavior might be compile-time dependent
3. **Try simpler configuration** - Remove rotations one by one to isolate issue
4. **Ask**: "Is the C code actually correct?" - Sometimes the reference has bugs too

---

**Last Updated**: January 9, 2025  
**Based On**: 8 hours of debugging session findings  
**Estimated Time Saved**: 4-8 hours per debugging session
