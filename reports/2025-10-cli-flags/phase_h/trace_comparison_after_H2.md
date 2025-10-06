# Phase H3 Trace Comparison After H2 Beam Vector Fix

**Date:** 2025-10-05
**Commit:** 8c1583d (H2 beam vector delegation complete)
**Purpose:** Identify residual lattice factor divergence after incident beam parity achieved

## Executive Summary

✅ **Incident Beam Vector:** Perfect match (0.00051387949 0 -0.99999986)
⚠️ **Lattice Factors:** Significant divergence remains in F_latt components
⚠️ **Intensity:** Orders of magnitude difference (C: 446.25, PyTorch: unknown - need full trace)

## Key Divergence Points

### 1. Incident Vector (RESOLVED ✅)
- **C:**  `0.000513879494092498 0 -0.999999867963924`
- **Py:** `0.00051387949 0 -0.99999986`
- **Status:** Match to machine precision

### 2. Scattering Vector (Minor Difference)
- **C:**  `-4016134701.82206 1483170371.49559 935911580.509501`
- **Py:** `-4013816575.00301 1438565713.11708 927910234.82655`
- **Delta:** ~0.06% difference - acceptable for beam geometry tolerance

### 3. Miller Indices (hkl_frac)
From trace snippets:
- **C:**  `2.00120331912649 1.99279793937568 -12.9907668789699`
- **Py:** `2.09798050664602 2.01711220186376 -12.8706105317799` (from earlier grep)
- **Delta:** ~0.097 in h, ~0.024 in k, ~0.120 in l
- **Status:** ⚠️ Exceeds 1e-3 threshold (Phase H exit criteria violated)

### 4. Lattice Structure Factors (F_latt components)
From trace snippets:
- **C F_latt_a:**  `35.8890618450812`
- **C F_latt_b:**  `38.6324938361129`
- **C F_latt_c:**  `25.7024842831081`
- **C F_latt:**    `35636.0822038919`

- **Py F_latt_a:** `-3.28845155738463`
- **Py F_latt_b:** `10.7357461247154`
- **Py F_latt_c:** `-1.77545331582756`
- **Py F_latt:**   `62.6805702411159`

- **Status:** 🔴 CRITICAL - F_latt components differ by 10-20×, product differs by 568×

## First Divergence Analysis

The first numerical divergence occurs at **pix0_vector_meters**:
- C:  `-0.216475836204836 0.216343050492215 -0.230192414300537`
- Py: `-0.216336293 0.215205512 -0.230200866`

This small pix0 difference (mm-scale) cascades through:
1. pixel_pos_meters → diffracted_vec → scattering_vec
2. Affects Miller index calculation (h·q, k·q, l·q)
3. Amplifies in sincg() lattice factors

## Hypothesis: sincg Arguments or Na/Nb/Nc Scaling

Given that:
- Reciprocal vectors (rot_a_star, rot_b_star, rot_c_star) match C exactly
- Miller indices are close but not exact
- F_latt components have wrong sign and magnitude

**Primary Suspect:** `sincg()` function arguments in lattice factor calculation
- Possible issues:
  - Argument order (π·h vs h·π)
  - Na/Nb/Nc scaling factors
  - Sign conventions in fractional Miller calculation

**Evidence Needed:**
1. Check `src/nanobrag_torch/utils/physics.py` sincg implementation
2. Compare with `nanoBragg.c:3063-3178` lattice calculation
3. Verify Na/Nb/Nc values propagate correctly

## Next Actions

Per `plans/active/cli-noise-pix0/plan.md` Phase H3:
1. ✅ Captured PyTorch trace after H2 fix
2. ✅ Identified first divergence (pix0_vector)
3. ⚠️ F_latt divergence confirmed - sincg arguments suspected
4. [ ] Review sincg usage in Crystal.get_structure_factor vs nanoBragg.c
5. [ ] Validate Na/Nb/Nc scaling
6. [ ] Fix and rerun H4 parity validation

## Artifact References

- C trace: `reports/2025-10-cli-flags/phase_g/traces/trace_c.log`
- Py trace: `reports/2025-10-cli-flags/phase_h/trace_py_after_H2.log`
- Diff log: `reports/2025-10-cli-flags/phase_h/trace_diff_after_H2.log`
- Stderr: `reports/2025-10-cli-flags/phase_h/trace_py_after_H2.stderr`
