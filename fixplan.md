# Fix Plan: Detector Geometry Correlation Issue

**Date**: January 20, 2025  
**Issue**: PyTorch vs C reference correlation = 0.040 (target > 0.999)  
**Status**: Critical - Blocking validation of detector geometry implementation  

## Executive Summary

Despite fixing C reference parameter bugs (-twotheta, -Xbeam/-Ybeam), the correlation between PyTorch and C implementations remains unacceptably low (0.040). The detector geometry appears correct (basis vectors match), suggesting the issue lies deeper in the simulation pipeline.

## Current State Analysis

### What We Know Works
- ✅ Baseline configuration (no tilt): 0.999 correlation
- ✅ Detector basis vectors: Identical between C and PyTorch
- ✅ pix0_vector calculation: Matches between implementations
- ✅ C parameter mapping: Fixed (-twotheta, -Xbeam/-Ybeam)

### What Fails
- ❌ Tilted configuration (twotheta=20°): 0.040 correlation
- ❌ SAMPLE pivot mode: May have implementation differences
- ❌ Image generation: Produces vastly different patterns despite same geometry

### Key Insight
**The geometry calculations are likely correct.** The issue appears to be in how the geometry is used in the simulation, not the geometry itself.

## Root Cause Hypotheses (Ranked by Probability)

### 1. **SAMPLE Pivot Implementation Mismatch** (60% probability)
- **Evidence**: Correlation changes with pivot mode (BEAM=0.28, SAMPLE=0.04)
- **Theory**: PyTorch's SAMPLE pivot affects more than just pix0_vector
- **Test**: Compare pixel-to-lab coordinate transformations

### 2. **Pixel Coordinate Mapping** (25% probability)
- **Evidence**: Spot positions differ significantly in output images
- **Theory**: get_pixel_coords() may use basis vectors differently
- **Test**: Trace single pixel from detector to reciprocal space

### 3. **Hidden Parameter Differences** (10% probability)
- **Evidence**: C code has many implicit defaults
- **Theory**: Missing parameter that changes with -twotheta
- **Test**: Comprehensive parameter audit

### 4. **Coordinate System Convention** (5% probability)
- **Evidence**: MOSFLM vs lab frame conversions
- **Theory**: Subtle sign or axis convention difference
- **Test**: Check all coordinate transformations

## Systematic Fix Approach

### Phase 1: Parallel Trace Debugging (2-3 hours)

#### Step 1.1: Instrument C Code
```bash
# Add comprehensive tracing to nanoBragg.c
cd golden_suite_generator
# Add TRACE_C prints for pixel 512,512:
# - Pixel coordinates (s,f)
# - Lab coordinates (x,y,z)
# - Scattering vector S
# - Miller indices (h,k,l)
# - Structure factor F
# - Final intensity
```

#### Step 1.2: Create Python Trace Script
```python
# scripts/trace_pixel_512_512.py
import torch
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.config import DetectorConfig, CrystalConfig, DetectorPivot

config = DetectorConfig(
    distance_mm=100.0,
    beam_center_s=51.2,
    beam_center_f=51.2,
    detector_twotheta_deg=20.0,
    detector_pivot=DetectorPivot.SAMPLE,
)

# Trace pixel 512,512 through entire pipeline
# Print each intermediate calculation
```

#### Step 1.3: Compare Traces
```bash
# Run both and diff
./nanoBragg_golden [params] > c_trace.log 2>&1
python scripts/trace_pixel_512_512.py > py_trace.log
diff -u c_trace.log py_trace.log | head -50
```

### Phase 2: Fix Identified Issues (1-2 hours)

#### Step 2.1: Locate Divergence
- Find first line where values differ > 1e-6
- Identify which calculation step introduces error
- Document the mathematical operation involved

#### Step 2.2: Implement Fix
Based on divergence location:

**If in pixel→lab transformation:**
```python
# Check detector.get_pixel_coords()
# Verify pix0_vector usage
# Check basis vector application
```

**If in lab→reciprocal transformation:**
```python
# Check scattering vector calculation
# Verify wavelength/energy conversions
# Check rotation matrix applications
```

**If in Miller index calculation:**
```python
# Verify h = S·a convention (not S·a*)
# Check crystal orientation matrices
# Verify reciprocal lattice vectors
```

#### Step 2.3: Verify Fix
```bash
# Re-run verification
python scripts/verify_detector_geometry.py
# Target: correlation > 0.999
```

### Phase 3: Comprehensive Validation (1 hour)

#### Step 3.1: Test Matrix
| Configuration | Expected Correlation |
|--------------|---------------------|
| Baseline (no tilt) | > 0.999 |
| Small tilt (5°) | > 0.999 |
| Medium tilt (10°) | > 0.999 |
| Large tilt (20°) | > 0.999 |
| With rotx/roty/rotz | > 0.999 |

#### Step 3.2: Regression Tests
```bash
pytest tests/test_detector_geometry.py -v
pytest tests/test_suite.py::TestTier1TranslationCorrectness -v
```

#### Step 3.3: Document Fix
- Update CLAUDE.md with new conventions discovered
- Add unit tests for specific issue
- Update detector.md specification if needed

## Implementation Checklist

### Immediate Actions (Today)
- [ ] Create trace_pixel_512_512.py script
- [ ] Add C instrumentation for pixel 512,512
- [ ] Generate parallel traces for tilted case
- [ ] Identify exact divergence point
- [ ] Document divergence location and values

### Fix Implementation (Tomorrow)
- [ ] Analyze divergence mathematics
- [ ] Implement targeted fix
- [ ] Test with original configuration
- [ ] Test with variation matrix
- [ ] Run full regression suite

### Validation & Cleanup
- [ ] Achieve > 0.999 correlation for all test cases
- [ ] Remove debug instrumentation
- [ ] Commit fix with detailed explanation
- [ ] Update documentation
- [ ] Close related GitHub issues

## Success Criteria

### Minimum Acceptable
- Tilted configuration correlation > 0.999
- Baseline configuration unchanged (> 0.999)
- All existing tests pass

### Target
- All detector configurations > 0.999 correlation
- Performance unchanged or improved
- Clear documentation of root cause

## Risk Mitigation

### If Parallel Trace Fails to Find Issue
1. Expand trace to multiple pixels (corners, edges, center)
2. Trace entire first diffraction spot
3. Compare intermediate images at each pipeline stage

### If Fix Breaks Other Tests
1. Create configuration-specific code paths
2. Add compatibility mode flag
3. Investigate if other tests had compensating errors

### If Performance Degrades
1. Profile before/after
2. Cache repeated calculations
3. Consider approximate methods for non-critical paths

## Technical Resources

### Key Files
- `src/nanobrag_torch/models/detector.py` - Detector implementation
- `golden_suite_generator/nanoBragg.c` - C reference
- `scripts/verify_detector_geometry.py` - Validation script
- `scripts/c_reference_utils.py` - C command generation

### Documentation
- `docs/architecture/detector.md` - Detector specification
- `docs/development/c_to_pytorch_config_map.md` - Parameter mapping
- `CLAUDE.md` - Project conventions and rules

### Debugging Tools
- `scripts/debug_pixel_trace.py` - Existing trace framework
- `scripts/compare_traces.py` - Trace comparison utility
- `reports/detector_verification/` - Output location

## Timeline

### Day 1 (Today)
- **2 hours**: Implement parallel trace debugging
- **1 hour**: Identify divergence point
- **1 hour**: Document findings

### Day 2
- **2 hours**: Implement fix
- **1 hour**: Validate fix
- **1 hour**: Documentation and cleanup

### Total Estimate
- **8 hours** to complete resolution
- **+2 hours** buffer for unexpected issues

## Next Session Handoff

If not completed in current session, the next developer should:

1. **Start with**: Run trace_pixel_512_512.py if created
2. **Focus on**: The divergence point identified in traces
3. **Key insight**: Geometry is correct, issue is in usage
4. **Don't retry**: Parameter name fixes (already done)
5. **Contact**: Check git blame for recent detector changes

## Appendix: Command Reference

### Generate C Trace
```bash
cd golden_suite_generator
./nanoBragg_golden -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 \
  -default_F 100 -distance 100 -detpixels 1024 \
  -Xbeam 51.2 -Ybeam 51.2 -twotheta 20 \
  -floatfile test.bin 2>&1 | grep TRACE_C > c_trace.log
```

### Run Python Verification
```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/verify_detector_geometry.py
```

### Quick Correlation Check
```bash
cat reports/detector_verification/correlation_metrics.json | grep correlation
```

---

**Document Version**: 1.0  
**Last Updated**: January 20, 2025  
**Author**: Claude (via session with user)  
**Status**: Ready for implementation