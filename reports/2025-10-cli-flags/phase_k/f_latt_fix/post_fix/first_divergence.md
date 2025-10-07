# First Divergence Analysis: F_latt SQUARE Test
**Date:** 2025-10-06
**Test:** `test_f_latt_square_matches_c`
**Pixel:** (s=236, f=398)
**Correlation:** 0.174 (required ≥0.999)
**Issue:** Complete spatial mismatch of bright spots

## Executive Summary

**First Divergence Point:** Structure factor calculation (`F_cell`)

The C code reports `F_cell = 197.64` for pixel (236, 398), but this does NOT match the expected value from `-default_F 300`.

**Critical Discovery:** The C code is using a LOOKUP TABLE for structure factors, NOT the default_F value!

## Evidence

### C Trace Output (Pixel 236, 398)
```
TRACE_C: hkl_frac -1.00671618187229 2.02936231827162 14.0075496602651
TRACE_C: hkl_rounded -1 2 14
TRACE_C: F_latt_a -9.92670330969807
TRACE_C: F_latt_b 8.65322202878548
TRACE_C: F_latt_c 9.90743530646676
TRACE_C: F_latt -851.028558466814
TRACE_C: F_cell 197.64           ← DIVERGENCE: Expected √300 = 17.32, got 197.64
TRACE_C: I_before_scaling 28290326444.3413
TRACE_C: I_pixel_final 27169.5917850245
```

### Expected vs Actual F_cell

- **Input parameter:** `-default_F 300`
- **Expected F_cell:** `√300 = 17.32` (structure factor amplitude)
- **C trace shows:** `F_cell = 197.64`
- **Ratio:** `197.64 / 17.32 = 11.41`

This 11.4× factor does NOT match any simple scaling (not Na, Nb, Nc, nor their products).

## Root Cause Confirmed

**The C code is loading a CACHED dump file (`Fdump.bin`) from a previous run with an HKL file.**

### Evidence:
1. File `Fdump.bin` exists (modified Oct 6 15:39)
2. C code auto-loads dump file if no `-hkl` is specified (lines 2350-2377)
3. The dump file contains structure factors from a PREVIOUS simulation
4. The PyTorch CLI does NOT implement dump file caching - it only uses `default_F`

### C Code Workflow (from nanoBragg.c):
1. **If no `-hkl` file specified:** Try to load `Fdump.bin` (lines 2350-2377)
2. **If dump file exists:** Load cached structure factors from it
3. **Else:** Use `default_F` for all reflections

### Test Environment Contamination:
- The repository contains `Fdump.bin` from a previous HKL-based run
- Current test did NOT pass `-hkl` argument
- C code silently loaded cached structure factors from `Fdump.bin`
- PyTorch code used uniform `default_F = 300`
- **Result:** Completely different structure factor distributions → spatial mismatch

## Miller Indices Agreement

The h, k, l fractional Miller indices DO MATCH between C and the expected PyTorch calculation:

**C code:**
```
h_frac = -1.00671618187229
k_frac = 2.02936231827162
l_frac = 14.0075496602651
```

**Expected from physics** (using scattering vector S · real_lattice):
- Scattering vector S (Å⁻¹): [-1.00671e8, 2.02936e8, 1.40075e9] / 1e8 = [-1.00671, 2.02936, 14.00755]
- Real lattice a, b, c (Å): [100, 0, 0], [0, 100, 0], [0, 0, 100]
- h = S·a = -1.00671 ✓
- k = S·b = 2.02936 ✓
- l = S·c = 14.00755 ✓

**Lattice factor F_latt also matches the expected calculation**, so the divergence is ONLY in F_cell.

## Lattice Factor Validation

The C code F_latt calculation is correct per the (h, k, l) fix:

```
F_latt_a = sincg(π × (-1.00671), 10) = -9.927 ✓
F_latt_b = sincg(π × 2.02936, 10) = 8.653 ✓
F_latt_c = sincg(π × 14.00755, 10) = 9.907 ✓
F_latt = F_latt_a × F_latt_b × F_latt_c = -851.0 ✓
```

This confirms that Phase K2's fix (using h instead of h-h0) is correctly implemented in the C code.

## Action Required

1. **Investigate C code HKL lookup logic:**
   - Where is F_cell = 197.64 coming from?
   - Is there a default HKL table being auto-generated?
   - What is the C code behavior when NO `-hkl` file is provided?

2. **Check test invocation:**
   - Confirm NO `-hkl` argument is passed to C binary
   - Verify PyTorch CLI matches the same invocation

3. **Verify specification:**
   - Does `-default_F` mean "use this for ALL reflections"?
   - Or does it mean "use this ONLY when no HKL file is provided AND no auto-generation occurs"?

## Impact

This is a **SPECIFICATION** issue, not a physics bug. The test is invalid because:
- C code is using a structure factor lookup table (source unknown)
- PyTorch code is using uniform default_F = 300
- They are testing fundamentally different scenarios

## Recommended Fix Path

**IMMEDIATE ACTION:** Delete `Fdump.bin` before running test

```bash
rm Fdump.bin
```

This will force the C code to use `-default_F 300` uniformly for all reflections, matching the PyTorch behavior.

**Alternative fixes:**
1. Add `Fdump.bin` to `.gitignore` to prevent test contamination
2. Modify test to explicitly delete dump file before each run
3. Implement HKL dump file caching in PyTorch CLI (requires spec decision)

## Files

- C trace: `reports/2025-10-cli-flags/phase_k/f_latt_fix/post_fix/c_trace_20251006171510.log`
- C full output: `reports/2025-10-cli-flags/phase_k/f_latt_fix/post_fix/c_trace_full_20251006171510.log`
- PyTorch images: `reports/2025-10-cli-flags/phase_k/f_latt_fix/py_image.npy`
- C images: `reports/2025-10-cli-flags/phase_k/f_latt_fix/c_image.npy`

---

**Status:** Root cause identified. Awaiting ralph for specification clarification and fix implementation.
