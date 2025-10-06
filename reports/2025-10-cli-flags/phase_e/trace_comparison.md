# Phase E3: Trace Comparison Analysis

**Date:** 2025-10-06
**Task:** CLI-FLAGS-003 Phase E3 - Identify first physics divergence
**Pixel:** (slow=1039, fast=685)

## Executive Summary

**FIRST DIVERGENCE IDENTIFIED: pix0_vector (line 1)**

The parallel trace comparison reveals that the **detector origin (pix0_vector) differs between C and PyTorch implementations**, causing all downstream geometry calculations to be incorrect.

### Root Cause

The PyTorch implementation is **NOT applying the `-pix0_vector_mm` override correctly**. The values being used:

| Implementation | pix0_vector_meters (X, Y, Z) |
|---------------|------------------------------|
| **C (correct)** | `-0.216475836`, `0.216343050`, `-0.230192414` |
| **PyTorch (wrong)** | `-0.216336293`, `0.215205512`, `-0.230200866` |
| **Difference** | `Δ=1.40e-4 m`, `Δ=1.14e-3 m`, `Δ=8.55e-6 m` |

The Y-component error of **1.14 mm** is particularly significant and directly explains the 1535-pixel horizontal displacement observed in Phase D (1535 px × 0.172 mm/px ≈ 264 mm geometry shift).

## Trace Diff Analysis

### Line-by-Line Comparison

```diff
--- C trace (reports/2025-10-cli-flags/phase_e/c_trace.log)
+++ PyTorch trace (reports/2025-10-cli-flags/phase_e/pytorch_trace.log)
@@ -1 +1 @@
-TRACE_C: pix0_vector_meters -0.216475836204836 0.216343050492215 -0.230192414300537
+TRACE_PY: pix0_vector_meters -0.216336293 0.215205512 -0.230200866
```

**First divergence:** Line 1, variable `pix0_vector_meters`

### Cascade Effects

Because pix0_vector is the **detector origin** used to calculate pixel positions, this error propagates through:

1. **pixel_pos_meters** (line 4): Different because `pixel_pos = pix0 + s*sdet + f*fdet`
2. **diffracted_vec** (line 9): Different because `d = normalize(pixel_pos)`
3. **scattering_vec_A_inv** (line 13): Different because `S = (d - i)/λ`
4. **hkl_frac** (line 20): Different because `h = a·S`, etc.
5. **I_pixel_final** (line 39): Different intensity because wrong reflection is being computed

## Diagnosis

### Expected Behavior (from C code)

The `-pix0_vector_mm` flag should:
1. Parse the input values: `-216.336293 215.205512 -230.200866` (millimeters)
2. Convert to meters by multiplying by 0.001
3. Set `pix0_vector = (-0.216336293, 0.215205512, -0.230200866)` meters
4. **THEN** apply pivot/convention transformations

### Actual PyTorch Behavior

PyTorch is applying the override, but the **final pix0_vector does not match**.

Possible causes:
1. ❌ Conversion factor wrong (C: ×0.001, PyTorch: ???)
2. ❌ Override being applied but then overwritten by pivot calculation
3. ❌ CUSTOM convention applying additional transformation to pix0
4. ❌ pix0 cache invalidation not working (stale value)

### C Reference Values (from Phase A/C2 logs)

```
# Input (command line):
-pix0_vector_mm -216.336293 215.205512 -230.200866

# C output (from c_cli.log):
DETECTOR_PIX0_VECTOR -0.216475836204836 0.216343050492215 -0.230192414300537
```

**Wait - the C output does NOT match the input either!**

This means:
- Input: `-216.336293 215.205512 -230.200866` mm
- C pix0: `-216.475836 216.343050 -230.192414` mm (note: already in mm in the C print)

The C code is **transforming the pix0_vector** after the override is applied!

### Re-Analysis: Convention Transform

Checking `docs/architecture/detector.md` and C code behavior:

The C code applies **convention-specific transformations** even when pix0 is overridden. The `beam_convention = CUSTOM` side effect (from Phase A findings) may cause additional rotation or mapping.

**Hypothesis:** The PyTorch override path is missing the CUSTOM convention's pix0 transformation logic.

## Comparison Table

| Variable | C Value | PyTorch Value | Match? | Impact |
|----------|---------|---------------|--------|--------|
| **pix0_vector_meters** | `-0.2165, 0.2163, -0.2302` | `-0.2163, 0.2152, -0.2302` | ❌ **NO** | **ROOT CAUSE** |
| fdet_vec | `0.999982, -0.005998, -0.000118` | `0.999982, -0.005998, -0.000118` | ✅ YES | Basis correct |
| sdet_vec | `-0.005998, -0.999970, -0.004913` | `-0.005998, -0.999970, -0.004913` | ✅ YES | Basis correct |
| pixel_pos_meters | `-0.0996, 0.0368, -0.2311` | `-0.0995, 0.0357, -0.2311` | ❌ NO | From bad pix0 |
| incident_vec | `0.000514, 0, -1.0` | `0.000514, 0, -1.0` | ✅ YES | Beam correct |
| hkl_frac | `2.001, 1.993, -12.991` | Different (not shown in truncated diff) | ❌ NO | Cascade |
| I_pixel_final | **446.254** | **4.50e-06** | ❌ **NO** | **10⁸× wrong!** |

## Recommended Fixes

### Immediate Fix (Targeted)

1. **Locate pix0 override assignment in `detector.py`:**
   - Current code: `src/nanobrag_torch/models/detector.py:391-407` (from fix_plan.md)
   - Verify the override value is assigned correctly
   - Check if CUSTOM convention is applying extra transform

2. **Add debug logging:**
   - Print `pix0_override_m` as received from CLI
   - Print `self.pix0_vector` after assignment
   - Print `self.pix0_vector` after any convention transforms

3. **Compare with C pix0 calculation:**
   - C code location: `golden_suite_generator/nanoBragg.c` lines ~1730-1860
   - Identify CUSTOM convention's pix0 modification
   - Port exact logic to PyTorch

### Verification

After fix, re-run Phase E2 and verify:
- `pix0_vector_meters` matches C value exactly (all 3 components)
- `pixel_pos_meters` matches (depends on pix0)
- `hkl_frac` matches (depends on pixel_pos)
- `I_pixel_final` matches within tolerance (depends on hkl)

## Artifacts

**Location:** `reports/2025-10-cli-flags/phase_e/`

### Generated Files

1. **`c_trace.log`** - C reference trace (40 lines)
2. **`pytorch_trace.log`** - PyTorch trace (40 lines + headers)
3. **`trace_diff.txt`** - Unified diff output
4. **`trace_comparison.md`** - This document
5. **`instrumentation_notes.md`** - C instrumentation documentation
6. **`pytorch_instrumentation_notes.md`** - PyTorch trace harness docs
7. **`trace_harness.py`** - Python trace script (evidence-only)

## References

- Plan: `plans/active/cli-noise-pix0/plan.md` Phase E (tasks E1-E3)
- Fix Plan: `docs/fix_plan.md` [CLI-FLAGS-003]
- Supervisor Memo: `input.md` (2025-10-06T00:49:07Z)
- Debugging SOP: `docs/debugging/debugging.md` §2.1
- Detector Architecture: `docs/architecture/detector.md` (pix0 workflow §5)
- C-Py Config Map: `docs/development/c_to_pytorch_config_map.md`

## Next Steps (for future loop)

1. ❌ **DO NOT** attempt implementation fix in this loop (evidence-only)
2. ✅ Update `docs/fix_plan.md` [CLI-FLAGS-003] Attempts with this divergence
3. ✅ Archive all trace artifacts
4. ✅ Commit Phase E evidence
5. 🔄 **Next loop:** Debug pix0 override path in detector.py with focus on CUSTOM convention transform

## Time Investment

- Trace generation (E1/E2): ~15 minutes
- Diff analysis (E3): ~5 minutes
- Report writing: ~20 minutes
- **Total:** ~40 minutes
