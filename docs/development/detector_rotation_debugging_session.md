# Detector Rotation Debugging Session Report

**Date:** January 2025  
**Issue:** Poor correlation (-0.017) between PyTorch and C implementations for tilted detector configurations  
**Resolution Status:** Root cause identified, fix pending

---

## Executive Summary

Through systematic debugging using parallel trace analysis between C and PyTorch implementations, we identified that the poor correlation for tilted detectors is caused by a fundamental algorithmic difference in how SAMPLE pivot mode is implemented. The C code calculates detector positions before applying rotations, while PyTorch calculates them after rotations, leading to completely different pixel coordinates.

## Key Discoveries

### 1. The Core Issue

**Symptom:** Tilted detector configuration shows correlation of -0.017 (nearly anti-correlated) while baseline shows 0.998 (excellent).

**Root Cause:** SAMPLE pivot mode implementation differs between C and PyTorch:

```c
// C Implementation (SAMPLE pivot)
1. Calculate pix0_vector using UNROTATED basis vectors
2. Rotate pix0_vector itself
3. Rotate basis vectors

// PyTorch Implementation (SAMPLE pivot)  
1. Rotate basis vectors first
2. Calculate pix0_vector using ROTATED basis vectors
```

This fundamental difference causes pixel coordinates to be completely different:
- C pixel (377,644): `(0.0995, 0.0231, 0.00523)` meters
- PyTorch pixel (377,644): `(0.1028, -0.0000404, 0.0000406)` meters

### 2. Unit System Clarification

Through debugging, we clarified the detector's unit system:
- **Internal geometry:** Works in meters (distance=0.1m for 100mm)
- **Physics calculations:** Work in Angstroms
- **Key insight:** The detector correctly returns coordinates in meters, which the simulator then converts to Angstroms

Initial attempts to "fix" unit conversions made things worse, confirming the original mixed-unit design is correct.

### 3. Configuration Inconsistencies

We discovered that different test scripts were using different configurations:
- `verify_detector_geometry.py`: Uses correct beam center (61.2, 61.2) mm
- Some scripts incorrectly used (51.2, 51.2) mm
- This 10mm difference is exactly 100 pixels, explaining some of the confusion

## Debug Practices Established

### 1. Parallel Trace Analysis

We established a systematic approach for comparing C and PyTorch implementations:

```python
# 1. Add trace output to C code
printf("TRACE_C: pixel_pos_meters %.15g %.15g %.15g\n", pixel_pos[1], pixel_pos[2], pixel_pos[3]);

# 2. Create matching PyTorch trace
log_variable("pixel_pos_meters", pixel_coord_meters, log_file)

# 3. Run both with identical configurations
./nanoBragg -trace_pixel 377 644 [other params] 2>&1 | grep "TRACE_C:" > c_trace.log
python debug_tilted_pixel_trace.py  # Generates pytorch_trace.log

# 4. Compare traces to find divergence
diff c_trace.log pytorch_trace.log
```

### 2. Systematic Isolation

We used a staged approach to isolate the issue:
1. **Configuration verification:** Ensure both implementations receive identical parameters
2. **Unit system verification:** Confirm units at each stage of calculation
3. **Component isolation:** Test individual components (rotations, pivot modes) separately
4. **Trace comparison:** Line-by-line comparison of intermediate values

### 3. Debug Scripts Created

Several diagnostic scripts were created during the session:
- `debug_tilted_pixel_trace.py`: Generates PyTorch traces matching C format
- `debug_pix0_calculation.py`: Isolates pix0_vector calculation issue
- `test_rotation_order.py`: Verifies rotation sequence
- `trace_pix0_bug.py`: Monkey-patches detector for detailed debugging

## CLI Parameter Pitfalls

### 1. Beam Center Syntax

**Issue:** The C code expects `-Xbeam` and `-Ybeam` separately, not `-beam X Y`:
```bash
# Wrong (silently uses defaults)
./nanoBragg -beam 61.2 61.2

# Correct
./nanoBragg -Xbeam 61.2 -Ybeam 61.2
```

### 2. Trace Pixel Parameter

**Issue:** The C code only outputs detailed traces for specific pixels:
```bash
# Must specify which pixel to trace
./nanoBragg -trace_pixel 377 644 [other params]
```

### 3. Pivot Mode Auto-Selection

**Issue:** C code automatically switches to SAMPLE pivot when twotheta ≠ 0:
```python
# C behavior (from c_reference_utils.py)
if abs(detector_config.detector_twotheta_deg) > 1e-6:
    cmd.extend(["-pivot", "sample"])
```

### 4. Parameter Order Matters

**Issue:** Multi-value parameters must be passed correctly:
```bash
# Correct
-twotheta_axis 0.0 0.0 -1.0

# May be parsed incorrectly
-twotheta_axis 0 0 -1
```

## Lessons Learned

### 1. Don't Assume Configuration Bugs First

Initial hypothesis was that C wasn't receiving correct beam center values. Systematic verification showed configuration was correct, saving time from chasing the wrong issue.

### 2. Unit System Consistency is Critical

Attempting to "fix" perceived unit issues made things worse. The original mixed-unit system (meters for geometry, Angstroms for physics) is intentional and correct.

### 3. Trace Output Formatting Matters

C uses 1-based array indexing while Python uses 0-based. This caused initial confusion when comparing vector components:
```c
// C: fdet_vector[1] is x-component
// Python: fdet_vec[0] is x-component
```

### 4. Correlation Values are Diagnostic

- **0.99+**: Excellent agreement, minor numerical differences
- **0.95-0.99**: Good agreement, likely unit scaling or small offset
- **Near 0**: Uncorrelated, likely different calculations entirely
- **Negative**: Anti-correlated, often indicates reflection/inversion

### 5. Always Verify Intermediate Values

The issue wasn't in the final image but in intermediate calculations (pix0_vector). Tracing intermediate values is essential for finding where implementations diverge.

## Next Steps for Fixing

### 1. Implement Correct SAMPLE Pivot Algorithm

The PyTorch `Detector._calculate_pix0_vector()` method needs to be updated:

```python
def _calculate_pix0_vector(self):
    if self.config.detector_pivot == DetectorPivot.SAMPLE:
        # NEW: Calculate pix0_vector BEFORE rotations
        # 1. Use initial (unrotated) basis vectors
        fdet_initial = torch.tensor([0., 0., 1.], ...)
        sdet_initial = torch.tensor([0., -1., 0.], ...)
        odet_initial = torch.tensor([1., 0., 0.], ...)
        
        # 2. Calculate initial pix0_vector
        detector_origin = self.distance * odet_initial
        s_offset = (0.5 - self.beam_center_s) * self.pixel_size
        f_offset = (0.5 - self.beam_center_f) * self.pixel_size
        pix0_initial = detector_origin + s_offset * sdet_initial + f_offset * fdet_initial
        
        # 3. Apply same rotations as basis vectors
        pix0_rotated = apply_rotations(pix0_initial, rotx, roty, rotz, twotheta)
        self.pix0_vector = pix0_rotated
```

### 2. Update Tests

Add specific tests for SAMPLE pivot mode with rotations:
```python
def test_sample_pivot_with_rotations():
    """Test that SAMPLE pivot matches C implementation."""
    config = DetectorConfig(
        detector_pivot=DetectorPivot.SAMPLE,
        detector_rotx_deg=5.0,
        detector_roty_deg=3.0,
        detector_rotz_deg=2.0,
        detector_twotheta_deg=15.0,
    )
    # Verify against C reference values
```

### 3. Document the Algorithm

Add clear documentation explaining the two pivot modes:
- **BEAM pivot:** Detector rotates around the beam spot on the detector surface
- **SAMPLE pivot:** Detector rotates around the sample position

### 4. Verify Fix

After implementing the fix:
1. Run `verify_detector_geometry.py` - should show >0.99 correlation for tilted case
2. Run full test suite to ensure no regressions
3. Generate new traces to confirm pixel coordinates match C implementation

### 5. Consider Refactoring

The current implementation mixes rotation logic with pix0_vector calculation. Consider separating concerns:
- `_calculate_initial_geometry()`: Set up unrotated positions
- `_apply_rotations()`: Handle all rotation logic
- `_finalize_geometry()`: Calculate final positions based on pivot mode

## Conclusion

This debugging session successfully identified a fundamental algorithmic difference between C and PyTorch implementations of SAMPLE pivot mode. The systematic approach using parallel traces proved highly effective for finding where the implementations diverge. The fix is straightforward: match the C algorithm by calculating pix0_vector before applying rotations in SAMPLE pivot mode.

The session also established valuable debugging practices and clarified several aspects of the codebase that will benefit future development. The correlation metric proved to be an excellent diagnostic tool, with negative correlation immediately indicating a systematic transformation difference rather than simple numerical errors.

## Related Session Cross-References

### **Session Relationship Map**
See [`history/debugging_session_relationship_map.md`](/Users/ollie/Documents/nanoBragg/history/debugging_session_relationship_map.md) for visual timeline and navigation guide.

### **Direct Successors**
- [`history/2025-01-20_detector-geometry-correlation-debug.md`](/Users/ollie/Documents/nanoBragg/history/2025-01-20_detector-geometry-correlation-debug.md) - January 20, 2025 systematic parameter debugging that built on this session's findings
- [`history/2025-01-09_detector-geometry-pivot-fix.md`](/Users/ollie/Documents/nanoBragg/history/2025-01-09_detector-geometry-pivot-fix.md) - January 9, 2025 implementation of pivot mode fix discovered in this session

### **Documentation Follow-up**
- [`history/2025-01-09_documentation_fortification.md`](/Users/ollie/Documents/nanoBragg/history/2025-01-09_documentation_fortification.md) - January 9, 2025 comprehensive documentation initiative that formalized the configuration mapping and debugging practices established during this session