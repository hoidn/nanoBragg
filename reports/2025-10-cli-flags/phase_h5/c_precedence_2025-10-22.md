# Phase H5a C Precedence Evidence (2025-10-22)

**Date:** 2025-10-22
**Git SHA:** 857c075
**NB_C_BIN:** ./golden_suite_generator/nanoBragg
**Status:** Evidence complete

## Executive Summary

Fresh C traces captured on 2025-10-22 **confirm** the October 6, 2025 finding: when custom detector vectors (`-odet_vector`, `-sdet_vector`, `-fdet_vector`) are supplied, the C code **ignores** the `-pix0_vector_mm` override and computes pix0 from `Xbeam`/`Ybeam` using the custom detector basis.

## Commands Executed

### WITH Override
```bash
./golden_suite_generator/nanoBragg \
  -mat A.mat -floatfile img.bin -hkl scaled.hkl \
  -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 \
  -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 \
  -distance 231.274660 -lambda 0.976800 -pixel 0.172 \
  -detpixels_x 2463 -detpixels_y 2527 \
  -odet_vector -0.000088 0.004914 -0.999988 \
  -sdet_vector -0.005998 -0.999970 -0.004913 \
  -fdet_vector 0.999982 -0.005998 -0.000118 \
  -pix0_vector_mm -216.336293 215.205512 -230.200866 \
  -beam_vector 0.00051387949 0.0 -0.99999986 \
  -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 \
  -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0
```

### WITHOUT Override
```bash
./golden_suite_generator/nanoBragg \
  -mat A.mat -floatfile img_no_override.bin -hkl scaled.hkl \
  -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 \
  -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 \
  -distance 231.274660 -lambda 0.976800 -pixel 0.172 \
  -detpixels_x 2463 -detpixels_y 2527 \
  -odet_vector -0.000088 0.004914 -0.999988 \
  -sdet_vector -0.005998 -0.999970 -0.004913 \
  -fdet_vector 0.999982 -0.005998 -0.000118 \
  -beam_vector 0.00051387949 0.0 -0.99999986 \
  -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 \
  -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0
```

## Results: IDENTICAL Geometry

| Quantity | WITH Override | WITHOUT Override | Difference | Unit |
|----------|--------------|------------------|------------|------|
| pix0_vector[0] | -0.216475836204836 | -0.216475836204836 | 0.0 | m |
| pix0_vector[1] | 0.216343050492215 | 0.216343050492215 | 0.0 | m |
| pix0_vector[2] | -0.230192414300537 | -0.230192414300537 | 0.0 | m |
| Fbeam | 0.217889 | 0.217889 | 0.0 | m |
| Sbeam | 0.215043 | 0.215043 | 0.0 | m |
| Fclose | 0.217742 | 0.217742 | 0.0 | m |
| Sclose | 0.213907 | 0.213907 | 0.0 | m |
| max_I | 446.254 | 446.254 | 0.0 | photons |
| max_I location | (0.117906, 0.178794) | (0.117906, 0.178794) | 0.0 | m |

**Only difference:** Output filename (`img.bin` vs `img_no_override.bin`)

## Dot-Product Derivation

The `-pix0_vector_mm` flag supplies the override vector in millimeters:
```
override_mm = (-216.336293, 215.205512, -230.200866)
override_m = (-0.216336293, 0.215205512, -0.230200866)  # after mm→m conversion
```

If the override were applied using projection onto detector axes:
```
Fbeam_expected = override_m · fdet_vector
             = (-0.216336, 0.215206, -0.230201) · (0.999982, -0.005998, -0.000118)
             = -0.216336×0.999982 + 0.215206×(-0.005998) + (-0.230201)×(-0.000118)
             = -0.216332 - 0.001291 + 0.000027
             = -0.217596  # magnitude, sign may vary

Sbeam_expected = override_m · sdet_vector
             = (-0.216336, 0.215206, -0.230201) · (-0.005998, -0.999970, -0.004913)
             = (-0.216336)×(-0.005998) + 0.215206×(-0.999970) + (-0.230201)×(-0.004913)
             = 0.001297 - 0.215200 + 0.001131
             = -0.212772  # magnitude, sign may vary
```

**Actual C output:**
```
Fbeam = 0.217889 m
Sbeam = 0.215043 m
```

The values do **NOT** match the override projection. Instead, the C code derives them from `Xbeam`/`Ybeam` using the CUSTOM convention mapping.

## Precedence Logic

The evidence demonstrates this precedence in nanoBragg.c when custom detector vectors are present:

```c
if (custom_vectors_supplied) {
    // Compute pix0 from Xbeam/Ybeam using custom basis
    pix0_vector = compute_from_xbeam_ybeam(Xbeam, Ybeam, fdet, sdet, odet);
    Fbeam = dot(pix0_vector, fdet);
    Sbeam = dot(pix0_vector, sdet);
    // IGNORE -pix0_vector_mm flag
} else if (pix0_override_supplied) {
    // Apply override
    pix0_vector = override_value;
    // ...
} else {
    // Use convention defaults
    // ...
}
```

## Artifacts

- WITH override log: `reports/2025-10-cli-flags/phase_h5/c_traces/2025-10-22/with_override.log`
- WITHOUT override log: `reports/2025-10-cli-flags/phase_h5/c_traces/2025-10-22/without_override.log`
- Diff: `reports/2025-10-cli-flags/phase_h5/c_traces/2025-10-22/diff.log` (only filename difference)

## Implications for PyTorch

**Current PyTorch status (as of Phase H3b2, commit d6f158c):** The implementation correctly skips the override when custom detector vectors are present, which **matches C behavior exactly**.

**Remaining work:**
- The 1.14 mm pix0 delta noted in Phase J traces is NOT due to override precedence (that parity is correct)
- The delta must originate from a different issue (likely normalization or lattice factor calculation)
- Proceed to Phase K (normalization) and Phase L (final parity) without modifying detector override logic

## References

- Plan: `plans/active/cli-noise-pix0/plan.md` Phase H5
- Supervisor directive: `input.md` (Do Now: CLI-FLAGS-003 Phase H5a evidence)
- Prior evidence: `reports/2025-10-cli-flags/phase_h5/PHASE_H5A_COMPLETE.md` (2025-10-06)
- C spec: `docs/architecture/detector.md` §5 (pix0 computation)
- C code reference: `golden_suite_generator/nanoBragg.c` lines 1730-1860
