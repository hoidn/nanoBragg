# Phase C2/C3 Documentation Sweep — Summary

**Date:** 2025-10-08T20:01:54Z
**Engineer:** Ralph (loop i=177)
**Mode:** Docs
**Plan Reference:** plans/active/phi-carryover-removal/plan.md Phase C

## Objective

Complete Phase C2 and C3 of the phi-carryover removal plan:
- C2: Update `docs/bugs/verified_c_bugs.md` to mark C-PARITY-001 as C-only
- C3: Sweep remaining carryover references in tests/docs/code

## Changes Made

### 1. docs/bugs/verified_c_bugs.md (Phase C2)

**Lines 179-189:** Rewrote the "PyTorch Parity Shim" section to emphasize:
- C-PARITY-001 is a **C-only defect** (PyTorch does NOT reproduce it)
- Current behavior uses spec-compliant fresh rotations (specs/spec-a-core.md:211-214)
- Historical shim was **fully removed in commit b9db0a3 (2025-10-08)**
- Removed references to "plumbing in progress" and deleted `CrystalConfig.phi_carryover_mode`

**Lines 187-189:** Removed stale PyTorch code reference to `crystal.py:1084-1128` (shim implementation that no longer exists)

### 2. tests/test_cli_scaling_parity.py (Phase C3)

**Status:** Deleted
**Rationale:** Test instantiated `CrystalConfig(... phi_carryover_mode="c-parity")` which now throws an error. The shim API no longer exists, and parity validation is covered by `tests/test_cli_scaling_phi0.py` for spec mode.

### 3. src/nanobrag_torch/models/crystal.py (Phase C3)

**Lines 1219-1256:** Updated `get_rotated_real_vectors_for_batch()` docstring to:
- Remove references to "cache interaction" and "Option B (batch-indexed pixel cache)"
- Clarify that PyTorch computes **fresh rotations for ALL φ steps, including φ=0**
- Add explicit note that C-code φ carryover bug is NOT reproduced
- Retain C-code reference for transparency but mark the `if(phi != 0.0)` logic as a **BUG**
- Remove `phi_carryover_mode` from Args section

### 4. reports/.../parity_shim/.../diagnosis.md (Phase C3)

**File:** reports/2025-10-cli-flags/phase_l/parity_shim/20251008T023140Z/diagnosis.md
**Lines 1-3:** Added historical notice banner:
```
⚠️ HISTORICAL DOCUMENT (2025-12-14): The c-parity shim described in this analysis
was fully removed in commit b9db0a3 (2025-10-08) per plans/active/phi-carryover-removal/plan.md
Phase B. This file is retained for archival evidence only.
```

## Verification

Ran pytest collection to verify test suite remains intact:
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py
```

**Result:** 2 tests collected successfully in 0.79s
- `tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c`
- `tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_k_frac_phi0_matches_c`

No import errors or collection failures.

## Files Modified

1. `docs/bugs/verified_c_bugs.md` (lines 179-189)
2. `src/nanobrag_torch/models/crystal.py` (lines 1219-1256)
3. `reports/2025-10-cli-flags/phase_l/parity_shim/20251008T023140Z/diagnosis.md` (lines 1-3)

## Files Deleted

1. `tests/test_cli_scaling_parity.py` (entire file removed — shim-dependent test)

## Spec/Arch Alignment

- **Spec Reference:** specs/spec-a-core.md:211-214 (normative φ rotation pipeline, no carryover)
- **Bug Dossier:** docs/bugs/verified_c_bugs.md C-PARITY-001 (C-only defect, PyTorch uses spec)
- **Removal Plan:** plans/active/phi-carryover-removal/plan.md Phase C (C2/C3 complete)
- **Tolerance:** |Δk_frac| ≤ 1e-6, |Δb_y| ≤ 1e-6 (enforced in test_cli_scaling_phi0.py)

## Phase C Status

- [x] C1: Coverage audit complete (Attempt #179, 2025-10-08)
- [x] C2: docs/bugs ledger updated to mark shim removal complete (this loop)
- [x] C3: Tooling/docs sweep complete — test retired, docstrings scrubbed, diagnosis archived (this loop)

## Next Phase

**Phase D (Validation & Closure):**
- D1: Capture proof-of-removal bundle with spec-mode trace harness
- D2: Update fix_plan + archive phi-parity-shim plan
- D3: Supervisor handoff memo for remaining CLI-FLAGS-003 tasks (-nonoise/-pix0)

## Artifact Metadata

- **Timestamp:** 2025-10-08T20:01:54Z
- **Git Branch:** feature/spec-based-2
- **Engineer:** Ralph
- **Loop ID:** i=177
- **Mode:** Docs (no code execution beyond pytest --collect-only)
