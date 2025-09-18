# Comprehensive Acceptance Tests for C vs PyTorch Parallel Validation

**Purpose**: Black-box behavior tests that systematically catch geometry, scaling, and correlation failures early in the development cycle. These tests focus on C vs PyTorch output comparison and are designed to catch the critical failures observed in current validation.

## Critical Failures Addressed

Based on the reported failures:
1. **Beam center scaling issues** - hardcoded 51.2mm regardless of detector size
2. **Position errors** - peaks at wrong locations (13,25) vs expected (32,32)
3. **Intensity scaling problems** - ~79x magnitude differences
4. **Pattern correlation failures** - 0.048 instead of >0.95

## Test Categories

### A. Detector Size Invariance Tests
### B. Beam Center Calculation Tests
### C. Peak Position Verification Tests
### D. Intensity Scaling Tests
### E. Pattern Correlation Tests
### F. Unit Conversion Tests
### G. Edge Case and Robustness Tests

---

## A. Detector Size Invariance Tests

### AT-PARALLEL-001: Beam Center Scales with Detector Size
**Purpose**: Catch hardcoded beam center issues
**Setup**:
- Fixed beam center ratio (0.5, 0.5) relative to detector
- Test detector sizes: 64x64, 128x128, 256x256, 512x512, 1024x1024
- Pixel size: 0.1mm
- Crystal: 100Å cubic, N=3

**C Commands**:
```bash
# 64x64 detector
./nanoBragg -detpixels 64 -pixel 0.1 -lambda 6.2 -N 3 -cell 100 100 100 90 90 90 -default_F 100 -distance 100 -floatfile 64x64.bin

# 128x128 detector
./nanoBragg -detpixels 128 -pixel 0.1 -lambda 6.2 -N 3 -cell 100 100 100 90 90 90 -default_F 100 -distance 100 -floatfile 128x128.bin

# etc. for 256, 512, 1024
```

**Expected Behavior**:
- Beam center (mm) = detector_pixels/2 × pixel_size_mm
- Peak should appear at (detector_pixels/2, detector_pixels/2) ± 2 pixels
- Intensity scaling should be proportional to solid angle

**Pass Criteria**:
- Beam center position accuracy: ±0.05mm
- Peak position accuracy: ±2 pixels from center
- Cross-size correlation: >0.95 when normalized

**Fail Criteria**:
- Beam center fixed at 51.2mm regardless of detector size
- Peak always at same absolute pixel position
- Intensity ratios inconsistent with geometric scaling

---

### AT-PARALLEL-002: Pixel Size Independence
**Purpose**: Verify beam center calculations with different pixel sizes
**Setup**:
- Fixed detector: 256x256 pixels
- Pixel sizes: 0.05mm, 0.1mm, 0.2mm, 0.4mm
- Beam center: (25.6mm, 25.6mm) for all cases

**Expected Behavior**:
- Beam center in pixels = 25.6mm / pixel_size_mm
- Peak position scales inversely with pixel size
- Angular geometry preserved

**Pass Criteria**:
- Beam center pixel calculation: ±0.1 pixels
- Peak positions scale correctly: ratio within 5%
- Pattern correlation: >0.95 when scaled

---

### AT-PARALLEL-003: Detector Offset Preservation
**Purpose**: Test beam center calculations with off-center beams
**Setup**:
- Detector: 512x512, 0.1mm pixels
- Beam centers: (20,20), (30,40), (45,25), (60,60) mm
- Test with 3 detector sizes: 256x256, 512x512, 1024x1024

**Expected Behavior**:
- Peak appears at beam_center_mm / pixel_size_mm pixels
- Offset geometry preserved across detector sizes

**Pass Criteria**:
- Position accuracy: ±1 pixel for all beam centers
- Offset ratios preserved: ±2%

---

## B. Beam Center Calculation Tests

### AT-PARALLEL-004: MOSFLM 0.5 Pixel Offset
**Purpose**: Verify MOSFLM convention's +0.5 pixel adjustment
**Setup**:
- Detector: 256x256, 0.1mm pixels
- Beam center: (25.6mm, 25.6mm)
- Convention: MOSFLM vs XDS comparison

**C Commands**:
```bash
# MOSFLM (should add +0.5 pixel)
./nanoBragg -mosflm -detpixels 256 -pixel 0.1 -Xbeam 25.6 -Ybeam 25.6 -lambda 6.2 -N 3 -cell 100 100 100 90 90 90 -default_F 100 -distance 100 -floatfile mosflm.bin

# XDS (no +0.5 pixel)
./nanoBragg -xds -detpixels 256 -pixel 0.1 -ORGX 256 -ORGY 256 -lambda 6.2 -N 3 -cell 100 100 100 90 90 90 -default_F 100 -distance 100 -floatfile xds.bin
```

**Expected Behavior**:
- MOSFLM: Effective beam center = (256+0.5, 256+0.5) pixels
- XDS: Effective beam center = (256, 256) pixels
- Peak offset = 0.5 pixels between conventions

**Pass Criteria**:
- Peak position difference: 0.4-0.6 pixels
- Pattern correlation: >0.99 when aligned

---

### AT-PARALLEL-005: Beam Center Parameter Mapping
**Purpose**: Test correct mapping of beam center parameters
**Setup**:
- Test parameter combinations:
  - `-Xbeam 30 -Ybeam 20` (MOSFLM style)
  - `-ORGX 300 -ORGY 200` (XDS style)
  - `-Xclose 0.03 -Yclose 0.02` (close distance style)

**Expected Behavior**:
- Parameter mapping follows convention rules
- Equivalent settings produce same beam centers
- Pivot mode set correctly (BEAM vs SAMPLE)

**Pass Criteria**:
- Equivalent configurations: peak position ±0.5 pixels
- Pivot mode consistency check passes

---

## C. Peak Position Verification Tests

### AT-PARALLEL-006: Single Reflection Position
**Purpose**: Verify first-principles peak position calculation
**Setup**:
- Crystal: 100Å cubic, single reflection h=1,k=0,l=0
- Multiple detector distances: 50mm, 100mm, 200mm
- Multiple wavelengths: 1.0Å, 1.5Å, 2.0Å

**Expected Behavior**:
- Bragg angle: θ = arcsin(λ/(2*d_hkl))
- Diffraction angle: 2θ
- Pixel position from geometry calculation

**Pass Criteria**:
- Peak position vs theory: ±0.5 pixels
- Distance scaling: position ratio within 2%
- Wavelength scaling: follows Bragg's law ±1%

---

### AT-PARALLEL-007: Peak Position with Rotations
**Purpose**: Test peak movement with detector rotations
**Setup**:
- Base: cubic crystal, centered beam
- Rotations: rotx=5°, roty=3°, rotz=2°, twotheta=10°
- Compare with and without rotations

**Expected Behavior**:
- Rotations shift peaks according to rotation matrices
- Peak intensities preserved (solid angle corrections)
- Multiple peaks maintain relative positions

**Pass Criteria**:
- Peak shift magnitude: 10-100 pixels (reasonable range)
- Relative peak positions: preserved within 5%
- Intensity conservation: total within 10%

---

### AT-PARALLEL-008: Multi-Peak Pattern Registration
**Purpose**: Verify complete diffraction pattern alignment
**Setup**:
- Crystal: Triclinic cell (70,80,90,75,85,95)°
- Generate pattern with 20+ visible reflections
- Test with 3 different orientations

**Expected Behavior**:
- All peaks align between C and PyTorch
- Peak intensity ratios preserved
- Pattern shape maintained

**Pass Criteria**:
- Peak matching: >95% of bright peaks align ±1 pixel
- Intensity ratio RMS error: <10%
- Overall pattern correlation: >0.98

---

## D. Intensity Scaling Tests

### AT-PARALLEL-009: Intensity Normalization
**Purpose**: Catch intensity scaling factor errors
**Setup**:
- Fixed geometry, vary crystal size: N=1,2,3,5,10
- Fixed geometry, vary F_hkl: 50,100,200,500
- Fixed geometry, vary wavelength: 1.0,1.5,2.0,3.0Å

**Expected Behavior**:
- Intensity ∝ N³ (volume scaling)
- Intensity ∝ F² (structure factor scaling)
- Wavelength dependence follows physics

**Pass Criteria**:
- Volume scaling: R² > 0.99 for log-log plot
- F-factor scaling: R² > 0.99 for quadratic fit
- Wavelength scaling: follows expected power law ±5%

**Fail Criteria**:
- Fixed intensity regardless of parameters
- Random intensity ratios
- Wrong power law exponents

---

### AT-PARALLEL-010: Solid Angle Corrections
**Purpose**: Test intensity corrections for detector geometry
**Setup**:
- Fixed crystal, vary detector distance: 50,100,200,400mm
- Fixed crystal, vary detector tilt: 0°,10°,20°,30°
- Measure total intensity in pattern

**Expected Behavior**:
- Intensity ∝ 1/distance² (solid angle)
- Tilt corrections preserve total flux
- Peak shapes change but total intensity conserved

**Pass Criteria**:
- Distance scaling: follows 1/r² law ±5%
- Tilt intensity conservation: ±10%
- Geometric corrections: consistent with theory

---

### AT-PARALLEL-011: Polarization Factor Verification
**Purpose**: Test polarization corrections
**Setup**:
- Reflections at different scattering angles
- Compare polarized vs unpolarized calculations
- Test at detector edges vs center

**Expected Behavior**:
- Polarization factor: P = (1 + cos²(2θ))/2
- Center vs edge intensity ratios follow formula
- Azimuthal angle dependence correct

**Pass Criteria**:
- Polarization factor calculation: ±1%
- Angular dependence: R² > 0.95 vs theory

---

## E. Pattern Correlation Tests

### AT-PARALLEL-012: Reference Pattern Correlation
**Purpose**: Test against known good patterns
**Setup**:
- Use proven C configurations that work
- Generate patterns with PyTorch using identical parameters
- Test multiple cell types: cubic, tetragonal, orthorhombic, triclinic

**Expected Behavior**:
- Near-perfect correlation for identical configurations
- Small numerical differences only
- Pattern features preserved

**Pass Criteria**:
- Simple cubic: correlation > 0.999
- Complex triclinic: correlation > 0.995
- Peak positions: all align ±0.5 pixels

**Fail Criteria**:
- Correlation < 0.95 for any standard case
- Systematic pattern shifts > 2 pixels
- Missing or extra peaks

---

### AT-PARALLEL-013: Cross-Platform Consistency
**Purpose**: Verify consistency across different systems
**Setup**:
- Run same calculation on different machines
- Test both C and PyTorch implementations
- Compare floating-point precision effects

**Expected Behavior**:
- Machine-independent results
- Reproducible random number sequences
- Minimal floating-point variations

**Pass Criteria**:
- Cross-machine correlation: > 0.9999
- Bit-reproducible when using same seed
- Floating-point differences: <1e-10 relative

---

### AT-PARALLEL-014: Noise Robustness Test
**Purpose**: Test correlation with added noise
**Setup**:
- Add controlled noise levels: 1%, 5%, 10% of signal
- Test correlation degradation vs noise level
- Verify noise doesn't hide systematic errors

**Expected Behavior**:
- Correlation degrades predictably with noise
- Systematic errors still detectable
- Pattern structure preserved under noise

**Pass Criteria**:
- 1% noise: correlation > 0.99
- 5% noise: correlation > 0.95
- 10% noise: correlation > 0.90

---

## F. Unit Conversion Tests

### AT-PARALLEL-015: Mixed Unit Input Handling
**Purpose**: Catch unit conversion errors
**Setup**:
- Same physical setup, different input units:
  - Distance: 100mm, 0.1m, 1000000Å
  - Wavelength: 1.5Å, 0.15nm, 1.5e-10m
  - Cell: 100Å, 10nm, 1e-8m

**Expected Behavior**:
- Identical results regardless of input units
- Proper internal unit conversion
- No unit-dependent scaling errors

**Pass Criteria**:
- Cross-unit correlation: > 0.9999
- Peak positions: identical ±0.01 pixels
- Intensities: identical ±0.1%

**Fail Criteria**:
- Different results for same physical setup
- Position errors of 10x or 100x (common unit errors)
- Intensity scaling by unit conversion factors

---

### AT-PARALLEL-016: Extreme Scale Testing
**Purpose**: Test numerical stability at extreme scales
**Setup**:
- Very small cells: 1Å, very large cells: 10000Å
- Very short wavelengths: 0.1Å, very long: 10Å
- Very close detectors: 10mm, very far: 10m

**Expected Behavior**:
- No numerical overflow/underflow
- Sensible results at all scales
- Graceful handling of extreme cases

**Pass Criteria**:
- No NaN or Inf values
- Results scale correctly with parameters
- Performance acceptable across range

---

## G. Edge Case and Robustness Tests

### AT-PARALLEL-017: Grazing Incidence Geometry
**Purpose**: Test extreme detector tilts
**Setup**:
- Detector tilts: 60°, 75°, 85° from normal
- Twotheta angles: 0°, 30°, 60°, 120°
- Test beam hitting detector edge

**Expected Behavior**:
- Proper geometric projections
- No division by zero or singularities
- Sensible intensity distributions

**Pass Criteria**:
- No mathematical errors
- Smooth intensity variations
- Correlation > 0.9 vs analytical expectation

---

### AT-PARALLEL-018: Crystal Boundary Conditions
**Purpose**: Test pathological crystal orientations
**Setup**:
- Near-singular orientations (cell angles ~0° or ~180°)
- Extreme aspect ratios (a:b:c = 1:1:100)
- Random orientations with large misset angles

**Expected Behavior**:
- Stable calculations near singularities
- Sensible results for extreme geometries
- Robust handling of all orientations

**Pass Criteria**:
- No crashes or NaN values
- Results vary smoothly with parameters
- Degenerate cases handled gracefully

---

### AT-PARALLEL-019: High-Resolution Data
**Purpose**: Test large detector arrays
**Setup**:
- Detector sizes: 2048x2048, 4096x4096
- High crystal N values: N=20, N=50
- Many reflections: complex unit cells

**Expected Behavior**:
- Memory usage scales reasonably
- Computation time acceptable
- Results maintain accuracy

**Pass Criteria**:
- Memory usage < 8GB for 4k×4k detector
- Runtime < 5 minutes for complex case
- Correlation maintained: > 0.995

---

### AT-PARALLEL-020: Comprehensive Integration Test
**Purpose**: End-to-end validation of complete pipeline
**Setup**:
- Realistic experimental parameters:
  - Protein crystal: triclinic, 300+ reflections
  - Detector: 1024x1024, realistic noise levels
  - Multiple phi angles, mosaicity, beam divergence

**Expected Behavior**:
- Complete pipeline functions correctly
- Results match C implementation
- Performance suitable for real use

**Pass Criteria**:
- Pattern correlation: > 0.99
- Peak positions: all align ±1 pixel
- Intensity scaling: ±5% globally
- Runtime: < 30 seconds for standard case

**Fail Criteria**:
- Any correlation < 0.95
- Systematic position errors > 2 pixels
- Intensity scaling errors > 20%
- Runtime > 5 minutes

---

## Test Implementation Strategy

### Automation Framework
Each test should be implemented as:

```python
def test_at_parallel_XXX():
    """AT-PARALLEL-XXX: Test description"""

    # 1. Setup: Generate C reference data
    c_config = generate_c_config(test_params)
    c_result = run_c_simulation(c_config)

    # 2. Generate PyTorch equivalent
    pytorch_config = convert_config(c_config)
    pytorch_result = run_pytorch_simulation(pytorch_config)

    # 3. Compare and validate
    correlation = calculate_correlation(c_result, pytorch_result)
    position_error = check_peak_positions(c_result, pytorch_result)
    intensity_ratio = check_intensity_scaling(c_result, pytorch_result)

    # 4. Apply pass/fail criteria
    assert correlation > threshold_correlation
    assert position_error < threshold_position
    assert 0.5 < intensity_ratio < 2.0

    return {
        'correlation': correlation,
        'position_error': position_error,
        'intensity_ratio': intensity_ratio,
        'status': 'PASS'
    }
```

### Test Data Management
- **Golden Reference**: Store C output for each test case
- **Regeneration**: Scripts to rebuild references when C code changes
- **Versioning**: Track which C code version generated each reference
- **Validation**: Ensure references are internally consistent

### Performance Monitoring
- **Runtime Tracking**: Monitor test execution time
- **Memory Usage**: Track peak memory consumption
- **Regression Detection**: Alert on performance degradation
- **Scaling Analysis**: Document performance vs problem size

### Failure Analysis
When tests fail, automatically generate:
- **Diff Images**: Visual comparison of C vs PyTorch patterns
- **Trace Logs**: Step-by-step calculation comparison
- **Parameter Audit**: Verify configuration parity
- **Diagnostic Report**: Structured failure analysis

---

## Success Metrics

### Tier 1: Basic Functionality
- All detector size tests pass (AT-PARALLEL-001 to 003)
- Beam center calculations correct (AT-PARALLEL-004 to 005)
- Peak positions accurate (AT-PARALLEL-006 to 008)

### Tier 2: Quantitative Accuracy
- Intensity scaling correct (AT-PARALLEL-009 to 011)
- Pattern correlations high (AT-PARALLEL-012 to 014)
- Unit conversions robust (AT-PARALLEL-015 to 016)

### Tier 3: Production Readiness
- Edge cases handled (AT-PARALLEL-017 to 019)
- Integration test passes (AT-PARALLEL-020)
- Performance acceptable for real use

### Failure Thresholds
**Immediate Investigation Required**:
- Any correlation < 0.95 for simple cases
- Position errors > 2 pixels systematically
- Intensity scaling errors > 10x
- Test runtime > 10x reference C implementation

**Development Blocker**:
- Any Tier 1 test fails
- Correlation < 0.90 for any standard case
- Crashes or NaN values in any test
- Memory usage exceeds reasonable limits

This comprehensive test suite is designed to catch the specific failure modes observed (beam center scaling, position errors, intensity problems, correlation issues) while providing systematic coverage of the entire validation space from simple to complex scenarios.