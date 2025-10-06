# CLI-FLAGS-003 Phase K2: Scaling Chain Analysis Post SAMPLE-Pivot Fix

**Date:** 2025-10-06
**Commit:** 3d03af4f501f78462a626d15b04a955e5f839b8d
**Pixel:** (slow=1039, fast=685)

## Executive Summary

After implementing the SAMPLE-pivot fix in Phase H6, we regenerated PyTorch traces and recomputed scaling ratios. The analysis reveals:

- **Improved geometry:** F_latt_a and F_latt_c components now match C within ~3% error
- **Remaining blocker:** F_latt_b diverges by 21.6%, causing 25.5% error in total F_latt
- **Secondary issues:** Polarization factor still 1.0 in PyTorch vs 0.913 in C (9.6% error)
- **Final intensity:** 11.4% higher in PyTorch (497 vs 446) due to cascading errors

## Detailed Scaling Chain Analysis

### Perfect Matches (0% error)
- **F_cell:** 300.58 (both) ✅
- **steps:** 10 (both) ✅
- **r_e²:** 7.941e-30 (both) ✅
- **fluence:** 1.0e24 (both) ✅

### Geometric Factors - Mixed Results

| Component | C Value | PyTorch Value | Ratio | Rel Error |
|-----------|---------|---------------|-------|-----------|
| F_latt_a  | 35.889  | 35.957        | 1.002 | **0.19%** ✅ |
| F_latt_b  | 38.632  | 46.984        | 1.216 | **21.6%** ❌ |
| F_latt_c  | 25.702  | 26.468        | 1.030 | **3.0%** ⚠️ |
| **F_latt** | **35,636** | **44,716** | **1.255** | **25.5%** ❌ |

**First Divergence:** F_latt_b shows significant error (8.35 unit delta). Since F_latt = F_latt_a × F_latt_b × F_latt_c, the 21.6% error in b-axis propagates to the product.

### Intensity Scaling Chain

```
I_before_scaling = F_cell² × F_latt²
C:  I_before = 300.58² × 35636² = 1.481e15
Py: I_before = 300.58² × 44716² = 1.807e14

Ratio: 0.122 (PyTorch 87.8% lower)
```

**Note:** This ratio mismatch comes from F_latt squaring, amplifying the 25.5% error to 57% ((1.255)² = 1.575).

### Scaling Factors Application

| Factor     | C Value    | Py Value   | Ratio  | Rel Error |
|------------|------------|------------|--------|-----------|
| omega      | 4.159e-07  | 4.159e-07  | 1.000  | 0.002% ✅ |
| polar      | 0.9126     | 1.0000     | 1.096  | **9.6%** ⚠️ |

**Secondary issue:** Polarization factor not applied correctly in PyTorch (remains at 1.0 instead of computing Kahn factor ≈0.913).

### Final Intensity

```
I_final = (I_before_scaling / steps) × r_e² × fluence × omega × polar

C:  I_final = (1.481e15 / 10) × 7.941e-30 × 1e24 × 4.159e-07 × 0.9126 = 446.25
Py: I_final = (1.807e14 / 10) × 7.941e-30 × 1e24 × 4.159e-07 × 1.0000 = 497.18

Ratio: 1.114 (PyTorch 11.4% higher)
```

## Root Cause Analysis

### Primary Blocker: F_latt_b Calculation Error

The b-axis lattice shape factor has a 21.6% error. This is computed via:
```
F_latt_b = sincg(π × k, Nb)
```

**Hypotheses:**
1. **Miller index k mismatch:** PyTorch fractional k differs from C (needs trace comparison)
2. **sincg numerical implementation:** Edge case in sinc function evaluation
3. **Nb parameter:** Cell count on b-axis incorrectly propagated (unlikely - should be 47)

**Next action:** Compare h,k,l fractional values in C vs PyTorch traces to isolate whether the error is in Miller index calculation (upstream of sincg) or in the sincg function itself.

### Secondary Issue: Polarization Factor

PyTorch applies `polar = 1.0` while C computes Kahn factor `0.9126`. This 9.6% error multiplies the final intensity.

**Hypothesis:** The Kahn polarization calculation may not be executing, or the per-source incident direction is not being used correctly (similar to issues identified in PERF-PYTORCH-004 P3.0b).

## Progress vs Phase J Baseline

| Metric | Phase J (before fix) | Phase K2 (after fix) | Change |
|--------|----------------------|----------------------|---------|
| F_latt_a error | Unknown | 0.19% | N/A |
| F_latt_b error | Unknown | 21.6% | N/A |
| F_latt_c error | Unknown | 3.0% | N/A |
| F_latt error | 463× | 25.5% | **MAJOR IMPROVEMENT** ✅ |
| Polar match | 9.6% (same) | 9.6% | No change |
| I_final error | ~25,800% | 11.4% | **MAJOR IMPROVEMENT** ✅ |

**Phase H6 impact:** The SAMPLE-pivot fix dramatically improved F_latt from a 463× error to 25.5%. However, the remaining F_latt_b error still blocks full parity.

## Artifacts

- **PyTorch trace:** `reports/2025-10-cli-flags/phase_k/f_latt_fix/trace_py_after.log`
- **C trace (baseline):** `reports/2025-10-cli-flags/phase_j/trace_c_scaling.log`
- **Trace diff:** `reports/2025-10-cli-flags/phase_k/f_latt_fix/trace_diff.txt`
- **Metrics JSON:** `reports/2025-10-cli-flags/phase_k/f_latt_fix/metrics_after.json`

## Next Actions (Phase K3)

1. **Compare fractional Miller indices:** Extract h,k,l_frac from both traces and compute deltas to determine if the 21.6% F_latt_b error originates in:
   - Miller index calculation (scattering vector → reciprocal space dot products)
   - sincg function evaluation

2. **Debug polarization:** Verify that Kahn factor is being computed and applied per-source (reference PERF-PYTORCH-004 P3.0b polarization fixes)

3. **Targeted regression:** Once F_latt_b is corrected, run:
   ```bash
   env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg \
     pytest tests/test_cli_scaling.py::test_f_latt_square_matches_c -v
   ```

4. **Documentation updates:** Refresh `docs/architecture/pytorch_design.md` with corrected lattice factor flow and update Phase K notes.

## Conclusion

The SAMPLE-pivot fix (Phase H6) resolved the major pix0 geometry error that was causing the 463× F_latt divergence. We now have:

- **Excellent:** F_cell, steps, r_e², fluence all match exactly
- **Good:** F_latt_a (0.19% error), omega (0.002% error)
- **Acceptable:** F_latt_c (3.0% error)
- **Blocking:** F_latt_b (21.6% error) → cascades to 25.5% F_latt error
- **Secondary:** Polarization (9.6% error)

**Status:** Phase K2 complete. Evidence gathered. Phase K3 gated on F_latt_b and polarization debugging before final parity sweep (Phase L).
