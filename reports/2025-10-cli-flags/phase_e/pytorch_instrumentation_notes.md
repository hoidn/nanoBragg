# PyTorch Trace Instrumentation Notes - CLI-FLAGS-003 Phase E2

## Date
2025-10-05

## Objective
Generate PyTorch trace log matching C trace format for pixel (slow=1039, fast=685).

## Approach

### 1. Created Custom Trace Harness
**File:** `/home/ollie/Documents/tmp/nanoBragg/reports/2025-10-cli-flags/phase_e/trace_harness.py`

The trace harness:
- Loads configuration from A.mat and scaled.hkl
- Recreates the exact C command parameters in PyTorch config objects
- Enables trace_pixel debug output in the simulator
- Uses float64 precision for accurate comparison

### 2. Enhanced Simulator Trace Output
**File:** `/home/ollie/Documents/tmp/nanoBragg/src/nanobrag_torch/simulator.py`

**Lines Modified:** 1178-1337

Added comprehensive TRACE_PY outputs matching C trace format:
1. pix0_vector_meters (detector origin)
2. fdet_vec, sdet_vec (detector basis vectors)
3. pixel_pos_meters (pixel position in lab frame)
4. R_distance_meters, omega_pixel_sr, close_distance_meters, obliquity_factor
5. diffracted_vec, incident_vec (unit vectors)
6. lambda_meters, lambda_angstroms
7. scattering_vec_A_inv (in m^-1, matching C units!)
8. rot_a/b/c_angstroms, rot_a/b/c_star_A_inv (rotated lattice vectors)
9. hkl_frac, hkl_rounded (Miller indices)
10. F_latt_a/b/c, F_latt (lattice structure factors)
11. F_cell (unit cell structure factor)
12. I_before_scaling (intensity before physical scaling)
13. r_e_meters, r_e_sqr, fluence_photons_per_m2, steps
14. oversample_thick/polar/omega flags
15. capture_fraction, polar, omega_pixel, cos_2theta
16. I_pixel_final, floatimage_accumulated

**Key Fix:** Lines 1279-1287
- Added isinstance() checks to handle omega_pixel/polarization being scalars vs tensors
- Prevents TypeError when oversample > 1 (which passes None instead of tensor)

### 3. Configuration Mapping

**Crystal Configuration:**
- Loaded cell parameters from A.mat (MOSFLM matrix)
- N_cells = (36, 47, 29)
- phi_steps = 10
- osc_range = 0.1 degrees
- spindle_axis = (-1, 0, 0)

**Detector Configuration:**
- Convention: CUSTOM (with explicit basis vectors)
- pix0_override_m: [-0.216336293, 0.215205512, -0.230200866] (from mm to m)
- custom_fdet_vector: [0.999982, -0.005998, -0.000118]
- custom_sdet_vector: [-0.005998, -0.999970, -0.004913]
- custom_odet_vector: [-0.000088, 0.004914, -0.999988]
- distance_mm: 231.274660
- pixel_size_mm: 0.172
- detpixels: (2463, 2527) [spixels, fpixels]
- beam_center: Xbeam=217.742295, Ybeam=213.907080

**Beam Configuration:**
- wavelength_A: 0.976800
- fluence: 1e24 (calculated from flux * exposure / beamsize^2)
- incident_beam_direction: [0.00051387949, 0.0, -0.99999986] (manually overridden after simulator init)

### 4. Execution Command

```bash
env KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_e/trace_harness.py > reports/2025-10-cli-flags/phase_e/pytorch_trace.log 2>&1
```

## Output

**Location:** `/home/ollie/Documents/tmp/nanoBragg/reports/2025-10-cli-flags/phase_e/pytorch_trace.log`

**Line Count:** 40 TRACE_PY lines (matches C trace exactly)

**Format:** Each line follows `TRACE_PY: variable_name value1 value2 ...` with 15 significant digits

## Key Differences from C Trace (Expected)

1. **Numerical Precision:** PyTorch uses float64, minor differences expected due to different math libraries
2. **Coordinate Systems:** PyTorch properly handles unit conversions (mm→m, Å→m^-1)
3. **Vector Ordering:** All vectors match C ordering (x, y, z components)

## Validation

- All 40 trace variables present and accounted for
- Variable names match C trace format exactly
- Output precision set to 15 significant digits (%.15g format)
- No runtime errors or exceptions

## Notes

1. The simulator's trace functionality was designed to be extensible - adding new trace variables required minimal code changes
2. The CUSTOM detector convention properly accepts user-specified basis vectors and pix0_vector
3. The beam_vector override is necessary because CUSTOM convention defaults to MOSFLM beam direction
4. All production code paths are used - no re-derivations or parallel implementations
