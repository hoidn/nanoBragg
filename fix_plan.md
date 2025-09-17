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

## In Progress 🚧

None currently.

## High Priority TODO 🔴

### Structure Factors & HKL Loading (AT-STR-001, AT-STR-002)
- **Priority**: CRITICAL - Required for any non-trivial simulation
- **Tasks**:
  - [ ] Implement HKL file reader in `Crystal` class
  - [ ] Implement Fdump.bin binary cache writer/reader
  - [ ] Implement nearest-neighbor lookup for structure factors
  - [ ] Implement tricubic interpolation with fallback
  - [ ] Add tests for in-range and out-of-range queries

### Beam Model & Geometry (AT-GEO-002, AT-GEO-003, AT-GEO-004)
- [ ] AT-GEO-002: Pivot defaults and overrides
- [ ] AT-GEO-003: r-factor distance update and beam-center preservation
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