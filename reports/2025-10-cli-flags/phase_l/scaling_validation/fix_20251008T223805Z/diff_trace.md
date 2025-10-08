# Phase M4d Trace Comparison Summary

**Date:** 2025-10-08
**Git SHA:** b2d2f64
**Context:** CLI-FLAGS-003 Phase M4d evidence capture after normalization fix

## Executive Summary

The normalization fix (Attempts #188-#189, commit fe3a328) has been applied to `src/nanobrag_torch/simulator.py`, ensuring a single `/steps` division occurs at line 1127. However, the trace comparison against the Phase M1 baseline still shows a -14.6% divergence in `I_before_scaling`.

## Trace Generation

**PyTorch Trace:**
- Command: `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --pixel 685 1039 --device cpu --dtype float64 --out reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/trace_py_scaling.log`
- Captured: 114 TRACE_PY lines
- Final intensity: 2.45946637686509e-07
- Device: CPU
- Dtype: float64

**C Trace (Baseline):**
- Source: `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/c_trace_scaling.log`
- Generated: Phase M1 (2025-10-08)

## Comparison Results

| Factor | C Value | PyTorch Value | Δ (rel) | Status |
|--------|---------|---------------|---------|--------|
| **I_before_scaling** | 943654.809 | 805473.787 | **-14.6%** | **CRITICAL** |
| r_e_sqr | 7.941e-30 | 7.941e-30 | 0.0 | PASS |
| fluence | 1.0e+24 | 1.0e+24 | 0.0 | PASS |
| steps | 10 | 10 | 0.0 | PASS |
| capture_fraction | 1.0 | 1.0 | 0.0 | PASS |
| polar | 0.914639699 | 0.914639662 | -4.0e-08 | PASS |
| omega_pixel | 4.204e-07 | 4.204e-07 | -4.8e-07 | PASS |
| cos_2theta | 0.910647790 | 0.910647743 | -5.2e-08 | PASS |
| **I_pixel_final** | 2.881e-07 | 2.460e-07 | **-14.6%** | **CRITICAL** |

## First Divergence

**Factor:** `I_before_scaling`
**Status:** The divergence occurs BEFORE normalization, indicating the issue is in the upstream physics calculation (F_cell, F_latt, or accumulation), not in the normalization step itself.

All downstream scaling factors (r_e², fluence, steps, capture_fraction, polarization, omega, cos2θ) match within tolerance (≤1e-6 relative).

## Analysis

### Code Verification
Inspected `src/nanobrag_torch/simulator.py`:
- ✅ Line 1127: Single `/steps` division present
- ✅ Line 956 comment: "Do NOT divide by steps here"
- ✅ Line 1041 comment: "Do NOT divide by steps here"
- ✅ Only ONE normalization occurs at final scaling

The normalization fix IS correctly implemented.

### Divergence Interpretation

The -14.6% deficit persists at the same magnitude as the original Phase M1 baseline, suggesting:

1. **Hypothesis A (Most Likely):** The C baseline trace was generated BEFORE understanding the full upstream physics issue. The normalization fix addressed one problem, but there may be additional discrepancies in:
   - F_cell calculation or interpolation
   - F_latt computation (sincg evaluation)
   - Per-φ accumulation logic
   - Mosaic domain sampling

2. **Hypothesis B:** The comparison is valid, but the normalization fix alone was insufficient. Additional investigation is needed into the `I_before_scaling` accumulation path.

3. **Hypothesis C:** The C trace may need regeneration with parameters that exactly match the PyTorch implementation's understanding of the supervisor command.

## Recommendation

**Escalate to supervisor** with the following questions:

1. Should a fresh C trace be generated to ensure apple-to-apple comparison?
2. Is there documentation of known upstream physics discrepancies beyond normalization?
3. What is the expected tolerance for `I_before_scaling` at this phase?

The evidence bundle is complete for M4d documentation purposes, but the parity gate remains blocked pending clarification.

## Artifacts

- `trace_py_scaling.log` — PyTorch trace with normalization fix
- `compare_scaling_traces.txt` — Detailed factor comparison
- `metrics.json` — Machine-readable comparison results
- `run_metadata.json` — Execution metadata
- `blockers.md` — Detailed blocker documentation
- `commands.txt` — Reproduction commands
- `sha256.txt` — Artifact checksums

## Next Steps (Pending Supervisor Input)

1. ✅ M4d artifacts captured (this document)
2. ⏸️ M4d closure BLOCKED pending divergence resolution
3. ⏸️ M5 (CUDA validation) deferred until M4d green
4. ⏸️ M6 (ledger sync) deferred until M4d green
