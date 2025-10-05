# Phase A: CLI Flags Evidence Gathering Summary

**Date:** 2025-10-05
**Initiative:** [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm
**Phase:** A - Requirements & Trace Alignment
**Status:** COMPLETE

## Executive Summary

Phase A has successfully captured C reference behavior for `-nonoise` and `-pix0_vector_mm` flags through parallel command execution and trace analysis. Key findings documented below inform PyTorch implementation decisions for Phase B.

## Task A1: -nonoise Flag Behavior

### Method
Executed the supervisor's canonical command twice:
1. WITH `-nonoise` flag → `c_with_nonoise.log`
2. WITHOUT `-nonoise` flag → `c_with_noise.log`

### Commands Executed
```bash
export NB_C_BIN=./golden_suite_generator/nanoBragg

# With -nonoise
$NB_C_BIN -mat A.mat -floatfile img.bin -hkl scaled.hkl -nointerpolate \
  -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 \
  -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 \
  -distance 231.274660 -lambda 0.976800 -pixel 0.172 \
  -detpixels_x 2463 -detpixels_y 2527 \
  -odet_vector -0.000088 0.004914 -0.999988 \
  -sdet_vector -0.005998 -0.999970 -0.004913 \
  -fdet_vector 0.999982 -0.005998 -0.000118 \
  -pix0_vector_mm -216.336293 215.205512 -230.200866 \
  -beam_vector 0.00051387949 0.0 -0.99999986 \
  -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 \
  -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 \
  -nonoise

# Without -nonoise (same command, flag removed)
```

### Findings

**Suppressed Output with -nonoise:**
1. **Noise parameters section removed:**
   ```
   noise image paramters:
   seed: -1759702416
   water droplet size: 0 m
   ```

2. **Noise image generation skipped:**
   ```
   6486 photons on noise image (0 overloads)
   writing noiseimage.img as 2-byte integers
   ```

**Preserved Output:**
- Float image (`img.bin`) generated in both cases
- Integer image (`intimage.img`) generated in both cases
- PGM preview (`image.pgm`) generated in both cases

### Conclusions for PyTorch

1. **Flag semantics:** `-nonoise` suppresses noise image generation entirely, even if `-noisefile` is provided.
2. **Implementation location:** Must guard noise writer in `__main__.py` (around line 1152 per CLAUDE.md).
3. **Config threading:** Add `suppress_noise` boolean or use `NoiseConfig.generate_noise_image = False`.
4. **Parity warning:** Should emit warning if both `-nonoise` and `-noisefile` are provided (C code silently ignores `-noisefile`).

## Task A2: pix0_vector_mm Ground Truth

### Method
Analyzed C code parsing logic and captured `DETECTOR_PIX0_VECTOR` output from trace.

### C Code Analysis

**Parsing location:** `golden_suite_generator/nanoBragg.c` lines 740-747

```c
if(strstr(argv[i], "-pix0_vector") && (argc > (i+3)))
{
    beam_convention = CUSTOM;
    pix0_vector[0] = 1.0;
    pix0_vector[1] = atof(argv[i+1]);
    pix0_vector[2] = atof(argv[i+2]);
    pix0_vector[3] = atof(argv[i+3]);
}
```

**Key observations:**
- Uses `strstr()` match: both `-pix0_vector` and `-pix0_vector_mm` match `-pix0_vector`
- **NO unit conversion** occurs during parsing
- Sets `beam_convention = CUSTOM` (critical side effect)
- Reads values AS-IS via `atof()`

### Trace Output

**Command input:**
```
-pix0_vector_mm -216.336293 215.205512 -230.200866
```

**C output (line 1849):**
```
DETECTOR_PIX0_VECTOR -0.216475836204836 0.216343050492215 -0.230192414300537
```

**Unit verification:**
| Axis | Input (labeled mm) | Input/1000 (→m) | C Output (m) | Difference |
|------|-------------------|-----------------|--------------|------------|
| X    | -216.336293       | -0.216336293    | -0.216475836 | ~0.00014   |
| Y    | 215.205512        | 0.215205512     | 0.216343050  | ~0.00114   |
| Z    | -230.200866       | -0.230200866    | -0.230192414 | ~0.000008  |

### Critical Finding: C Code Unit Handling Bug

**The C code does NOT convert millimeters to meters for -pix0_vector_mm!**

The `_mm` suffix is purely **documentation** - the C implementation treats both flags identically via `strstr()` matching. The caller (supervisor command) provides values that appear to be in millimeters based on magnitude, but the C code reads them directly as-is.

The small differences (~0.0001-0.001 m) between input/1000 and final output are due to detector rotation transformations applied afterward (lines 1737-1841), NOT unit conversion.

### Conclusions for PyTorch

1. **Implement as distinct flags:**
   - `-pix0_vector`: read as meters (no conversion)
   - `-pix0_vector_mm`: read as millimeters, **divide by 1000** to convert to meters

2. **Unit system alignment:**
   - DetectorConfig.pix0_override_m: store in meters (canonical unit)
   - Normalize both flag inputs to meters at parse time
   - Preserve gradient flow (use tensor operations, not .item())

3. **CUSTOM convention trigger:**
   - Both flags MUST set `beam_convention = CUSTOM` (or equivalent)
   - This disables default beam center calculations per C behavior

4. **Validation:**
   - Reject partial vectors (must provide all 3 components)
   - Reject mixed units (can't specify both -pix0_vector and -pix0_vector_mm)
   - Emit clear error messages for unit mismatches

## Task A3: Integration Notes

### CUSTOM Convention Interactions

When `-pix0_vector` or `-pix0_vector_mm` is provided:
- C code sets `beam_convention = CUSTOM` (line 742)
- This disables MOSFLM/XDS/ADXV default beam center mappings
- PyTorch MUST replicate this behavior to maintain parity

### Detector Cache Invalidation

Per plan Phase B Task B5:
- Supplying pix0 overrides MUST trigger `Detector.invalidate_cache()`
- Ensure dependent tensors (pixel coordinates, solid angles) are recomputed
- Verify device/dtype consistency for override tensor

### Noise Suppression Priority

Flag precedence (C behavior):
1. `-nonoise` suppresses ALL noise generation
2. `-noisefile` is ignored when `-nonoise` is present
3. No warning emitted by C code (silent ignore)

PyTorch improvement opportunity:
- Emit warning when conflicting flags detected
- Document this in help text and user-facing docs

## Artifacts Generated

### Logs
- `c_with_nonoise.log` - C execution WITH -nonoise flag
- `c_with_noise.log` - C execution WITHOUT -nonoise flag
- `pix0_trace/trace.log` - Detailed pix0 vector analysis

### Output Files (from C runs)
- `img.bin` - Float image (24M, generated in both cases)
- `intimage.img` - Integer SMV image (12M, both cases)
- `image.pgm` - PGM preview (6.0M, both cases)
- `noiseimage.img` - Noise image (12M, only without -nonoise)

## Exit Criteria Status

✅ **A1 Complete:** C reference for `-nonoise` captured with stdout/stderr diff
✅ **A2 Complete:** pix0 vector ground truth documented with unit analysis
✅ **A3 Complete:** Findings memo published (this document)

## Recommendations for Phase B

1. **Prioritize unit correctness:** Implement proper mm→m conversion for `-pix0_vector_mm`
2. **Add validation:** Reject mixed units, partial vectors, conflicting flags
3. **Preserve parity:** Set CUSTOM convention when pix0 overrides are used
4. **Improve UX:** Emit warnings for conflicting flags (better than C's silent behavior)
5. **Test coverage:** Add regression tests for both meter and millimeter inputs verifying identical normalized tensors

## References

- Supervisor directive: `input.md` lines 8-9
- Plan definition: `plans/active/cli-noise-pix0/plan.md`
- C code: `golden_suite_generator/nanoBragg.c` lines 740-747, 1737-1850
- Architecture: `docs/architecture/detector.md` §5 (pix0 caching)
- Config map: `docs/development/c_to_pytorch_config_map.md` (detector pivot + noise)

---

**Next Phase:** B - CLI & Config Wiring (argparse, config threading, override support)
