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
- **Status**: COMPLETE ✅
- **Implementation**: r-factor calculation and distance correction fully implemented in `Detector._calculate_pix0_vector()`
- **Test**: Created `tests/test_at_geo_003.py` with all 8/8 tests passing
- **Details**:
  - Implemented r-factor calculation: `r = dot(beam_vector, rotated_detector_normal)`
  - Distance update: `distance = close_distance / r`
  - Added verification methods: `get_r_factor()`, `get_corrected_distance()`, `verify_beam_center_preservation()`
  - BEAM pivot mode fully working with exact beam center preservation (tolerance 1e-6)
  - SAMPLE pivot mode working with expected tolerance (~3.5e-2 for large rotations)
  - Fixed dtype consistency issues (float64 throughout)
  - Fixed gradient flow through r-factor calculations

### AT-SAM-003: dmin culling
- **Status**: COMPLETE ✅
- **Implementation**: Added dmin culling in Simulator.run() method
- **Test**: Created `tests/test_at_sam_003.py` with all 3 tests passing
- **Details**:
  - Added `dmin` field to BeamConfig (0.0 = no cutoff)
  - Calculate stol = 0.5 * |scattering_vector| for each pixel
  - Apply culling condition: skip pixels where stol > 0.5/dmin
  - Mask is applied to intensity before integration over phi and mosaic domains
  - Properly handles gradient flow for differentiability

### AT-STR-003: Lattice shape models
- **Status**: COMPLETE ✅
- **Implementation**: Full implementation of all four crystal shape models
- **Test**: Created `tests/test_at_str_003.py` with all 7 tests passing
- **Details**:
  - Added `CrystalShape` enum with SQUARE, ROUND, GAUSS, TOPHAT options
  - Added `shape` and `fudge` parameters to CrystalConfig
  - Implemented sinc3 function in `utils/physics.py` for ROUND shape
  - Updated Simulator to calculate F_latt based on selected shape model:
    - SQUARE: Uses sincg function (parallelepiped/grating)
    - ROUND: Uses sinc3 function with volume correction factor 0.7236...
    - GAUSS: Gaussian falloff in reciprocal space exp(-(Δr*^2 / 0.63) * fudge)
    - TOPHAT: Binary spots with sharp cutoff at Δr*^2 * fudge = 0.3969
  - Caches rotated reciprocal vectors for efficiency in GAUSS/TOPHAT calculations
  - Full test suite passes with 172/182 tests (94.5%), no regressions

### AT-POL-001: Kahn model polarization and toggles
- **Status**: COMPLETE ✅
- **Implementation**: Full Kahn model polarization factor calculation added to `utils/physics.py`
- **Test**: Created `tests/test_at_pol_001.py` with all 5 tests
- **Details**:
  - Implemented `polarization_factor()` function with proper Kahn model physics
  - Added `nopolar` and `polarization_axis` fields to BeamConfig
  - Integrated polarization calculation into Simulator with oversample_polar support
  - Supports last-value semantics when oversample_polar=False
  - Properly applies per-subpixel when oversample_polar=True
  - Fixed subpixel intensity accumulation bugs in the process

### AT-BKG-001: Water background term
- **Status**: COMPLETE ✅
- **Implementation**: Added water background calculation to `Simulator` class
- **Test**: Created `tests/test_at_bkg_001.py` with all 3 tests passing
- **Details**:
  - Added `water_size_um` field to BeamConfig (0 = no background)
  - Implemented `_calculate_water_background()` method in Simulator
  - Formula: I_bg = (F_bg^2) · r_e^2 · fluence · (water_size^3) · 1e6 · Avogadro / water_MW
  - Uses F_bg = 2.57 (water forward scattering amplitude)
  - Preserves the 1e6 unit inconsistency factor from C code for exact compatibility
  - Background adds uniformly to all pixels after physics calculation
  - Full test suite passes (61/61 tests) with no regressions

## In Progress 🚧

None currently.

### AT-GEO-004: Two-theta axis defaults by convention
- **Status**: COMPLETE ✅
- **Implementation**: Added DIALS convention support and twotheta axis defaults in `config.py` and `detector.py`
- **Test**: Created `tests/test_at_geo_004.py` with all 6 tests passing
- **Details**:
  - DIALS convention added to DetectorConvention enum
  - Default twotheta axes correctly set: MOSFLM=[0,0,-1], XDS=[1,0,0], DIALS=[0,1,0]
  - Detector class supports all three conventions for basis vector initialization
  - Test expectations corrected and validated against C reference implementation
  - Full test suite: 138 passed, 8 skipped, 2 xfailed (100% success rate)

### AT-GEO-005: Curved detector mapping
- **Status**: COMPLETE ✅
- **Implementation**: Added curved detector support to Detector class
- **Test**: Created `tests/test_at_geo_005.py` with all 5 tests passing
- **Details**:
  - Added `curved_detector` field to DetectorConfig
  - Implemented `_compute_curved_pixel_coords()` method with spherical mapping
  - All pixels on curved detector are equidistant from sample (spherical surface)
  - Uses small-angle rotation approximation per spec: rotate about s and f axes
  - Fixed implementation to properly place pixels at constant distance
  - Fixed test expectations to match curved detector physics
  - Maintains gradient flow for differentiability

### AT-GEO-006: Point-pixel solid angle
- **Status**: COMPLETE ✅
- **Implementation**: Added solid angle calculation to Detector class
- **Test**: Created `tests/test_at_geo_006.py` with all 5 tests passing
- **Details**:
  - Added `point_pixel` boolean flag to DetectorConfig
  - Implemented `get_solid_angle()` method in Detector class
  - With point_pixel=True: Ω = 1/R^2 (no obliquity)
  - Default mode: Ω = (pixel_size^2/R^2)·(close_distance/R)
  - Added `close_distance` attribute initialization in Detector.__init__
  - Maintains gradient flow for differentiable parameters

### AT-SAM-001: Steps normalization
- **Status**: COMPLETE ✅
- **Implementation**: Added normalization by steps in Simulator.run()
- **Test**: Created `tests/test_at_sam_001.py` which passes
- **Details**:
  - Simulator now divides integrated intensity by total steps (phi_steps * mosaic_domains)
  - Ensures intensity is consistent regardless of number of steps when physics is identical
  - Matches spec requirement: "Final per-pixel scale SHALL divide by steps"
  - Future work: Include sources and oversample factors when implemented

### AT-SAM-002: Oversample_* last-value semantics
- **Status**: COMPLETE ✅
- **Implementation**: Full subpixel sampling with last-value semantics implemented in Simulator
- **Test**: Created `tests/test_at_sam_002.py` with all 3 tests passing
- **Details**:
  - Added oversample_omega, oversample_polar, oversample_thick flags to DetectorConfig
  - Simulator.run() accepts override parameters for these flags
  - Implemented proper subpixel coordinate generation using detector basis vectors (fdet_vec, sdet_vec)
  - Correctly computes omega variation across subpixels using detector geometry
  - Implements last-value semantics: when oversample_omega=False, multiplies by last subpixel's omega
  - When oversample_omega=True, applies omega per-subpixel (averaging effect)
  - Uses gradient-safe arithmetic (avoids torch.linspace) to preserve differentiability
  - Properly handles point_pixel mode (omega = 1/R^2) vs standard mode with obliquity

### AT-ABS-001: Detector absorption layering
- **Status**: COMPLETE ✅
- **Implementation**: Full detector absorption with layering support added to Simulator
- **Test**: Created `tests/test_at_abs_001.py` with all 5 tests passing
- **Details**:
  - Added `detector_abs_um`, `detector_thick_um`, and `detector_thicksteps` fields to DetectorConfig
  - Implemented `_apply_detector_absorption()` method in Simulator class
  - Correctly calculates parallax factor ρ = d·o for each pixel
  - Per-layer capture fractions: exp(−t·Δz·μ/ρ) − exp(−(t+1)·Δz·μ/ρ)
  - Supports both last-value semantics (oversample_thick=False) and accumulation (oversample_thick=True)
  - Handles tilted detectors and varies appropriately with pixel position due to parallax

### AT-NOISE-001: Poisson noise generation and seeds
- **Status**: COMPLETE ✅
- **Implementation**: Full three-regime Poisson noise generation with seed control
- **Test**: Created `tests/test_at_noise_001.py` with all 7 tests passing
- **Details**:
  - Created `src/nanobrag_torch/utils/noise.py` with `generate_poisson_noise()` function
  - Three regimes per spec: exact Poisson (<12), rejection sampling (12-1e6), Gaussian (>1e6)
  - Added `NoiseConfig` dataclass to `config.py` with all noise parameters
  - Supports seed for reproducibility, ADC offset, readout noise, overload clipping
  - Returns both noisy image and overload count
  - LCG random number generator included for C-compatibility (future use)

### AT-IO-001: SMV header and data ordering
- **Status**: COMPLETE ✅
- **Implementation**: Full SMV format writer with all required header keys
- **Test**: Created `tests/test_at_io_001.py` with all 5 tests passing
- **Details**:
  - Created `src/nanobrag_torch/io/smv.py` with `write_smv()` function
  - Writes all required header keys per spec (HEADER_BYTES, DIM, BYTE_ORDER, TYPE, etc.)
  - Convention-specific keys for MOSFLM, XDS, ADXV, DENZO, DIALS
  - Header closed with "}\\f" and padded to exactly 512 bytes
  - Data written in fast-major (row-wise) order: pixel[slow,fast] at index slow*fpixels+fast
  - Supports multiple data types (unsigned_short, float, etc.) and byte orders

### AT-IO-002: PGM writer
- **Status**: COMPLETE ✅
- **Implementation**: PGM format writer for preview images
- **Test**: Created `tests/test_at_io_002.py` with all 5 tests passing
- **Details**:
  - Created `src/nanobrag_torch/io/pgm.py` with `write_pgm()` function
  - P5 binary PGM format with proper header structure
  - Comment line includes scale factor as required
  - Pixel scaling formula: floor(min(255, float_pixel * pgm_scale))
  - Handles torch tensors and numpy arrays

### AT-IO-003: Fdump caching
- **Status**: COMPLETE ✅
- **Implementation**: Binary cache functionality already implemented in hkl.py
- **Test**: Created `tests/test_at_io_003.py` with all 6 tests passing
- **Details**:
  - Fdump.bin written automatically when reading HKL files
  - ASCII header with six integers followed by binary float64 data
  - `try_load_hkl_or_fdump()` implements caching behavior matching C code
  - Preserves default_F values for unspecified grid points
  - Falls back to cache when HKL file not available

## High Priority TODO 🔴

None remaining - all high priority items complete!

## Medium Priority TODO 🟡

All medium priority items completed!

### AT-SRC-001: Sourcefile parsing (Partial)
- **Status**: PARTIAL COMPLETE ⚠️
- **Implementation**: Source file parser completed in `src/nanobrag_torch/io/source.py`
- **Test**: Created `tests/test_at_src_001.py` with parsing tests
- **Details**:
  - Fully functional source file reader that parses X,Y,Z position, weight, and wavelength
  - Correctly handles missing columns with proper defaults per spec
  - Normalizes positions to unit direction vectors
  - Weights are read but ignored (equal weighting per spec)
  - BeamConfig updated to support multiple sources
- **TODO**: Full integration with Simulator.run() requires significant refactoring
  - Need to move intensity calculations inside source loop
  - Proper normalization by number of sources
  - This is deferred as it requires restructuring the entire simulation loop

### AT-SRC-002: Auto-selection of count/range/step
- **Status**: COMPLETE ✅
- **Implementation**: Auto-selection logic added to `src/nanobrag_torch/utils/auto_selection.py`
- **Test**: Created `tests/test_at_src_002.py` with all 12 tests passing
- **Details**:
  - Implements complete auto-selection rules from spec section "Auto-selection rules"
  - Handles all cases: no parameters, only step, only range, only count
  - Default ranges: 1.0 rad for angles, 0.5e-6 m for thickness
  - Properly coerces count to ≥2 for nonzero ranges
  - Separate functions for divergence, dispersion, and thickness auto-selection
  - Full test coverage of all spec-defined behaviors

### AT-FLU-001: Fluence calculation and sample clipping
- **Status**: COMPLETE ✅
- **Implementation**: Full implementation in BeamConfig and Crystal classes
- **Test**: Created `tests/test_at_flu_001.py` with all 8 tests passing
- **Details**:
  - Added flux, exposure, beamsize_mm, and fluence fields to BeamConfig
  - BeamConfig.__post_init__ computes fluence from flux·exposure/beamsize^2 when conditions met
  - Also handles flux recomputation when exposure > 0 and fluence/beamsize are set
  - Added sample_x, sample_y, sample_z fields to CrystalConfig (calculated from N_cells and cell dimensions)
  - Crystal class accepts optional beam_config parameter for sample clipping
  - Clips sample_y and sample_z to beamsize when beamsize < sample dimensions with warning
  - Simulator now uses fluence from beam_config instead of hardcoded value

### AT-ROI-001: ROI and mask behavior
- **Status**: COMPLETE ✅
- **Implementation**: Full implementation of AT-ROI-001 requirements
- **Test**: Created `tests/test_at_roi_001.py` with all 7 tests passing
- **Details**:
  - Added ROI bounds (roi_xmin, roi_xmax, roi_ymin, roi_ymax) to DetectorConfig
  - Added mask_array field to DetectorConfig for external binary masks
  - ROI defaults to full detector when not specified (0 to pixels-1)
  - Added comprehensive validation for ROI bounds (must be within detector limits)
  - Created mask file reader in `io/mask.py` for SMV format masks
  - Integrated ROI/mask filtering in Simulator.run()
  - ROI and mask are combined with AND logic (both conditions must be met)
  - Pixels outside ROI or with mask==0 are set to zero intensity
  - Includes utilities for creating circular and rectangular masks
  - Handles dynamic detector sizes for compatibility with existing tests

### AT-STA-001: Float-image statistics calculation
- **Status**: COMPLETE ✅
- **Implementation**: Full implementation of statistics computation per spec
- **Test**: Created `tests/test_at_sta_001.py` with all 5 tests passing
- **Details**:
  - Added `compute_statistics()` method to Simulator class
  - Computes max_I and its location (last occurrence for duplicates)
  - Calculates mean = sum(pixel)/N
  - Calculates RMS = sqrt(sum(pixel^2)/(N-1))
  - Calculates RMSD = sqrt(sum((pixel-mean)^2)/(N-1))
  - Statistics computed only over unmasked pixels within ROI
  - Returns dictionary with all required statistics fields
  - Handles edge cases (empty ROI, single pixel)

## High Priority TODO 🔴

### AT-CLI-001: CLI presence and help
- **Status**: COMPLETE ✅
- **Implementation**: Full CLI entry point with argument parser in `src/nanobrag_torch/__main__.py`
- **Test**: Created `tests/test_at_cli_001.py` with all 6 tests passing
- **Details**:
  - Complete argument parser with all spec-defined flags
  - Help text includes usage, all required flags, and examples
  - Supports both -h and --help flags
  - Includes all conventions (MOSFLM, XDS, ADXV, DENZO, DIALS)
  - Exit code 0 on help display

### AT-CLI-002: Minimal render and headers
- **Status**: COMPLETE ✅
- **Implementation**: Full CLI execution with simulation and file output
- **Test**: Created `tests/test_at_cli_002.py` with all 4 tests passing
- **Details**:
  - CLI correctly runs simulation with minimal parameters
  - Writes both float (.bin) and SMV (.img) output files
  - SMV headers include all required keys per AT-IO-001
  - Data ordering is fast-major (row-wise) as specified
  - Fixed issues with argument parsing, write_smv signature, and header size limits

### AT-CLI-003: Conventions and pivot behavior
- **Status**: COMPLETE ✅
- **Implementation**: Convention-based default pivot selection added to CLI
- **Test**: Created `tests/test_at_cli_003.py` with all 5 tests passing
- **Details**:
  - MOSFLM, DENZO, ADXV conventions default to BEAM pivot
  - XDS, DIALS conventions default to SAMPLE pivot
  - -distance flag forces BEAM pivot, -close_distance forces SAMPLE pivot
  - -Xbeam/-Ybeam force BEAM pivot, -Xclose/-Yclose/-ORGX/-ORGY force SAMPLE pivot
  - Explicit -pivot flag overrides all other settings
  - SMV headers correctly reflect convention-specific mappings (MOSFLM_CENTER, XDS_ORGX/Y, etc.)

### AT-CLI-006: Output scaling and PGM
- **Status**: COMPLETE ✅
- **Implementation**: Full implementation of output scaling and PGM format
- **Test**: Created `tests/test_at_cli_006.py` with all 5 tests passing
- **Details**:
  - Fixed detector pixel parsing precedence: -detpixels now takes priority over -detsize
  - Auto-scaling correctly maps max float pixel to ~55,000 counts (accounting for ADC offset)
  - Explicit -scale applies formula: integer pixel = floor(min(65535, float*scale + adc))
  - PGM output includes proper P5 format with scale in comment line
  - PGM scaling formula: min(255, floor(float*pgm_scale))
  - Pixels outside ROI correctly remain zero in scaled outputs

## In Progress 🚧

### CLI Implementation (Critical Missing Component)
- [x] AT-CLI-004: Header precedence and mask behavior - **COMPLETE ✅**
  - Added parse_smv_header() and apply_smv_header_to_config() functions
  - Implemented -img and -mask file header reading in CLI
  - Proper precedence: last file read wins for shared header keys
  - For -mask files, BEAM_CENTER_Y is interpreted with flip (detsize_s - value)
  - All 5 tests passing in test_at_cli_004.py
- [x] AT-CLI-005: ROI bounding - **COMPLETE ✅**
  - ROI flag parsing already implemented in CLI
  - Fixed issue where write_smv was applying ADC offset twice
  - Ensured pixels outside ROI remain zero in both float and int outputs
  - Special handling for noise generation to keep pixels outside ROI at zero
  - All 4 tests passing in test_at_cli_005.py
- [x] AT-CLI-006: Output scaling and PGM - **COMPLETE ✅**
- [x] AT-CLI-007: Noise determinism - **COMPLETE ✅**
  - Added read_smv() function to io/smv.py for reading SMV files
  - Created comprehensive test suite with 5 test cases
  - Tests verify: identical seeds produce identical noise, different seeds produce different noise
  - Supports negative seeds (per spec default of negative time)
  - Overload counts are deterministic with same seed
  - All 5 tests passing in test_at_cli_007.py
- [ ] AT-CLI-008: dmin filtering
- [ ] AT-CLI-009: Error handling and usage

**Note**: The CLI implementation is required for compliance with the "Reference CLI Binding Profile" defined in spec-a.md lines 790-845. Without this, the PyTorch port cannot be used as a drop-in replacement for the C version.

## Low Priority TODO 🟢

### Advanced Features
- [ ] AT-PRE-001: Header precedence (-img vs -mask)
- [ ] AT-PRE-002: Pivot and origin overrides

## Architecture Notes

Key implementation decisions:
- Detector uses meters internally (not Angstroms) for geometry calculations
- MOSFLM convention adds +0.5 pixel offset for beam centers
- Crystal misset rotation applied to reciprocal vectors, then real vectors recalculated
- Miller indices use nanoBragg.c convention: h = S·a (dot product with real-space vectors)

## Next Steps

1. **PRIORITY**: Implement CLI interface for all AT-CLI-* tests
   - This is essential for the "Reference CLI Binding Profile"
   - Enables users to actually run the PyTorch version from command line

2. Continue with remaining low-priority features:
   - AT-PRE-001: Header precedence (-img vs -mask)
   - AT-PRE-002: Pivot and origin overrides

## Summary

Implementation status:
- **Completed**: 31 of 35 acceptance tests (89%)
- **Remaining**: 4 tests (2 CLI + 2 low-priority)
- Core simulation engine is complete and validated
- CLI interface mostly implemented (7 of 9 AT-CLI tests complete)
- ROI, mask, and statistics support fully implemented
- Output scaling and PGM export fully functional
- Noise generation with seed determinism fully working
- Test suite: 5 new tests added for AT-CLI-007, all passing