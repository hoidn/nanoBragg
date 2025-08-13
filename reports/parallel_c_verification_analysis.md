# Parallel C Reference Verification Analysis

**Date:** 2025-08-06  
**Status:** Investigation Complete - Major Issues Identified  
**Author:** Claude Code Analysis

## Executive Summary

This document summarizes the comprehensive debugging process undertaken to implement and analyze a parallel C reference verification system for the nanoBragg PyTorch port. The investigation revealed critical discrepancies between the PyTorch and C implementations, including massive intensity scaling differences and spatial pattern mismatches.

## 1. Implementation Overview

### 1.1 Completed Infrastructure

We successfully implemented a complete parallel C verification system:

**✅ Phase 1 - Foundation Components:**
- `scripts/c_reference_utils.py`: Identity matrix generator and nanoBragg.c command builder
- Proper parameter mapping from PyTorch configs to C command-line arguments

**✅ Phase 2 - Execution and Parsing:**
- `scripts/smv_parser.py`: Complete SMV format parser with header extraction
- `scripts/c_reference_runner.py`: C execution wrapper with error handling and temp file management

**✅ Phase 3 - Integration and Visualization:**
- Enhanced `scripts/verify_detector_geometry.py` with 6-panel comparison plots
- Quantitative correlation metrics and JSON output
- Automatic parallel comparison when C reference available

**✅ Phase 4 - Validation Infrastructure:**
- End-to-end verification system functional
- Proper image dimension matching (1024×1024)
- Comprehensive dimensional analysis tools

### 1.2 System Capabilities

The verification system can now:
- Execute nanoBragg.c with equivalent parameters to PyTorch
- Parse SMV output files and extract image data
- Generate side-by-side visualizations with difference maps
- Compute quantitative agreement metrics (correlation, RMS differences)
- Handle various detector configurations (baseline, tilted, rotated)

## 2. Critical Issues Discovered

### 2.1 Massive Intensity Scale Discrepancy

**Issue:** PyTorch and C reference produce dramatically different intensity scales.

**Quantitative Findings:**
- **PyTorch**: Maximum intensity ~155, mean ~0.9-1.0
- **C Reference**: Maximum intensity ~55,000, mean ~52,000
- **Scale Ratio**: ~350-8,800× difference
- **Correlation**: 0.126 baseline, 0.024 tilted (expected >0.999)

**Detailed Analysis:**
```
Small-scale test (8×8 pixels):
  PyTorch: Min=5.89e-01, Max=6.40e-01, Mean=6.22e-01
  C Reference: Min=5.50e+04, Max=5.50e+04, Mean=5.50e+04
  Intensity ratio: ~86,000×
```

### 2.2 Spatial Pattern Mismatch

**Issue:** Fundamental differences in diffraction pattern characteristics.

**Visual Observations:**
- **PyTorch**: Fine, sharp, closely-spaced concentric rings with high resolution detail
- **C Reference**: Broad, blurred features with fewer, more diffuse patterns
- **Pattern Type**: PyTorch shows what appears to be proper Bragg diffraction; C shows blob-like features

**Spatial Scale Analysis:**
- Both implementations use identical crystal parameters (5×5×5 cells, 100 Å unit cell)
- Expected first Bragg ring at ~62 pixels from beam center
- PyTorch shows rings much closer to center than expected
- C shows broader features more consistent with expected scale

## 3. Debugging Process and Methodology

### 3.1 Parameter Verification

**Detector Geometry Analysis:**
```
✅ Detector parameters verified identical:
  - Size: 1024×1024 pixels
  - Pixel size: 0.1 mm (1000 Å)
  - Physical size: 102.4×102.4 mm
  - Distance: 100 mm (1,000,000 Å)
  - Beam center: (51.2, 51.2) mm
```

**Crystal Configuration Analysis:**
```
✅ Crystal parameters verified identical:
  - Unit cell: 100×100×100 Å, 90°×90°×90°
  - Crystal size: 5×5×5 cells = 500×500×500 Å
  - Structure factor: F = 100 (constant)
  - Reciprocal lattice: |a*| = 0.01 Å⁻¹ (correct for |G|=1/d convention)
```

### 3.2 Unit System Investigation

**Initial Hypothesis:** Missing 2π factor in reciprocal lattice calculation.

**Investigation Results:**
- PyTorch uses |G| = 1/d convention correctly
- For 100 Å unit cell: |a*| = 1/100 = 0.01 Å⁻¹ ✅
- Expected d₁₀₀ = 100 Å matches input ✅
- Unit conversions verified correct (mm → Å) ✅

**Conclusion:** Crystal geometry implementation is mathematically correct.

### 3.3 Scattering Vector Analysis

**Miller Index Calculation Debug:**
```
Expected first-order reflections:
  (1,0,0): |q| = 0.062832 Å⁻¹ (expected)
  Actual PyTorch |q| values: ~0.006-0.015 Å⁻¹

Initial Factor Analysis:
  Ratio: 0.062832 / 0.01 ≈ 6.28 ≈ 2π
```

**Convention Verification:**
- PyTorch simulator uses: `S = (s_out - s_in) / λ` ✅
- This matches nanoBragg.c convention ✅
- Factor of 2π discrepancy was in debug script, not implementation ✅

### 3.4 Intensity Scale Investigation

**Structure Factor Analysis:**
```python
# Both implementations should use F = 100
PyTorch: crystal.get_structure_factor() returns 100.0 ✅
C Reference: -default_F 100 parameter ✅
```

**Intensity Calculation:**
- Expected: I = |F|² × |F_lattice|² × (geometric factors)
- Scale factor √(86,000) ≈ 293 suggests ~300× amplitude difference
- Not a simple linear scaling relationship

## 4. Root Cause Hypotheses

### 4.1 Primary Hypothesis: Different Integration Schemes

**Evidence:**
- C reference produces nearly constant intensity across pixels (55,000 ± small variation)
- PyTorch shows proper diffraction patterns with spatial variation
- 350-8,800× intensity differences suggest different physics calculations

**Possible Causes:**
1. **Mosaic Integration Differences**: C may average over mosaic domains differently
2. **Phi Step Integration**: Different oscillation angle sampling
3. **Source Point Integration**: Beam divergence effects
4. **Pixel Oversampling**: C may use subpixel integration PyTorch lacks

### 4.2 Secondary Hypothesis: Structure Factor Handling

**Possible Issues:**
1. **Default F Application**: `-default_F` in C may work differently than hardcoded F=100 in PyTorch
2. **Lattice Factor Calculation**: F_lattice computation may differ
3. **Crystal Shape Function**: sincg() implementation differences

### 4.3 Spatial Pattern Hypothesis: Effective Resolution Differences

**Evidence:**
- PyTorch shows fine, sharp rings (higher effective resolution)
- C shows broad, blurred features (lower effective resolution)
- Both use identical geometric parameters

**Possible Causes:**
1. **Mosaic Spread**: C includes crystal mosaicity PyTorch ignores
2. **Beam Divergence**: C includes source size effects
3. **Instrumental Resolution**: C includes detector response functions
4. **Integration Kernel Size**: Different effective integration volumes

## 5. Diagnostic Evidence Summary

### 5.1 What Works Correctly
- ✅ Image dimension matching (1024×1024)
- ✅ Parameter parsing and command generation
- ✅ SMV file reading and header extraction
- ✅ Unit conversions (mm ↔ Angstroms)
- ✅ Crystal geometry and reciprocal lattice calculations
- ✅ Detector coordinate system and basis vectors
- ✅ Miller index calculation convention

### 5.2 What Shows Major Discrepancies
- ❌ Intensity scales (300-8,800× difference)
- ❌ Spatial pattern characteristics (sharp vs. blurred)
- ❌ Correlation coefficients (0.02-0.13 vs. expected >0.999)
- ❌ Physical interpretation of results

### 5.3 What Needs Further Investigation
- ❓ Mosaic domain sampling and integration
- ❓ Phi rotation step handling
- ❓ Source point integration
- ❓ Crystal shape transform implementation
- ❓ Detector response and instrumental effects

## 6. Recommended Next Steps

### 6.1 High Priority Investigations

**1. Compare Mosaic and Phi Integration [Critical]**
```python
# Test with minimal settings
mosaic_spread = 0.0  # Disable mosaicity
phi_steps = 1        # Single phi angle
N_source_points = 1  # Single source point
```
**Hypothesis**: If patterns match with minimal integration, the issue is in averaging schemes.

**2. Trace Individual Physics Components [Critical]**
- Compare F_cell values at specific (h,k,l) positions
- Compare F_lattice (sincg function) outputs
- Compare |F_total|² calculations step by step
- Verify intensity = |F_total|² implementation

**3. Implement C-Code Trace Comparison [High Priority]**
```bash
# Generate detailed C trace logs
./nanoBragg -default_F 100 -trace_pixels 10 -verbose > c_trace.log

# Generate equivalent PyTorch trace
python debug_pixel_trace.py > pytorch_trace.log

# Compare line by line
diff -u c_trace.log pytorch_trace.log
```

### 6.2 Medium Priority Investigations

**4. Test with Different Crystal Sizes**
- Try N_cells = (1,1,1) vs (2,2,2) vs (5,5,5)
- Check if intensity scaling is crystal-size dependent
- Verify if spatial patterns change appropriately

**5. Test with Real Structure Factors**
- Generate simple HKL file with known F values
- Compare `-hkl` mode vs `-default_F` mode
- Verify structure factor lookup mechanisms

**6. Investigate Detector Effects**
- Test different detector distances (50mm, 200mm)
- Test different pixel sizes (0.05mm, 0.2mm)  
- Check if scale factors are geometry-dependent

### 6.3 Lower Priority Enhancements

**7. Improve Diagnostic Tools**
- Add pixel-by-pixel F_cell and F_lattice output
- Implement interactive visualization tools
- Add automated regression testing

**8. Documentation and Validation**
- Document all discovered conventions and formulas
- Create reference implementation test cases
- Validate against known analytical solutions

## 7. Technical Implementation Notes

### 7.1 Current Verification Workflow
```bash
# Run complete parallel verification
KMP_DUPLICATE_LIB_OK=TRUE python scripts/verify_detector_geometry.py

# Outputs generated:
reports/detector_verification/parallel_c_comparison.png      # 6-panel comparison
reports/detector_verification/correlation_metrics.json       # Quantitative metrics
```

### 7.2 Key Code Components
- **C Command Generation**: `build_nanobragg_command()` in `c_reference_utils.py`
- **SMV Parsing**: `parse_smv_image()` in `smv_parser.py`  
- **Execution Wrapper**: `CReferenceRunner.run_simulation()` in `c_reference_runner.py`
- **Visualization**: `create_parallel_comparison_plots()` in `verify_detector_geometry.py`

### 7.3 Debug Commands
```bash
# Intensity scaling analysis
python scripts/debug_intensity_scaling.py

# Spatial scale analysis
python scripts/debug_spatial_scale.py

# Miller index analysis
python scripts/debug_miller_indices.py

# Unit conversion verification
python scripts/debug_unit_conversion.py
```

## 8. Conclusion

The parallel C verification system is **functionally complete and operational**, providing a powerful framework for validating the PyTorch implementation. However, it has revealed **fundamental discrepancies** between the implementations that require immediate attention.

The **300-8,800× intensity scale difference** and **spatial pattern mismatches** indicate that while the geometric foundations are correct, the physics calculations differ significantly. This suggests either:

1. **Implementation bugs** in the PyTorch diffraction calculation
2. **Different physics assumptions** between the implementations  
3. **Missing integration effects** in the PyTorch version

The verification system provides the necessary tools to debug these issues systematically through detailed trace comparisons and component-by-component validation.

**Immediate Action Required:** Focus on mosaic/phi integration differences and implement detailed physics tracing to identify where the implementations diverge.