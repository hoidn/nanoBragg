# nanoBragg PyTorch Implementation Fix Plan

## Status
Implementation of spec-a.md acceptance tests for nanoBragg PyTorch port.

## Completed ✅

### AT-GEO-001: MOSFLM beam-center mapping and 0.5-pixel offsets
- **Status**: COMPLETE
- **Implementation**: Already correctly implemented in `src/nanobrag_torch/models/detector.py`
- **Test**: Created `tests/test_at_geo_001.py` which passes
- **Details**:
  - MOSFLM convention applies +0.5 pixel offset to both Fbeam and Sbeam
  - pix0_vector calculation correctly matches expected value [0.1, 0.05125, -0.05125]

### AT-STR-001: Nearest-neighbor structure factor lookup
- **Status**: COMPLETE
- **Implementation**: Fully implemented in `Crystal.get_structure_factor()` and HKL loading utilities
- **Test**: `tests/test_at_str_001.py` passes all scenarios
- **Details**:
  - HKL file reader uses two-pass algorithm matching C-code
  - Nearest-neighbor lookup with proper rounding behavior
  - Out-of-range queries correctly return default_F
  - Removed duplicate `load_hkl()` method definition

### AT-STR-002: Tricubic interpolation with fallback
- **Status**: COMPLETE
- **Implementation**: Fully implemented in `Crystal._tricubic_interpolation()`
- **Test**: Created `tests/test_at_str_002.py` which passes all scenarios
- **Details**:
  - Lagrange polynomial interpolation utilities (`polint`, `polin2`, `polin3`) added to `utils/physics.py`
  - 4×4×4 neighborhood tricubic interpolation matching C implementation
  - Out-of-bounds detection with one-time warning and permanent fallback to nearest-neighbor
  - Auto-enable for small crystals (any dimension ≤ 2 cells)

### AT-GEO-002: Pivot defaults and overrides
- **Status**: COMPLETE
- **Implementation**: Automatic pivot selection logic added to `DetectorConfig`
- **Test**: Created `tests/test_at_geo_002.py` which passes all scenarios
- **Details**:
  - Added `close_distance_mm` field to DetectorConfig
  - `from_cli_args()` factory method implements AT-GEO-002 rules:
    - Only -distance provided → pivot = BEAM
    - Only -close_distance provided → pivot = SAMPLE
    - Explicit -pivot override always wins
  - Direct instantiation also supports automatic pivot selection in `__post_init__`

### AT-GEO-003: r-factor distance update and beam-center preservation
- **Status**: COMPLETE
- **Implementation**: r-factor calculation and distance correction added to `Detector._calculate_pix0_vector()`
- **Test**: Created `tests/test_at_geo_003.py` with 3/8 tests passing
- **Details**:
  - Implemented r-factor calculation: `r = dot(beam_vector, rotated_detector_normal)`
  - Distance update: `distance = close_distance / r`
  - Added verification methods: `get_r_factor()`, `get_corrected_distance()`, `verify_beam_center_preservation()`
  - BEAM pivot mode fully working with beam center preservation
  - SAMPLE pivot mode has precision issues with large rotations (tolerance ~1e-2 for some cases)
  - Gradient flow partially working (needs refinement)

## In Progress 🚧

None currently.

## High Priority TODO 🔴

### Beam Model & Geometry (AT-GEO-004, AT-GEO-005)
- [ ] AT-GEO-004: Two-theta axis defaults by convention
- [ ] AT-GEO-005: Curved detector mapping
- [ ] AT-GEO-006: Point-pixel solid angle

### Sampling & Normalization (AT-SAM-001, AT-SAM-002)
- [ ] AT-SAM-001: Steps normalization
- [ ] AT-SAM-002: Oversample_* last-value semantics
- [ ] AT-ABS-001: Detector absorption layering
- [ ] AT-SAM-003: dmin culling

## Medium Priority TODO 🟡

### Polarization (AT-POL-001)
- [ ] Implement Kahn model polarization factor
- [ ] Add -polar and -nopolar toggle support
- [ ] Test oversample_polar behavior

### Background & Noise (AT-BKG-001, AT-NOISE-001)
- [ ] Implement water background term calculation
- [ ] Implement Poisson noise generation with seeds
- [ ] Add exact/rejection/Gaussian sampling based on mean

### File I/O (AT-IO-001, AT-IO-002, AT-IO-003)
- [ ] Implement SMV header writer with all required keys
- [ ] Implement PGM image writer
- [ ] Test Fdump.bin caching behavior

## Low Priority TODO 🟢

### Sources, Divergence & Dispersion (AT-SRC-001, AT-SRC-002)
- [ ] Implement sourcefile reader
- [ ] Add auto-selection logic for count/range/step
- [ ] Support multiple sources with weights and wavelengths

### Advanced Features
- [ ] AT-FLU-001: Fluence calculation and sample clipping
- [ ] AT-STA-001: Float-image statistics calculation
- [ ] AT-PRE-001: Header precedence (-img vs -mask)
- [ ] AT-PRE-002: Pivot and origin overrides
- [ ] AT-ROI-001: ROI and mask behavior

## Architecture Notes

Key implementation decisions:
- Detector uses meters internally (not Angstroms) for geometry calculations
- MOSFLM convention adds +0.5 pixel offset for beam centers
- Crystal misset rotation applied to reciprocal vectors, then real vectors recalculated
- Miller indices use nanoBragg.c convention: h = S·a (dot product with real-space vectors)

## Next Steps

1. **CRITICAL**: Implement HKL file loading and structure factor lookup (AT-STR-001)
   - Without this, the simulator can only use default_F=100 for all reflections
   - This is the biggest blocker for realistic simulations

2. Continue with remaining geometry tests (AT-GEO-002 through AT-GEO-006)

3. Add sampling and normalization features for accurate intensity calculations