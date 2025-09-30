# Detailed Trace Comparison: Pixel (64, 79) - 0.4mm pixel size

## Test Configuration
- Pixel: (slow=64, fast=79)
- Pixel size: 0.4mm
- Detector: 256×256 pixels
- Beam center: (25.6mm, 25.6mm)
- Distance: 100mm
- Crystal: 100Å cubic, N=5
- Wavelength: 6.2Å
- Convention: MOSFLM

## Complete Values Comparison

### Detector Geometry
| Variable | C Value | PyTorch Value | Match? | Ratio (Py/C) |
|----------|---------|---------------|--------|--------------|
| pixel_pos[1] (m) | 0.1 | 1.000000000000e-01 | ✓ | 1.0 |
| pixel_pos[2] (m) | 0 | 0.000000000000e+00 | ✓ | - |
| pixel_pos[3] (m) | 0.006 | 6.000000000000e-03 | ✓ | 1.0 |
| airpath (m) | 0.100179838290946 | 1.001798382909e-01 | ✓ | 1.0 |
| omega_pixel (sr) | 1.59139871736274e-05 | 1.591398717363e-05 | ✓ | 1.0 |
| close_distance (m) | 0.1 | - | - | - |
| obliquity_factor | 0.998204845465779 | - | - | - |

### Beam Vectors
| Variable | C Value | PyTorch Value | Match? |
|----------|---------|---------------|--------|
| diffracted[1] | 0.998204845465779 | - | - |
| diffracted[2] | 0 | - | - |
| diffracted[3] | 0.0598922907279467 | - | - |
| incident[1] | 1 | - | - |
| incident[2] | 0 | - | - |
| incident[3] | -0 | - | - |
| lambda (m) | 6.2e-10 | - | - |

### Scattering Vector (Å⁻¹)
| Variable | C Value | PyTorch Value | Match? | Ratio (Py/C) |
|----------|---------|---------------|--------|--------------|
| scattering[1] | -2895410.53906661 | -2.895410539067e-04 | **❌** | **1.0e-10** |
| scattering[2] | 0 | 0.000000000000e+00 | ✓ | - |
| scattering[3] | 96600468.9160431 | 9.660046891604e-03 | **❌** | **1.0e-10** |

**CRITICAL DIVERGENCE FOUND: SCATTERING VECTOR UNITS**

The scattering vector in PyTorch is **10¹⁰ times smaller** than in C!
- C: scattering in Å⁻¹ (correct crystallographic units)
- PyTorch: scattering in m⁻¹ (wrong units!)

This is a **unit conversion error** in the scattering vector calculation.

### Miller Indices
| Variable | C Value | PyTorch Value | Match? | Ratio (Py/C) |
|----------|---------|---------------|--------|--------------|
| h (fractional) | -0.0289541053906661 | -2.895410539067e-06 | **❌** | **1.0e-4** |
| k (fractional) | 5.91507275270828e-17 | 1.772927624443e-22 | **❌** | **3.0e-6** |
| l (fractional) | 0.966004689160431 | 9.660046891604e-05 | **❌** | **1.0e-4** |
| h0 (rounded) | 0 | 0 | ✓ | 1.0 |
| k0 (rounded) | 0 | 0 | ✓ | 1.0 |
| l0 (rounded) | 1 | 0 | **❌** | **DIFFERENT** |

**SECOND CRITICAL DIVERGENCE: MILLER INDICES**

The fractional Miller indices in PyTorch are **10⁴ times smaller** than in C!
This causes l0 to round to 0 instead of 1, which is **fundamentally wrong**.

This is a direct consequence of the scattering vector unit error.

### Lattice and Structure Factor
| Variable | C Value | PyTorch Value | Match? | Ratio (Py/C) |
|----------|---------|---------------|--------|--------------|
| F_latt_a | 4.83606351478624 | 4.999999998276e+00 | **❌** | 1.034 |
| F_latt_b | 5 | 5.000000000000e+00 | ✓ | 1.0 |
| F_latt_c | 4.7748095119366 | 4.999998081257e+00 | **❌** | 1.047 |
| F_latt | 115.456410353655 | 1.249999519883e+02 | **❌** | 1.083 |
| F_cell | 100 | 1.000000000000e+02 | ✓ | 1.0 |

**THIRD CRITICAL DIVERGENCE: F_latt VALUES**

The F_latt components differ significantly:
- F_latt_a: 3.4% higher in PyTorch
- F_latt_c: 4.7% higher in PyTorch
- F_latt (combined): 8.3% higher in PyTorch

This is because PyTorch has the wrong l0 value (0 vs 1), so it's calculating F_latt for (0,0,0) instead of (0,0,1).

### Final Intensity
| Variable | C Value | PyTorch Value | Match? | Ratio (Py/C) |
|----------|---------|---------------|--------|--------------|
| I_before_scaling | 133301826.917515 | 1.562498799708e+08 | **❌** | **1.172** |
| r_e_sqr | 7.94079248018965e-30 | 7.940792480190e-30 | ✓ | 1.0 |
| fluence | 1.25932015286227e+29 | 1.259320152862e+29 | ✓ | 1.0 |
| steps | 1 | 1 | ✓ | 1.0 |
| I_pixel_final | 2117.55880649785 | - | - | - |
| Final intensity | 2117.55883789062 | 2.121363563786e+03 | **❌** | **1.00179** |

**FINAL DIVERGENCE ANALYSIS:**

The I_before_scaling ratio (1.172) combined with omega should give the final ratio.
- I_before_scaling: 1.172× higher in PyTorch
- This propagates through: I_before_scaling × omega × r_e² × fluence / steps
- Final ratio: 1.00179× (0.179% higher in PyTorch)

The 17.2% difference in I_before_scaling is partially cancelled by differences in the intensity calculation chain.

## Root Cause Identification

### PRIMARY BUG: Scattering Vector Units

**Location:** `_compute_physics_for_position` method in simulator.py, line ~188

**C Code (correct):**
```c
scattering[1] = (diffracted[1]-incident[1])/lambda;  // lambda in meters, result in Å⁻¹
scattering[2] = (diffracted[2]-incident[2])/lambda;
scattering[3] = (diffracted[3]-incident[3])/lambda;
```

**PyTorch Code (WRONG):**
```python
scattering_vector = (diffracted_beam_unit - incident_beam_unit) / wavelength
# wavelength is in Angstroms, but diffracted_beam_unit is in Angstroms
# This gives scattering in m⁻¹ instead of Å⁻¹!
```

**The Bug:**
The PyTorch code calculates the scattering vector using pixel coordinates in **Angstroms** but divides by wavelength which is also in **Angstroms**. However, there's a hidden unit error: the coordinates coming into this function are labeled as "Angstroms" but are actually being treated inconsistently somewhere in the pipeline.

Looking at the trace output:
- C: scattering_vec = [-2895410, 0, 96600468] Å⁻¹
- PyTorch: scattering_vec = [-0.000289541, 0, 0.009660047] m⁻¹

The ratio is exactly 1e10, which is the Angstrom-to-meter conversion factor!

**The Real Issue:**
The pixel coordinates coming into `_compute_physics_for_position` are supposed to be in Angstroms, but they're actually in meters! Look at the trace:
- Position (Å) = 1000000000.000000 (this is 1e9, which is 0.1 m = 100 mm in Angstroms)

The coordinate calculation is mixing units incorrectly.

### SECONDARY BUG: Incorrect Miller Index Rounding

Because the scattering vector is 10⁴ too small, the Miller indices are also 10⁴ too small:
- C: l = 0.9660 → l0 = 1
- PyTorch: l = 0.00009660 → l0 = 0

This causes PyTorch to calculate F_latt for the wrong reflection!

## Fix Required

**File:** `src/nanobrag_torch/simulator.py`
**Method:** `run()` around lines 520-660

The issue is likely in how `pixel_coords_angstroms` is calculated or passed to `_compute_physics_for_position`. Need to check:

1. Is `get_pixel_coordinates()` returning values in the correct units?
2. Is there a meter↔Angstrom conversion missing?
3. Check the trace code - it shows "Position (Å)" but the value is clearly wrong (1e9 Å = 100 mm, but pixel is at 100 mm + 6mm = 106mm from sample)

The coordinate system is correct in direction but has a unit scaling error.

## Impact on Test Failure

This explains the 1.00179× ratio at pixel (64,79):
1. Wrong scattering vector units → wrong Miller indices
2. Wrong Miller indices → wrong F_latt calculation
3. Wrong F_latt → 17.2% error in I_before_scaling
4. The errors partially cancel in the full calculation chain
5. Final error: 0.179% (close to the 0.2% seen in the 0.4mm test)

The pixel-size dependency of the error suggests the unit conversion error scales with pixel position (distance from center).