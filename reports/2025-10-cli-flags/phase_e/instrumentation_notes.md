# C Trace Instrumentation Notes - Phase E1

## Metadata
- **Timestamp**: 2025-10-05
- **Commit Hash**: a3518b99b26b6ff82c85d8592429e666626be0b2
- **Task**: CLI-FLAGS-003 Phase E1 - Instrument C trace for pixel (slow=1039, fast=685)
- **Author**: Claude Code Agent

## Summary
The C code in `golden_suite_generator/nanoBragg.c` already contained comprehensive trace instrumentation for pixel-level debugging. The only modification required was to add a `-dump_pixel` alias to the existing `-trace_pixel` command-line argument to match the supervisor's expected command syntax.

## Source Files Touched
- **File**: `/home/ollie/Documents/tmp/nanoBragg/golden_suite_generator/nanoBragg.c`
- **Line Range**: Line 1114 (command-line argument parsing)
- **Change Type**: Added alias for `-dump_pixel` flag

## Existing Trace Infrastructure
The C code already includes trace output for all required variables when compiled with `-DTRACING=1` (which is the default in the Makefile):

### Trace Variables (in order of computation):
1. **pix0_vector** (line 2937) - Detector origin in lab frame (meters)
2. **fdet_vector** (line 2938) - Fast detector basis vector (unitless)
3. **sdet_vector** (line 2939) - Slow detector basis vector (unitless)
4. **pixel_pos_meters** (line 2940) - Pixel position in lab frame (meters)
5. **R_distance_meters** (line 2941) - Air path distance to pixel (meters)
6. **omega_pixel_sr** (line 2942) - Solid angle subtended by pixel (steradians)
7. **diffracted_vec** (line 2945) - Diffracted beam unit vector
8. **incident_vec** (line 2946) - Incident beam unit vector
9. **lambda_meters** (line 2947) - X-ray wavelength (meters)
10. **lambda_angstroms** (line 2948) - X-ray wavelength (Angstroms)
11. **scattering_vec_A_inv** (line 2949) - Scattering vector (1/Angstroms)
12. **rot_a_angstroms** (line 3051) - Rotated real-space a vector (Angstroms)
13. **rot_b_angstroms** (line 3052) - Rotated real-space b vector (Angstroms)
14. **rot_c_angstroms** (line 3053) - Rotated real-space c vector (Angstroms)
15. **rot_a_star_A_inv** (line 3054) - Rotated reciprocal a* vector (1/Angstroms)
16. **rot_b_star_A_inv** (line 3055) - Rotated reciprocal b* vector (1/Angstroms)
17. **rot_c_star_A_inv** (line 3056) - Rotated reciprocal c* vector (1/Angstroms)
18. **hkl_frac** (line 3057) - Fractional Miller indices
19. **hkl_rounded** (line 3058) - Nearest integer Miller indices
20. **F_latt_a** (line 3083) - Lattice structure factor component (a direction)
21. **F_latt_b** (line 3084) - Lattice structure factor component (b direction)
22. **F_latt_c** (line 3085) - Lattice structure factor component (c direction)
23. **F_latt** (line 3086) - Total lattice structure factor
24. **F_cell** (line 3261) - Unit cell structure factor
25. **I_before_scaling** (line 3295) - Intensity before scaling corrections
26. **r_e_meters** (line 3296) - Classical electron radius (meters)
27. **r_e_sqr** (line 3297) - Classical electron radius squared
28. **fluence_photons_per_m2** (line 3298) - Photon fluence
29. **capture_fraction** (line 3303) - Detector capture fraction
30. **polar** (line 3304) - Polarization correction factor
31. **omega_pixel** (line 3305) - Solid angle (final value)
32. **cos_2theta** (line 3306) - Cosine of scattering angle
33. **I_pixel_final** (line 3307) - Final pixel intensity (photons)
34. **floatimage_accumulated** (line 3308) - Accumulated value in output array

### Trace Output Format
All trace output uses the `TRACE_C:` prefix for easy filtering:
```
TRACE_C: variable_name value1 value2 value3
TRACE_C: scalar_name value
```

Precision: 15 significant digits (format: `%.15g`)

### Units in Trace Output
- **Geometry vectors**: Meters (not Angstroms) for lab-frame positions
- **Unit vectors**: Dimensionless
- **Wavelength**: Both meters and Angstroms provided
- **Reciprocal vectors**: 1/Angstroms
- **Real-space vectors**: Angstroms
- **Solid angle**: Steradians
- **Intensity**: Photons

## Changes Made

### Modification 1: Add `-dump_pixel` alias
**Purpose**: Enable supervisor command to use `-dump_pixel` syntax as documented in `input.md`

**Before** (line 1114):
```c
if(strstr(argv[i], "-trace_pixel") && (argc > (i+2)))
```

**After** (line 1114):
```c
if((strstr(argv[i], "-trace_pixel") || strstr(argv[i], "-dump_pixel")) && (argc > (i+2)))
```

**Rationale**: The supervisor command in `input.md` line 32 uses `-dump_pixel 1039 685`, but the C code originally only recognized `-trace_pixel`. This change adds backward-compatible support for both flags.

## Build Commands Executed

```bash
timeout 120 make -C /home/ollie/Documents/tmp/nanoBragg/golden_suite_generator
```

### Build Output:
```
make: Entering directory '/home/ollie/Documents/tmp/nanoBragg/golden_suite_generator'
gcc -O2 -fno-fast-math -ffp-contract=off -DTRACING=1 -fopenmp -o nanoBragg nanoBragg.c -lm -fopenmp
make: Leaving directory '/home/ollie/Documents/tmp/nanoBragg/golden_suite_generator'
```

**Build Status**: ✓ SUCCESS

### Compiler Flags Used:
- `-O2`: Moderate optimization level
- `-fno-fast-math`: Preserve IEEE floating-point semantics
- `-ffp-contract=off`: Disable floating-point contraction
- `-DTRACING=1`: Enable trace output macros
- `-fopenmp`: Enable OpenMP parallelization
- `-lm`: Link math library

## Recompilation Necessity
**Yes** - Recompilation was necessary for the following reasons:
1. Modified source code requires rebuilding the binary
2. The `-DTRACING=1` flag must be present to enable trace output
3. The Makefile already includes the correct flags for trace builds

## Usage

### Command-Line Syntax (Both Accepted):
```bash
# Original syntax
./golden_suite_generator/nanoBragg -trace_pixel <spixel> <fpixel> [other args...]

# New supervisor-compatible syntax
./golden_suite_generator/nanoBragg -dump_pixel <spixel> <fpixel> [other args...]
```

### Example (from supervisor command):
```bash
NB_C_BIN=./golden_suite_generator/nanoBragg timeout 120 "$NB_C_BIN" \
  -mat A.mat -floatfile img.bin -hkl scaled.hkl -nonoise -nointerpolate \
  -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 \
  -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 \
  -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 \
  -odet_vector -0.000088 0.004914 -0.999988 \
  -sdet_vector -0.005998 -0.999970 -0.004913 \
  -fdet_vector 0.999982 -0.005998 -0.000118 \
  -pix0_vector_mm -216.336293 215.205512 -230.200866 \
  -beam_vector 0.00051387949 0.0 -0.99999986 \
  -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 \
  -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 \
  -dump_pixel 1039 685 2>&1 | tee reports/2025-10-cli-flags/phase_e/c_trace.log
```

### Expected Output:
All trace output will be prefixed with `TRACE_C:` and can be filtered using grep:
```bash
grep "^TRACE_C:" reports/2025-10-cli-flags/phase_e/c_trace.log
```

## Trace Configuration
When the trace pixel is set, the code prints:
```
TRACE_CONFIG: tracing pixel (spixel=1039, fpixel=685)
```

This confirms that trace instrumentation is active for the specified pixel.

## Verification Checklist
- [x] All required variables are traced (9 primary + 25 additional)
- [x] Trace output uses consistent `TRACE_C:` prefix
- [x] 15 significant digits for floating-point values
- [x] Units documented and consistent with component contracts
- [x] `-dump_pixel` alias added for supervisor compatibility
- [x] C code compiles successfully
- [x] Build uses `-DTRACING=1` flag
- [x] No compilation warnings or errors

## Next Steps (Phase E2)
After generating the C trace log, the PyTorch trace will be captured using:
```bash
python scripts/debug_pixel_trace.py [args...]
```

Compare the two trace logs line-by-line to identify any physics discrepancies between the C and PyTorch implementations.

## References
- Supervisor instructions: `/home/ollie/Documents/tmp/nanoBragg/input.md` lines 28-35
- Debugging workflow: `docs/debugging/debugging.md`
- Component contracts: `docs/architecture/`
