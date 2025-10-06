# CLI-FLAGS-003 Phase H5b Implementation Notes

**Date:** 2025-10-21
**Engineer:** ralph (loop iteration in response to supervisor directive)

## Task
Restore pix0 override precedence in the custom-vector code path so PyTorch matches C behavior.

## Background
- **Previous understanding (Phase H3b1, 2025-10-06):** Believed C code IGNORED `-pix0_vector_mm` when custom detector vectors were present
- **Updated evidence (Phase J, 2025-10-21):** C code DOES honor the override and recomputes `Fbeam/Sbeam ≈0.2179/0.2139 m`
- **Problem:** PyTorch was skipping override application (line 542 condition: `and not has_custom_vectors`)

## Root Cause
The condition at `src/nanobrag_torch/models/detector.py:542` prevented pix0_override from being applied when custom detector vectors were present:

```python
if pix0_override_tensor is not None and not has_custom_vectors:
```

This caused PyTorch to use default beam center calculations (Fbeam/Sbeam ≈ 0.037 m) instead of the derived values from the override (Fbeam/Sbeam ≈ 0.218 m).

## Implementation Changes

### File: `src/nanobrag_torch/models/detector.py`

**Change 1: Removed has_custom_vectors gate (line 535-540)**
```python
# OLD (Phase H3b):
has_custom_vectors = (
    self.config.custom_fdet_vector is not None or
    self.config.custom_sdet_vector is not None or
    self.config.custom_odet_vector is not None
)

if pix0_override_tensor is not None and not has_custom_vectors:
    # Apply override...

# NEW (Phase H5b):
if pix0_override_tensor is not None:
    # Apply override even with custom vectors...
```

**Change 2: Updated documentation (lines 518-531)**
- Removed outdated comment "C code IGNORES -pix0_vector_mm entirely"
- Added reference to Phase J evidence (2025-10-21)
- Documented workflow: pix0_override → derive Fbeam/Sbeam → BEAM pivot formula

## Device/Dtype Neutrality Preserved
- All tensor conversions use `.to(device=self.device, dtype=self.dtype)`
- No hard-coded device assumptions
- Maintains vectorization (no Python loops)

## Expected Impact
- Fbeam/Sbeam should now be derived from pix0_override even when custom vectors present
- This should close the 1.14 mm pix0 Y-axis gap reported in Attempt #28
- F_latt components should align (C: 35.9/38.6/25.7 vs PyTorch: currently -2.4/11.8/-2.7)

## Next Steps
1. Generate PyTorch trace with updated code (Phase H5c)
2. Compare against C trace to verify pix0/Fbeam/Sbeam/F_latt parity
3. Update test expectations if parity achieved
4. Record Attempt #29 in docs/fix_plan.md

## Artifacts
- Implementation: `src/nanobrag_torch/models/detector.py` (commit pending)
- Test log: `reports/2025-10-cli-flags/phase_h5/pytest_h5b.log`
