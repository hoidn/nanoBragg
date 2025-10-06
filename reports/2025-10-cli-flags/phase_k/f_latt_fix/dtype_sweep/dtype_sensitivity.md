# CLI-FLAGS-003 Phase K3d: Dtype Sensitivity Analysis

## Executive Summary

**Finding:** Float64 precision does **NOT** resolve the F_latt_b discrepancy.

**Conclusion:** The 21.6% F_latt_b drift between C and PyTorch is NOT caused by floating-point precision limitations. The root cause lies elsewhere in the orientation/geometry pipeline, most likely the MOSFLM rescaling issue documented in Phase K2b.

## Test Configuration

- **Date:** 2025-10-06
- **Commit:** (current HEAD)
- **Target Pixel:** (133, 134) - on-peak pixel from Phase J/K traces
- **Device:** CPU (for determinism per testing_strategy.md §2.5.1)
- **Test Case:** Supervisor command configuration (MOSFLM A.mat, λ=0.9768 Å)

## Quantitative Results

### Miller Index Precision

| Component | Float32 | Float64 | Δ (float64-float32) | Relative Error |
|-----------|---------|---------|---------------------|----------------|
| h_frac    | 26.415195 | 26.415194 | -1.09e-06 | 4.12e-06% |
| k_frac    | -9.899110 | -9.899110 | -1.38e-07 | 1.40e-06% |
| l_frac    | -11.067196 | -11.067192 | 4.13e-06 | 3.73e-05% |

**Interpretation:** Miller index precision is excellent in both float32 and float64. The fractional differences are 6-7 orders of magnitude smaller than the Miller indices themselves, ruling out index rounding as a significant error source.

### Lattice Shape Factors (SQUARE Model)

| Component | Float32 | Float64 | Δ (float64-float32) | Relative Error |
|-----------|---------|---------|---------------------|----------------|
| F_latt_a  | 0.171621 | 0.171805 | 1.84e-04 | 0.11% |
| F_latt_b  | 2.326403 | 2.326202 | -2.02e-04 | 0.0087% |
| F_latt_c  | -0.765703 | -0.767915 | -2.21e-03 | 0.29% |
| F_latt    | -0.305715 | -0.306900 | -1.19e-03 | 0.39% |

**Interpretation:** Float64 improves F_latt precision by <0.4%, which is negligible compared to the 93.98% error vs C.

### C Reference Comparison

| Implementation | F_latt_b | Error vs C |
|----------------|----------|------------|
| C (reference)  | **38.63** | — |
| PyTorch float32 | 2.33 | **93.98%** |
| PyTorch float64 | 2.33 | **93.98%** |

**Critical Finding:** Both float32 and float64 produce nearly identical F_latt_b values (2.33), which are **16.6× smaller** than C's 38.63. This is a systematic error, not a precision issue.

## Scaling Factors

| Factor | Float32 | Float64 | Notes |
|--------|---------|---------|-------|
| omega_pixel | 1.087335e-04 sr | 1.087335e-04 sr | Identical to 7 sig figs |
| polar | 0.0 | 0.0 | Matches C default |

## Root Cause Analysis

### What dtype sensitivity ruled out:
1. ✅ Miller index rounding errors (precision is 6-7 orders of magnitude better than needed)
2. ✅ sincg numerical instability (differences are <0.4%)
3. ✅ Accumulation errors in F_latt product (matches expected precision)

### What remains (from Phase K2b):
1. **MOSFLM rescaling mismatch** (orientation_delta.md): PyTorch always rescales cross products to match cell parameters, but C only rescales when `user_cell=1` (i.e., `-cell` flag provided). Current supervisor command uses `-matrix A.mat` without `-cell`, so C has `user_cell=0` and skips rescaling.
   - **Impact:** Real-space lattice vectors differ by ≈0.6% in magnitude
   - **Propagation:** Magnitude error → Miller index calculation → sincg arguments → F_latt

2. **Polarization default** (Phase I2 / K3b): Needs verification that PyTorch polar=0.0 triggers the same geometry-dependent calculation as C (expected ~0.9126 for this pixel).

3. **Geometric orientation discrepancies:** The fact that F_latt_b differs by 16.6× suggests a more fundamental issue than just vector magnitude - possibly in how MOSFLM reciprocal vectors are converted to real-space vectors.

## Recommendations

### Immediate Next Steps (per plan.md K3a/K3b):

1. **K3a - Guard MOSFLM rescale path:**
   - Bypass cross-product rescaling in `Crystal.compute_cell_tensors` when `mosflm_a_star`/`b_star`/`c_star` are provided
   - Target: `src/nanobrag_torch/models/crystal.py:681-705`
   - Expected impact: Should bring PyTorch vector magnitudes into parity with C's unrescaled values

2. **K3b - Realign polarization defaults:**
   - Verify BeamConfig.polarization_factor=0.0 triggers geometry-dependent calculation
   - Confirm result matches C's ~0.9126 for this pixel
   - Less likely to explain the massive F_latt_b error, but needed for complete parity

3. **Post-K3a verification:**
   - Rerun this dtype sweep script after K3a implementation
   - Expected: F_latt_b should move significantly closer to C's 38.63
   - If still divergent, investigate:
     - MOSFLM → real-space conversion formula
     - Reciprocal vector recalculation sequence (per CLAUDE.md Rule #13)
     - Misset application order

### Evidence Artifacts

All results from this analysis are stored in:
```
reports/2025-10-cli-flags/phase_k/f_latt_fix/dtype_sweep/
├── float32_run.log          # Full float32 trace output
├── float64_run.log          # Full float64 trace output
├── trace_float32.json       # Machine-readable float32 data
├── trace_float64.json       # Machine-readable float64 data
├── dtype_sensitivity.json   # Automated comparison summary
└── dtype_sensitivity.md     # This document
```

## Technical Notes

### Instrumentation Compliance

Per CLAUDE.md Core Rule #0.3 (Instrumentation/Tracing Discipline), this analysis reused production code paths:
- `crystal.a`, `crystal.b`, `crystal.c` for real-space vectors
- `detector.get_pixel_coords()` and `detector.pix0_vector` for geometry
- `nanobrag_torch.utils.physics.sincg` for lattice factors

No parallel reimplementations were introduced, ensuring trace values reflect actual production behavior.

### Reproducibility

```bash
# Float32 run
NB_PYTORCH_DTYPE=float32 PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE \
  python reports/2025-10-cli-flags/phase_k/f_latt_fix/analyze_scaling.py

# Float64 run
NB_PYTORCH_DTYPE=float64 PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE \
  python reports/2025-10-cli-flags/phase_k/f_latt_fix/analyze_scaling.py
```

Environment requirements:
- Editable install: `pip install -e .`
- PyTorch with CPU support
- MOSFLM A.mat file in repository root

## Conclusion

Dtype precision is **not** the root cause of the F_latt_b discrepancy. The 93.98% error is systematic and consistent across float32 and float64, pointing to a geometric/orientation issue rather than numerical precision.

Phase K3a (MOSFLM rescale guard) is the next critical step to resolve this discrepancy.
