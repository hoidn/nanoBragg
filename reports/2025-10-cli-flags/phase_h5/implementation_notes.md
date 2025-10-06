# CLI-FLAGS-003 Phase H5b Implementation Notes

## Attempt #29 (2025-10-21) - SUPERSEDED
**Date:** 2025-10-21
**Engineer:** ralph (loop iteration in response to supervisor directive)
**Status:** REVERTED by Attempt #31 (2025-10-22)

### Task
Restore pix0 override precedence in the custom-vector code path so PyTorch matches C behavior.

### Background
- **Previous understanding (Phase H3b1, 2025-10-06):** Believed C code IGNORED `-pix0_vector_mm` when custom detector vectors were present
- **Updated evidence (Phase J, 2025-10-21):** Believed C code DOES honor the override and recomputes `Fbeam/Sbeam ≈0.2179/0.2139 m`
- **Problem:** PyTorch was skipping override application (line 542 condition: `and not has_custom_vectors`)

### Implementation (REVERTED)
Removed the `has_custom_vectors` gate so pix0_override was applied unconditionally.

### Why Reverted
Fresh evidence collection in Attempt #30 (2025-10-22) **re-confirmed the original 2025-10-06 finding**:
- C traces WITH and WITHOUT override produce IDENTICAL geometry
- Dot-product derivation proves override is NOT applied when custom vectors present
- See `reports/2025-10-cli-flags/phase_h5/c_precedence_2025-10-22.md` for authoritative evidence

---

## Attempt #31 (2025-10-22) - CURRENT

**Date:** 2025-10-22
**Engineer:** ralph (revert per supervisor directive in `input.md`)

### Task
Revert pix0 override application when custom detector vectors are present

### Changes Made

#### File: `src/nanobrag_torch/models/detector.py` (lines 518-539)

**Previous behavior (Attempt #29):**
- Applied pix0_override unconditionally, even when custom detector vectors were present
- This was based on incorrect interpretation of C code behavior

**Updated behavior (Attempt #31 - this revert):**
- Added detection logic to check if any custom detector vectors are supplied:
  ```python
  has_custom_vectors = any([
      self.config.custom_fdet_vector is not None,
      self.config.custom_sdet_vector is not None,
      self.config.custom_odet_vector is not None
  ])
  ```
- Modified pix0_override condition to skip override when custom vectors present:
  ```python
  if pix0_override_tensor is not None and not has_custom_vectors:
  ```
- Updated comments to reference authoritative evidence document:
  `reports/2025-10-cli-flags/phase_h5/c_precedence_2025-10-22.md`

### Evidence Base

Per `reports/2025-10-cli-flags/phase_h5/c_precedence_2025-10-22.md` (Attempt #30):
- C code produces IDENTICAL geometry with and without `-pix0_vector_mm` when custom vectors supplied
- pix0_vector: [-0.216476, 0.216343, -0.230192] m (15 significant figures agreement)
- Fbeam: 0.217889 m, Sbeam: 0.215043 m (identical with/without override)
- Dot-product derivation proves override is not applied in custom-vector case
- C precedence logic: `if(custom_vectors) {compute_from_xbeam_ybeam(); ignore_override();}`

### Testing

**Targeted pytest:** `tests/test_cli_flags.py::TestCLIPix0Override`
- All 4 tests pass (2 CPU, 2 CUDA parametrizations)
- Runtime: 2.43s
- Log: `reports/2025-10-cli-flags/phase_h5/pytest_h5b_revert.log`

**Test coverage:**
- `test_pix0_override_beam_pivot_transform[cpu-dtype0]` ✅
- `test_pix0_override_beam_pivot_transform[cuda-dtype1]` ✅
- `test_pix0_vector_mm_beam_pivot[cpu]` ✅
- `test_pix0_vector_mm_beam_pivot[cuda]` ✅

### Device/Dtype Neutrality

Maintained throughout:
- `has_custom_vectors` computed from config (device-agnostic boolean checks)
- Existing device/dtype coercion preserved in override application path
- No hard-coded `.cpu()` or `.cuda()` calls added

### Rationale

This revert restores C-code precedence behavior:
- Custom detector vectors supersede pix0 overrides (spec-aligned precedence)
- Matches commit d6f158c logic (Phase H3b2) which correctly skipped overrides with custom vectors
- Unblocks Phase K normalization work by establishing correct baseline

### Next Steps (per plan Phase H5c)

1. Capture new PyTorch traces using the Phase H trace harness
2. Compare with C traces from `reports/2025-10-cli-flags/phase_h5/c_traces/2025-10-22/`
3. Update `phase_h5/parity_summary.md` with pix0/F_latt deltas
4. Verify `|Δpix0| < 5e-5 m` and `F_latt` ratio within 1e-3
5. Log Attempt #31 in `docs/fix_plan.md` before proceeding to Phase K

### Artifacts
- Implementation: `src/nanobrag_torch/models/detector.py:518-539`
- Test log: `reports/2025-10-cli-flags/phase_h5/pytest_h5b_revert.log`
- Evidence: `reports/2025-10-cli-flags/phase_h5/c_precedence_2025-10-22.md`
