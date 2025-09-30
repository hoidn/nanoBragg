# Trace Comparison: Pixel (64, 79) - 0.4mm pixel size

## Test Configuration
- Pixel: (slow=64, fast=79)
- Pixel size: 0.4mm
- Detector: 256×256 pixels
- Beam center: (25.6mm, 25.6mm)
- Distance: 100mm
- Crystal: 100Å cubic, N=5
- Wavelength: 6.2Å
- Convention: MOSFLM

## Key Values Comparison

### Detector Geometry
| Variable | C Value | PyTorch Value | Match? | Notes |
|----------|---------|---------------|--------|-------|
| pixel_pos[1] (m) | 0.1 | 1.000000000000e-01 | ✓ | X coordinate |
| pixel_pos[2] (m) | 0 | 0.000000000000e+00 | ✓ | Y coordinate |
| pixel_pos[3] (m) | 0.006 | 6.000000000000e-03 | ✓ | Z coordinate |
| airpath (m) | 0.100179838290946 | 1.001798382909e-01 | ✓ | Distance to pixel |
| omega_pixel (sr) | 1.59139871736274e-05 | 1.591398717363e-05 | ✓ | Solid angle |
| close_distance (m) | 0.1 | - | - | |
| obliquity_factor | 0.998204845465779 | - | - | close_distance/airpath |

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

### Scattering Vector
| Variable | C Value | PyTorch Value | Match? |
|----------|---------|---------------|--------|
| scattering[1] (Å⁻¹) | -2895410.53906661 | - | - |
| scattering[2] (Å⁻¹) | 0 | - | - |
| scattering[3] (Å⁻¹) | 96600468.9160431 | - | - |

### Miller Indices
| Variable | C Value | PyTorch Value | Match? |
|----------|---------|---------------|--------|
| h (fractional) | -0.0289541053906661 | - | - |
| k (fractional) | 5.91507275270828e-17 | - | - |
| l (fractional) | 0.966004689160431 | - | - |
| h0 (rounded) | 0 | - | - |
| k0 (rounded) | 0 | - | - |
| l0 (rounded) | 1 | - | - |

### Lattice and Structure Factor
| Variable | C Value | PyTorch Value | Match? |
|----------|---------|---------------|--------|
| F_latt_a | 4.83606351478624 | - | - |
| F_latt_b | 5 | - | - |
| F_latt_c | 4.7748095119366 | - | - |
| F_latt | 115.456410353655 | - | - |
| F_cell | 100 | - | - |

### Final Intensity
| Variable | C Value | PyTorch Value | Match? | Ratio (Py/C) |
|----------|---------|---------------|--------|--------------|
| I_before_scaling | 133301826.917515 | - | - | - |
| r_e_sqr | 7.94079248018965e-30 | 7.940792480190e-30 | ✓ | 1.0 |
| fluence | 1.25932015286227e+29 | 1.259320152862e+29 | ✓ | 1.0 |
| steps | 1 | 1 | ✓ | 1.0 |
| I_pixel_final | 2117.55880649785 | - | - | - |
| Final intensity | 2117.55883789062 | 2.121363563786e+03 | **❌** | **1.00179** |

## Key Finding

**DIVERGENCE IDENTIFIED:**
- **Variable:** Final pixel intensity
- **C Value:** 2117.55883789062
- **PyTorch Value:** 2121.363563786
- **Ratio (Py/C):** 1.00179 (0.179% higher in PyTorch)

This 1.00179× ratio at pixel (64, 79) is consistent with the off-center error pattern observed in the test (ratio~1.002 for off-center pixels).

## Analysis

The PyTorch trace is less detailed - it doesn't show intermediate values like:
- Miller indices (h, k, l)
- Lattice factors (F_latt_a, F_latt_b, F_latt_c)
- Structure factor (F_cell)
- I_before_scaling

This makes it difficult to pinpoint exactly where the divergence occurs. We need to enhance the PyTorch trace to match the C trace granularity.

## Next Steps

1. Add detailed tracing to PyTorch implementation to match C trace output
2. Compare Miller indices calculation
3. Compare F_latt calculation
4. Compare intensity accumulation formula