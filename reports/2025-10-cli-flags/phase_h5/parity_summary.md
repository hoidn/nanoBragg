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
⏳ **Parity evidence pending** — need updated PyTorch traces (post-revert) to confirm pix0/Fbeam/Sbeam/hkl/`F_latt` align with the C logs captured on 2025-10-22.

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
