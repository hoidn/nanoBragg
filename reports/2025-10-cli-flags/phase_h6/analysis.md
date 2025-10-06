# Phase H6c Findings: First Divergence Analysis

**Date:** 2025-10-26
**Phase:** H6c Trace Diff Analysis
**Objective:** Identify first divergence between C and PyTorch pix0 traces

## Summary

**First Divergence Identified:** `beam_center_m` values differ by a factor of ~10³ (millimeters vs meters)

### Critical Finding

The C trace shows:
```
TRACE_C:beam_center_m=Xclose:0.000211818 Yclose:0.000217322 pixel_mm:0.172
```

The PyTorch trace shows:
```
TRACE_PY:beam_center_m=Xclose:0.217742295 Yclose:0.21390708 pixel_mm:0.172
```

**Diagnosis:** PyTorch is logging `beam_center_m` values in **millimeters**, while the C code logs them in **meters**. This is purely a logging/units issue in the trace output, NOT necessarily a calculation error.

## Detailed Comparison

| Variable | C Value (meters) | PyTorch Value (mm as m) | Ratio | Issue |
| --- | --- | --- | --- | --- |
| Xclose | 0.000211818 m | 0.217742295 (mm) | ~1028× | Unit mismatch in trace |
| Yclose | 0.000217322 m | 0.21390708 (mm) | ~984× | Unit mismatch in trace |
| Fclose_m | 0.217742295 m | 0.217742295 m | 1.0 | ✓ Correct |
| Sclose_m | 0.21390708 m | 0.21390708 m | 1.0 | ✓ Correct |

### Key Observations

1. **Xclose/Yclose logging mismatch**: PyTorch trace is outputting the mm values directly without converting to meters for the trace output
2. **Fclose/Sclose are correct**: These derived values match exactly, suggesting the actual calculation is using proper units
3. **Subsequent calculations appear correct**: The term_fast/term_slow/term_close values are very close, indicating the pix0 calculation itself may be correct

## Hypothesis

The 1.1mm pix0 discrepancy found in Phase H5c may NOT be due to unit conversion errors in the calculation, but rather:

1. **Different interpretation of beam_center input**: C may be treating Xclose/Yclose differently in the CUSTOM convention + SAMPLE pivot case
2. **Missing transform or offset**: There may be a CUSTOM-specific transform applied in C that PyTorch is missing

## Numeric Comparison Table

### Beam Center Values
| Source | Xclose | Yclose | Unit |
| --- | --- | --- | --- |
| C (from trace) | 0.000211818 | 0.000217322 | meters |
| PyTorch (logged as m) | 0.217742295 | 0.21390708 | **actually mm** |
| PyTorch (corrected) | 0.000217742 | 0.000213907 | meters |

### Derived Values (All in Meters)
| Variable | C | PyTorch | Delta | % Diff |
| --- | --- | --- | --- | --- |
| Fclose_m | 0.217742295 | 0.217742295 | 0 | 0% |
| Sclose_m | 0.21390708 | 0.21390708 | 0 | 0% |
| close_distance_m | 0.231271826 | 0.231271809 | -1.7e-8 | 0% |
| ratio | 0.999987747 | 0.999987815 | +6.8e-8 | 0% |
| distance_m | 0.23127466 | 0.231274628 | -3.2e-8 | 0% |

### Pix0 Components Before Rotation
| Component | C (m) | PyTorch (m) | Delta (μm) |
| --- | --- | --- | --- |
| term_fast X | -0.217738377 | -0.217738376 | +0.001 |
| term_fast Y | 0.001306018 | 0.001306018 | 0 |
| term_fast Z | 2.569e-05 | 2.569e-05 | 0 |
| term_slow X | 0.001283015 | 0.001283015 | 0 |
| term_slow Y | 0.213900651 | 0.213900663 | -12 |
| term_slow Z | 0.001050925 | 0.001050925 | 0 |
| term_close X | -2.047e-05 | -2.035e-05 | +1.2 |
| term_close Y | 0.001136382 | 0.001136470 | -0.088 |
| term_close Z | -0.231269033 | -0.231269034 | -1 |

### Final Pix0 Values
| Axis | C (m) | PyTorch (m) | Delta (μm) | Match? |
| --- | --- | --- | --- | --- |
| X (Fast) | -0.216475836 | -0.216336514 | **+139.3** | ✗ |
| Y (Slow) | 0.216343050 | 0.215206681 | **-1136.4** | ✗ |
| Z (Close) | -0.230192414 | -0.230198009 | **-5.6** | ~✓ |

## Root Cause Analysis

The beam_center_m trace line is misleading because:

1. C logs the **pixel-based** values (Xclose/Yclose in pixels × pixel_size in m)
2. PyTorch logs the **mm-based** config values directly (beam_center_f/beam_center_s in mm)
3. Both are labeled as "beam_center_m" but represent different stages of conversion

The actual Fclose/Sclose values match perfectly, which means:
- The mm→m conversion IS happening correctly in the calculation
- The trace logging is just showing different intermediate values
- The real divergence is elsewhere in the pix0 calculation

## Next Steps

1. **Verify unit system**: Confirm that PyTorch's trace logging for beam_center_m should show the converted meters value, not the raw mm config
2. **Look deeper**: The pix0 divergence (139μm, 1136μm, 6μm) persists even though Fclose/Sclose match. This suggests:
   - Missing offset in the CUSTOM convention case
   - Different pivot calculation between C and PyTorch
   - Possible MOSFLM +0.5 pixel offset not being applied/unapplied correctly in CUSTOM mode
3. **Phase H6d**: Update fix_plan.md with these findings
4. **Phase H6e**: Investigate why pix0 differs when Fclose/Sclose are identical

## References

- C trace: `reports/2025-10-cli-flags/phase_h6/c_trace/trace_c_pix0_clean.log`
- PyTorch trace: `reports/2025-10-cli-flags/phase_h6/py_trace/trace_py_pix0.log`
- Diff output: `reports/2025-10-cli-flags/phase_h6/trace_diff.txt`
- Detector architecture: `docs/architecture/detector.md:95-210`
- Config map: `docs/development/c_to_pytorch_config_map.md:58-118`
