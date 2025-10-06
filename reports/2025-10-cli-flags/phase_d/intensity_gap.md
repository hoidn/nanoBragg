# Phase D3: Intensity Gap Analysis

**Date:** 2025-10-06
**Task:** CLI-FLAGS-003 Phase D3 - Diagnose 257.7× intensity scaling discrepancy
**Command:** Supervisor parity command from `prompts/supervisor.md`

## Executive Summary

The Phase C2 parity run revealed a **257.7× intensity gap** between C (max_I=446) and PyTorch (max_I=115,000). However, deeper analysis reveals this is **NOT** a simple scaling issue, but rather a **fundamental geometry/physics discrepancy**:

1. **Zero correlation** between C and PyTorch outputs (r = -5×10⁻⁶)
2. **Completely different peak locations** (1538 pixels apart)
3. **Vastly different diffraction patterns** (C: 99.22% non-zero pixels, PyTorch: 1.88%)

**Conclusion:** The intensity gap is a **symptom** of incorrect scattering geometry, not the root cause. The PyTorch implementation is producing a fundamentally different diffraction pattern.

## Quantitative Analysis

### Image Statistics

| Metric | C Implementation | PyTorch Implementation | Ratio (Py/C) |
|--------|------------------|------------------------|--------------|
| **Max intensity** | 4.463e+02 | 1.150e+05 | **257.7×** |
| **Mean intensity** | 1.043e-03 | 1.217e-01 | 116.7× |
| **Sum (total photons)** | 6.491e+03 | 7.572e+05 | 116.7× |
| **L2 norm** | 8.342e+02 | 1.882e+05 | 225.6× |
| **Correlation** | — | — | **-5×10⁻⁶** ≈ **0** |

### Peak Location Analysis

**C peak:** (slow=1039, fast=685), intensity=446.3
**PyTorch peak:** (slow=1145, fast=2220), intensity=115,000

- **Displacement:** 1538 pixels (Δslow=106, Δfast=1535)
- **Cross-check:** PyTorch has **zero** intensity at C peak location
- **Inference:** These are different Bragg reflections or the geometry is wrong

### Non-Zero Pixel Count

- **C:** 6,175,476 / 6,224,001 pixels = **99.22%** non-zero
- **PyTorch:** 117,049 / 6,224,001 pixels = **1.88%** non-zero

**Interpretation:** C produces a dense diffraction pattern with background everywhere. PyTorch produces sparse, concentrated peaks. This suggests:
1. PyTorch may be missing the background/diffuse scattering component
2. PyTorch's dmin culling may be too aggressive
3. PyTorch's structure factor interpolation may be returning zero for most reflections

## Configuration Parameters (from C log)

```
phi_steps = 10
sources = 1
mosaic_domains = 1
oversample = 1×1 = 1
fluence = 1e+24 photons/m²
wavelength = 9.768e-11 m (0.9768 Å)
distance = 0.231275 m
pixel_size = 0.000172 m
detector = 2463×2527 pixels
detector convention = CUSTOM
pivot = SAMPLE
```

## Top-10 Peak Comparison

### C Implementation
```
#1: (1039,  685) = 4.463e+02
#2: (1039,  684) = 3.691e+02
#3: (1632, 1443) = 3.302e+02
#4: (1631, 1443) = 2.383e+02
#5: ( 910, 1489) = 1.764e+02
...
```

### PyTorch Implementation
```
#1: (1145, 2220) = 1.150e+05
#2: (1146, 2220) = 1.143e+05
#3: (1146, 2219) = 4.369e+04
#4: (1145, 2221) = 4.159e+04
#5: (1145, 2219) = 3.915e+04
...
```

**Observation:** PyTorch peaks are **highly clustered** (adjacent pixels), while C peaks are **distributed** across the detector. This could indicate:
1. PyTorch is missing the lattice shape factor smearing
2. PyTorch is computing incorrect fractional Miller indices
3. PyTorch has an interpolation bug causing extreme peakiness

## Hypotheses & Diagnostics

### Hypothesis 1: Missing Steps Normalization (RULED OUT)

**Test:** Check `steps` divisor in `simulator.py:998`
**Finding:** Code correctly computes `steps = 1 × 10 × 1 × 1 = 10` and divides by it
**Verdict:** ❌ This is NOT the cause (would only explain 10× factor, not 257×)

### Hypothesis 2: 256 = 2⁸ Artifact

**Observation:** 257.7 ≈ 256
**Possible causes:**
- Byte-order swapping during binary I/O?
- Incorrect dtype cast (e.g., uint8 → float32)?
- Bit-shift error in normalization?

**Test needed:** Check if torch binary writer is introducing a scaling factor

### Hypothesis 3: Incorrect Geometry (LIKELY ROOT CAUSE)

**Evidence:**
- Zero correlation between outputs
- Peaks in completely different locations
- Vastly different non-zero pixel distributions

**Possible causes:**
1. **pix0_vector override not being applied correctly** (detector origin wrong)
2. **Custom basis vectors not matching C code** (detector orientation wrong)
3. **SAMPLE pivot calculation incorrect** (beam position wrong)
4. **Scattering vector calculation error** (incident beam direction wrong from log line: "XDS incident beam: 0.00063187 0.00490992 0.999988")
5. **Miller index rounding error** (reflections assigned to wrong pixels)

**Critical observation from C log:**
```
DETECTOR_PIX0_VECTOR -0.216475836204836 0.216343050492215 -0.230192414300537
INCIDENT_BEAM_DIRECTION= 0.000513879 0 -1
```

**Test needed:**
1. Generate PyTorch detector trace showing pix0_vector and incident_beam_direction
2. Compare scattering vectors for a known pixel
3. Compare fractional Miller indices for the same pixel

### Hypothesis 4: Missing Background/F_cell Issues

**Evidence:** PyTorch has only 1.88% non-zero pixels
**Possible causes:**
1. dmin culling too aggressive (eliminating valid reflections)
2. HKL file not loaded correctly (missing structure factors)
3. Interpolation returning zero for out-of-grid indices
4. Background not being added

**Test needed:**
1. Check if Fdump.bin was loaded in PyTorch run
2. Print HKL grid dimensions and non-zero count
3. Check dmin threshold vs stol distribution

### Hypothesis 5: Lattice Shape Factor Error

**Evidence:** PyTorch peaks are extremely sharp/concentrated
**Possible cause:** `sincg()` lattice shape factor not being applied, or Na/Nb/Nc values wrong

**Test needed:** Compare `F_latt` values for top-10 C peaks in PyTorch trace

## Recommended Next Steps

### Immediate Actions (Required for Plan D3 Closure)

1. **Generate parallel trace for a C peak pixel:**
   - Instrument C code to print pix0_vector, incident_beam_direction, scattering_vector, h/k/l, F_cell, F_latt, omega for pixel (1039, 685)
   - Generate identical PyTorch trace for the same pixel
   - **Compare line-by-line to find first divergence**

2. **Verify detector geometry:**
   - Print PyTorch's `detector.pix0_vector` after override
   - Print PyTorch's incident_beam_direction
   - Compare to C log values above

3. **Check HKL data loading:**
   - Verify Fdump.bin was loaded (not regenerated)
   - Print grid dimensions and non-zero structure factor count
   - Compare to C's "64333 initialized hkls"

4. **Inspect simulator normalization:**
   - Add debug print for `steps` value
   - Add debug print for `source_norm`, `phi_steps`, `mosaic_domains`, `oversample`
   - Verify fluence, r_e_sqr, omega values match C

### Proposed Fixes (After Root Cause Identified)

Based on trace comparison findings:
- If pix0_vector wrong → Fix detector override assignment
- If incident_beam wrong → Fix convention-dependent beam direction
- If scattering vector wrong → Fix coordinate system transform
- If Miller indices wrong → Fix reciprocal space calculation
- If F_cell/F_latt wrong → Fix structure factor lookup/interpolation

## Artifacts

**Location:** `reports/2025-10-cli-flags/phase_d/`

### Generated Files

1. **`intensity_gap_stats.json`** - Complete statistical comparison
2. **`analyze_intensity.py`** - Analysis script (first-pass quantitative)
3. **`compare_peak_locations.py`** - Peak location and distribution analysis
4. **`intensity_gap.md`** - This document

### Input Files (Phase C2)

- **`../phase_c/parity/c_img.bin`** - C reference output (24 MB)
- **`../phase_c/parity/torch_img.bin`** - PyTorch output (24 MB)
- **`../phase_c/parity/c_cli.log`** - C execution log
- **`../phase_c/parity/torch_stdout.log`** - PyTorch execution log

## Authoritative Command

```bash
# Phase C2 parity run command (from prompts/supervisor.md):
export AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md

# C reference:
NB_C_BIN=./golden_suite_generator/nanoBragg "$NB_C_BIN" \
  -mat A.mat -hkl scaled.hkl -lambda 0.9768 \
  -oversample 1 -pix0_vector_mm -216.475836 216.343050 -230.192414 \
  -nonoise -floatfile reports/2025-10-cli-flags/phase_c/parity/c_img.bin \
  >reports/2025-10-cli-flags/phase_c/parity/c_cli.log 2>&1

# PyTorch equivalent:
env KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python -m nanobrag_torch \
  -mat A.mat -hkl scaled.hkl -lambda 0.9768 \
  -oversample 1 -pix0_vector_mm -216.475836 216.343050 -230.192414 \
  -nonoise -floatfile reports/2025-10-cli-flags/phase_c/parity/torch_img.bin \
  >reports/2025-10-cli-flags/phase_c/parity/torch_stdout.log 2>&1
```

## Time Investment

- Analysis script development: ~10 minutes
- Image loading and statistics: ~2 minutes
- Peak comparison: ~3 minutes
- Report writing: ~25 minutes
- **Total:** ~40 minutes

## References

- Plan: `plans/active/cli-noise-pix0/plan.md` Phase D3
- Fix Plan: `docs/fix_plan.md` [CLI-FLAGS-003]
- Supervisor Memo: `input.md` (2025-10-06T00:32:22Z)
- Debugging SOP: `docs/debugging/debugging.md` §2.1 (Parallel Trace Comparison)
- C-Py Config Map: `docs/development/c_to_pytorch_config_map.md`
- Detector Architecture: `docs/architecture/detector.md`
- Simulator Code: `src/nanobrag_torch/simulator.py:831` (steps calculation), `:998` (normalization), `:1049-1053` (final scaling)
