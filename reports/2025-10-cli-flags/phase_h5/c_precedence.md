# Phase H5 Evidence: C-Code pix0 Override Precedence with Custom Vectors

**Date:** 2025-10-06
**Author:** Ralph (evidence loop)
**Purpose:** Capture C-code behavior when both `-pix0_vector_mm` override and custom detector vectors (`-odet_vector`, `-sdet_vector`, `-fdet_vector`) are supplied.

## Executive Summary

When custom detector vectors are provided to `nanoBragg.c`, the `-pix0_vector_mm` flag appears to have **no effect** on the computed `DETECTOR_PIX0_VECTOR` or beam center coordinates (`Fbeam`/`Sbeam`). Both runs (with and without the override) produce identical geometry values.

## Test Configuration

**Common Parameters:**
- Matrix: `A.mat` (MOSFLM orientation)
- HKL: `scaled.hkl`
- Wavelength: 0.9768 Å
- Distance: 231.274660 mm
- Pixel size: 0.172 mm
- Detector dimensions: 2463 × 2527 pixels
- Beam center: Xbeam=217.742295 mm, Ybeam=213.907080 mm
- Custom detector vectors:
  - `fdet_vector`: [0.999982, -0.005998, -0.000118]
  - `sdet_vector`: [-0.005998, -0.999970, -0.004913]
  - `odet_vector`: [-0.000088, 0.004914, -0.999988]
- Beam vector: [0.00051387949, 0.0, -0.99999986]
- Crystal: Na=36, Nb=47, Nc=29
- Phi: 0° to 0.1° in 10 steps
- Detector rotations: all 0°
- Two-theta: 0°

**Variable Parameter:**
- **Run 1 (WITH override):** `-pix0_vector_mm -216.336293 215.205512 -230.200866`
- **Run 2 (WITHOUT override):** No `-pix0_vector_mm` flag

## Results

### Geometry Output Comparison

| Quantity | WITH Override | WITHOUT Override | Difference |
|----------|--------------|------------------|------------|
| **pix0_vector[0]** (m) | -0.216475836204836 | -0.216475836204836 | 0.000000 |
| **pix0_vector[1]** (m) | 0.216343050492215 | 0.216343050492215 | 0.000000 |
| **pix0_vector[2]** (m) | -0.230192414300537 | -0.230192414300537 | 0.000000 |
| **Fbeam** (m) | 0.217889 | 0.217889 | 0.000000 |
| **Sbeam** (m) | 0.215043 | 0.215043 | 0.000000 |

### Full Trace Diff

The only difference between the two log files is the output filename:
```diff
-writing img_no_override.bin as 6224001 4-byte floats
+writing img.bin as 6224001 4-byte floats
```

All TRACE lines, detector geometry, beam parameters, crystal setup, and final statistics are **byte-for-byte identical**.

## Interpretation

### Observed Behavior

When custom detector vectors are supplied:
1. The C code computes `pix0_vector` from the **custom vectors and Xbeam/Ybeam** values
2. The `-pix0_vector_mm` override is **silently ignored**
3. `Fbeam` and `Sbeam` are derived from the computed `pix0_vector` via projection onto the detector plane

### Implied C-Code Logic Path

Based on these results, `nanoBragg.c` appears to follow this precedence:

```c
if (custom_detector_vectors_provided) {
    // Use custom vectors to compute pix0 from Xbeam/Ybeam
    // Ignore any -pix0_vector_mm override
    pix0_vector = compute_from_custom_vectors(fdet, sdet, odet, Xbeam, Ybeam, distance);
} else if (pix0_override_provided) {
    // Apply the override
    pix0_vector = pix0_override;
} else {
    // Use convention defaults
    pix0_vector = compute_from_convention(Xbeam, Ybeam, distance, pivot_mode);
}
```

### Discrepancy with Phase H3b1 Findings

**⚠️ CRITICAL INCONSISTENCY DETECTED:**

This Phase H5 evidence **contradicts** Phase H3b1 findings (2025-10-17 Attempt #23), which concluded:
> "C geometry is identical with or without `-pix0_vector_mm` when custom vectors are supplied."

**However**, Attempt #23 artifacts showed:
- WITH override: `Fbeam=0.217889`, `Sbeam=0.215043`
- WITHOUT override: `Fbeam=0.037` (approximately), `Sbeam=0.037` (approximately)

The current Phase H5 evidence shows BOTH runs producing `Fbeam=0.217889`, `Sbeam=0.215043`.

**Possible explanations:**
1. **Different C binary versions:** Phase H3b1 used a different commit or instrumentation
2. **Missing trace capture:** Phase H3b1 may have captured incomplete logs
3. **Command differences:** The exact flags may have differed between phases

## Derivation: pix0 Override to Fbeam/Sbeam

**Note:** This derivation is for documentation purposes. Based on the evidence above, when custom vectors are present, the C code does NOT apply the override, so this calculation is academic.

If the override WERE applied with custom vectors, the conversion would be:

1. **Input (mm):** `pix0_override_mm = [-216.336293, 215.205512, -230.200866]`
2. **Convert to meters:** `pix0_override_m = pix0_override_mm / 1000.0`
   ```
   pix0_override_m = [-0.216336293, 0.215205512, -0.230200866]
   ```

3. **Project onto detector plane:**
   Given:
   - `fdet = [0.999982, -0.005998, -0.000118]`
   - `sdet = [-0.005998, -0.999970, -0.004913]`

   Compute:
   ```
   Fbeam = pix0_override_m · fdet
         = (-0.216336293)(0.999982) + (0.215205512)(-0.005998) + (-0.230200866)(-0.000118)
         = -0.216332405 + (-0.001290822) + 0.000027184
         = -0.217596043 m

   Sbeam = pix0_override_m · sdet
         = (-0.216336293)(-0.005998) + (0.215205512)(-0.999970) + (-0.230200866)(-0.004913)
         = 0.001297409 + (-0.215199057) + 0.001130697
         = -0.212770951 m
   ```

4. **Expected if override were applied:**
   - `Fbeam ≈ -0.2176 m` (negative!)
   - `Sbeam ≈ -0.2128 m` (negative!)

5. **Actual C output:**
   - `Fbeam = 0.217889 m` (positive, derived from Xbeam/Ybeam with MOSFLM +0.5 pixel adjustment)
   - `Sbeam = 0.215043 m` (positive)

The sign difference and magnitude mismatch confirm that the override is **NOT** being applied when custom vectors are present.

## Next Actions for PyTorch Implementation (Phase H5b)

Based on this evidence, the PyTorch implementation should:

1. **SKIP pix0 override when custom vectors are present** (current behavior is correct!)
2. **Log a warning** when both `-pix0_vector_mm` and custom vectors are supplied, noting the override will be ignored
3. **Document this precedence** in the CLI help text and architecture docs

**No geometry code changes needed** - the current PyTorch behavior matches C semantics.

## Artifacts

- **C trace WITH override:** `reports/2025-10-cli-flags/phase_h5/c_traces/with_override.log`
- **C trace WITHOUT override:** `reports/2025-10-cli-flags/phase_h5/c_traces/without_override.log`
- **Diff output:** `reports/2025-10-cli-flags/phase_h5/c_traces/diff.log`
- **This memo:** `reports/2025-10-cli-flags/phase_h5/c_precedence.md`

## References

- Supervisor command: `prompts/supervisor.md` (exact flags captured in test configuration above)
- C parameter mapping: `docs/development/c_to_pytorch_config_map.md`
- Detector architecture: `docs/architecture/detector.md` §5
- Prior phase: `reports/2025-10-cli-flags/phase_h3b1/` (Phase H3b1 WITH/without override traces)
- Plan: `plans/active/cli-noise-pix0/plan.md` Phase H5
