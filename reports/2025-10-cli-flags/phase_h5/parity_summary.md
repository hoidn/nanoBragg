# Phase H5 Parity Summary

**Date:** 2025-10-22
**Task:** CLI-FLAGS-003 Phase H5 — Reinstate C precedence for pix0 overrides when custom detector vectors are supplied
**Goal:** Confirm the revert that skips `-pix0_vector_mm` whenever custom detector vectors are present, then capture matching PyTorch traces so Phase K normalization work starts from a geometry-accurate baseline.

## Implementation Snapshot

### Code Changes
**File:** `src/nanobrag_torch/models/detector.py`

1. **Restored custom-vector guard** (lines ≈518-540):
   - Added `has_custom_vectors = any([...])` helper mirroring C precedence.
   - Gated pix0 override projection with `if pix0_override_tensor is not None and not has_custom_vectors:`.
   - Refreshed comments to cite `reports/2025-10-cli-flags/phase_h5/c_precedence_2025-10-22.md` (evidence that C ignores the override in this configuration).

2. **Doc updates**:
   - `reports/2025-10-cli-flags/phase_h5/implementation_notes.md` now records the revert (Attempt #31) and supersedes Attempt #29 notes.

### Regression Test Results
**Command:** `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestCLIPix0Override -v`

**Results:** ✅ **4 passed in 2.43s** (`reports/2025-10-cli-flags/phase_h5/pytest_h5b_revert.log`)

Breakdown:
- Overrides skipped when custom vectors present (CPU + CUDA parameterisations)
- Overrides still applied without custom vectors (CPU + CUDA)

Core CLI/geometry suites were not rerun in this loop; last recorded run (2025-10-17) remained green.

## Observed Physics Impact (Post-Revert)
- pix0 deltas vs C (pre-traces): expected to return to <5e-5 m once PyTorch traces are refreshed.
- Fbeam/Sbeam: should revert to ≈0.218 m after re-running trace harness.
- `F_latt` disparity persists until Phase K aligns the sincg usage.

## Verification Status

✅ **Implementation complete** — precedence matches C behavior again.
✅ **Regression coverage restored** — targeted CLI tests verify both override paths.
✅ **PyTorch trace captured** — trace_py.log generated on 2025-10-22 (Phase H5c).
⚠️ **Parity gap identified** — pix0 ΔF = 1.136e-03 m (1.1mm) exceeds <5e-5 m threshold.

## Parity Metrics (Phase H5c — 2025-10-22)

**Command:**
```bash
PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE \
python reports/2025-10-cli-flags/phase_h/trace_harness.py \
  --out reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-22/trace_py.log
```

**Pixel:** (slow=1039, fast=685)

### Comparison Table

| Variable | C Value | PyTorch Value | Delta | Threshold | Status |
|----------|---------|---------------|-------|-----------|--------|
| pix0_S (m) | -0.216475836 | -0.216336514 | +1.393e-04 | <5e-5 | ⚠️ **FAIL** |
| pix0_F (m) | 0.216343050 | 0.215206681 | -1.136e-03 | <5e-5 | ⚠️ **FAIL** |
| pix0_O (m) | -0.230192414 | -0.230198009 | -5.594e-06 | <5e-5 | ⚠️ **FAIL** |
| fdet_vector | 0.999982, -0.005998, -0.000118 | 0.999982, -0.005998, -0.000118 | 0.0 | exact | ✅ **PASS** |
| sdet_vector | -0.005998, -0.99997, -0.004913 | -0.005998, -0.99997, -0.004913 | 0.0 | exact | ✅ **PASS** |
| hkl_frac | (not logged) | 2.098, 2.017, -12.871 | N/A | <1e-6 residual | ⏳ pending C trace |
| F_latt components | (not logged) | -3.294, 10.815, -1.823 | N/A | <1e-3 relative | ⏳ pending C trace |
| F_latt (product) | (not logged) | 64.945 | N/A | <1e-3 relative | ⏳ pending C trace |
| F_cell | (not logged) | 300.58 | N/A | N/A | ⏳ HKL value |
| I_pixel_final | (not logged for pixel) | 0.003838 | N/A | N/A | ⏳ pending C trace |

### Key Findings

1. **pix0 divergence:** All three components fail the <5e-5 m threshold, with ΔF = 1.1mm being the largest deviation.
   - This suggests a fundamental difference in how pix0 is calculated between C and PyTorch, despite the custom-vector guard being restored.
   - Basis vectors match exactly, ruling out orientation issues.

2. **Basis vector parity:** ✅ fdet and sdet vectors match C exactly, confirming detector orientation is correctly configured.

3. **Missing C instrumentation:** F_latt components, fractional h/k/l, and per-pixel intensities are not logged in the C trace. Phase K1 will need additional C instrumentation to validate lattice factor calculations.

### Analysis

The pix0 delta pattern (S: +139μm, F: -1136μm, O: -5.6μm) suggests systematic bias rather than random error. Possible causes:

- Different beam-center → pix0 conversion logic
- Pivot mode calculation differs despite identical detector_pivot setting
- MOSFLM +0.5 pixel offset applied differently
- Custom vector projection math differs from C implementation

**Recommendation:** Phase K work should be blocked until pix0 parity is resolved. The 1.1mm fast-axis deviation will cascade into incorrect Miller index calculations and invalidate lattice factor comparisons.

## Immediate Next Steps (Phase H5c)
1. Create output directory: `mkdir -p reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-22/`.
2. Run the PyTorch trace harness:
   ```bash
   PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE \
   python reports/2025-10-cli-flags/phase_h/trace_harness.py \
     --out reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-22/trace_py.log
   ```
3. Diff against `reports/2025-10-cli-flags/phase_h5/c_traces/2025-10-22/trace_c_with_override.log` and record deltas in a refreshed `parity_summary.md` table (<5e-5 m pix0, <1e-3 relative `F_latt`).
4. Log the outcome in docs/fix_plan.md Attempt history when metrics land.

## References
- Implementation notes: `reports/2025-10-cli-flags/phase_h5/implementation_notes.md`
- C precedence proof: `reports/2025-10-cli-flags/phase_h5/c_precedence_2025-10-22.md`
- Plan checkpoint: `plans/active/cli-noise-pix0/plan.md` Phase H5/H5c
- Fix plan entry: `docs/fix_plan.md` §[CLI-FLAGS-003]
