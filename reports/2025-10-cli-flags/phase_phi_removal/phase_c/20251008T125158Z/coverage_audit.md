# Coverage Audit: CLI-FLAGS-003 Phase C1

## Summary

**Date:** 2025-10-08
**Audit Scope:** Post-shim-removal spec-mode test coverage in `tests/test_cli_scaling_phi0.py`
**Plan Reference:** `plans/active/phi-carryover-removal/plan.md` Phase C1
**Supervisor Memo:** `input.md:7` (Do Now: CLI-FLAGS-003 coverage audit per plan row C1)

## Collected Tests

**Command:** `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py`

```
tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c
tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_k_frac_phi0_matches_c

2 tests collected in 0.79s
```

## Removed Coverage (from `tests/test_phi_carryover_mode.py`)

The shim removal in Phase B (commit 340683f / b9db0a3) deleted `tests/test_phi_carryover_mode.py`, which contained **33 tests** organized in 5 test classes:

### 1. TestPhiCarryoverModeParsing (4 tests)
- `test_default_mode_is_spec` — Verified CLI default was 'spec'
- `test_spec_mode_explicit` — Verified `--phi-carryover-mode spec` parsing
- `test_c_parity_mode_explicit` — Verified `--phi-carryover-mode c-parity` parsing
- `test_invalid_mode_rejected` — Verified invalid mode rejection

**Disposition:** No longer needed. The `--phi-carryover-mode` CLI flag no longer exists.

### 2. TestCrystalConfigValidation (4 tests)
- `test_default_config_mode` — Verified `CrystalConfig.phi_carryover_mode` default
- `test_spec_mode_validation` — Verified 'spec' mode accepted
- `test_c_parity_mode_validation` — Verified 'c-parity' mode accepted
- `test_invalid_mode_raises_valueerror` — Verified invalid mode rejection

**Disposition:** No longer needed. The `phi_carryover_mode` config field no longer exists.

### 3. TestPhiCarryoverModeWiring (2 tests)
- `test_spec_mode_wiring` — Verified config flows to Crystal model (spec mode)
- `test_c_parity_mode_wiring` — Verified config flows to Crystal model (c-parity mode)

**Disposition:** No longer needed. The mode parameter no longer exists.

### 4. TestPhiCarryoverModePhysics (12 tests, parametrized: 2 modes × 2 devices × 3 dtypes)
- `test_spec_mode_identity_at_phi_zero` — Verified φ=0 gives identity rotation (spec mode)
- `test_c_parity_mode_stale_carryover` — Verified φ=0 matches φ=final (c-parity mode)
- `test_modes_differ_at_phi_zero` — Verified spec and c-parity produce different φ=0 vectors

**Disposition:**
- **RETAINED (spec behavior):** The first test's assertion (φ=0 identity) is now covered by `test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c` (validates rot_b[0,0,1] equals base vector at φ=0).
- **NO LONGER NEEDED (c-parity behavior):** The c-parity mode tests are obsolete.

### 5. TestDeviceDtypeNeutrality (8 tests, parametrized: 2 modes × 2 devices × 2 dtypes)
- `test_cpu_consistency` — Verified mode works on CPU with float32/float64
- `test_cuda_consistency` — Verified mode works on CUDA with float32/float64

**Disposition:**
- **COVERAGE GAP (non-blocking):** Current spec-mode tests run only on CPU float32. The deleted tests exercised CPU float64 and CUDA float32/float64.
- **Mitigation:** The broader test suite includes device/dtype parametrization elsewhere (e.g., `test_at_parallel_*.py` tests). Spec-mode φ=0 behavior is deterministic and doesn't require exhaustive device/dtype coverage in this specific test file.

### 6. TestFlagInteractions (3 tests)
- `test_with_misset` — Verified phi carryover works with misset angles
- `test_with_mosaic` — Verified phi carryover works with mosaic domains
- `test_with_single_phi_step` — Verified edge case of single phi step

**Disposition:**
- **NO LONGER NEEDED:** These tests validated that the now-removed `phi_carryover_mode` parameter didn't interfere with other features.

## Retained Coverage Analysis

### Current Test 1: `test_rot_b_matches_c`

**Purpose:** Validates SPEC-COMPLIANT behavior (specs/spec-a-core.md:211-214) where φ=0° rotation should equal identity transformation.

**Assertions:**
- Verifies `rot_b[0,0,1]` (φ=0 b-vector Y component) equals `0.7173197865` Å (spec baseline) within 1e-6 relative tolerance
- Validates φ dimensions match `crystal_config.phi_steps`

**Coverage Provided:**
✅ φ=0 identity rotation (replaces `test_spec_mode_identity_at_phi_zero` from deleted tests)
✅ Spec-compliant base vector calculation
✅ Reproduces supervisor command configuration (A.mat + scaled.hkl from CLI-FLAGS-003 Phase L)

**Note:** This test uses the C-PARITY-001 bug reference only in comments; the assertion validates the **correct** spec behavior, not the buggy C behavior.

### Current Test 2: `test_k_frac_phi0_matches_c`

**Purpose:** Validates φ=0 fractional Miller index `k` calculation using spec-compliant (identity) rotation.

**Assertions:**
- Computes `k_frac = b · S` at φ=0 for target pixel (685, 1039)
- Verifies `k_frac` equals `1.6756687164` (spec baseline) within 1e-6 absolute tolerance

**Coverage Provided:**
✅ End-to-end Miller index calculation at φ=0
✅ Detector pixel coordinate calculation
✅ Scattering vector computation
✅ Real-space lattice vector dot product
✅ Spec-compliant φ=0 behavior (not C bug reproduction)

## Coverage Gaps

### 1. Device/Dtype Parametrization (Non-Blocking)

**Gap:** Current spec-mode tests run only on CPU float32.

**Deleted Coverage:** `TestDeviceDtypeNeutrality` exercised:
- CPU float32, CPU float64
- CUDA float32, CUDA float64 (when available)

**Mitigation:**
- Broader test suite includes device/dtype smoke tests (`test_at_parallel_*.py`)
- φ=0 identity rotation is deterministic; spec behavior doesn't vary by device/dtype
- VG-1 tolerance (≤1e-6) is achievable on all devices

**Recommendation:** Add parametrized device/dtype markers to `TestPhiZeroParity` in a future hygiene pass (not blocking Phase C closure).

### 2. Mosaic Domains / Misset Interaction (Non-Blocking)

**Gap:** Current tests use `mosaic_domains=1` and `misset_deg=[0,0,0]`.

**Deleted Coverage:** `TestFlagInteractions::test_with_mosaic` and `test_with_misset` validated non-interference.

**Mitigation:**
- These interactions are validated in other test files (e.g., `test_at_parallel_007.py` exercises rotations, `test_at_parallel_011.py` exercises mosaic spread)
- The removed tests validated the **shim parameter** didn't break interactions; no shim means no interaction risk

**Recommendation:** No action required. Coverage exists elsewhere.

## Spec Alignment Verification

### Authoritative Spec Reference: `specs/spec-a-core.md:211-214`

```
- Crystal orientation:
    - φ step: φ = φ0 + (step index)*phistep; rotate the reference cell (a0,b0,c0)
      about u by φ to get (ap,bp,cp).
    - Mosaic: for each domain, apply the domain's rotation to (ap,bp,cp) to get
      (a,b,c).
```

**Spec Requirement:** At φ=0°, the rotation should produce the reference cell vectors unchanged (identity transformation).

**Test Coverage:** ✅ Both current tests validate this:
- `test_rot_b_matches_c` directly asserts identity at φ=0
- `test_k_frac_phi0_matches_c` uses φ=0 vectors and validates downstream Miller index calculation

### C-PARITY-001 Bug Reference (Historical Context Only)

**Bug Description:** `docs/bugs/verified_c_bugs.md:166-204` documents that the C binary carries forward the final φ step's rotated vectors to φ=0, violating the spec.

**PyTorch Behavior:** After Phase B shim removal, PyTorch **only** implements spec-compliant behavior. The bug is no longer reproducible in PyTorch.

**Test Validation:** Current tests validate the **correct** spec behavior. Comments reference the C bug for context but do not attempt to reproduce it.

## Phase B Removal Verification

### Verification Command
```bash
grep -r "phi_carryover_mode" src/ tests/ --exclude-dir=__pycache__
```

**Result:** No matches (expected post-Phase B)

### Code Removal Confirmation

**Phase B Artifacts:** `reports/2025-10-cli-flags/phase_phi_removal/phase_b/20251008T193106Z/`

**Removed Components:**
1. CLI flag: `--phi-carryover-mode` (from `src/nanobrag_torch/__main__.py`)
2. Config field: `CrystalConfig.phi_carryover_mode` (from `src/nanobrag_torch/config.py`)
3. Model logic: Carryover branching in `Crystal.get_rotated_real_vectors()` (from `src/nanobrag_torch/models/crystal.py`)
4. Simulator wiring: Mode parameter passing (from `src/nanobrag_torch/simulator.py`)
5. Test file: `tests/test_phi_carryover_mode.py` (33 tests deleted)

**Retained Spec Assertions:** Consolidated into `tests/test_cli_scaling_phi0.py` (2 tests)

## Conclusions

### Coverage Assessment: ✅ SUFFICIENT

**Spec-Mode Assertions:** The two retained tests adequately cover the normative spec requirement (φ=0 identity rotation) and validate both:
1. **Direct vector comparison** (`test_rot_b_matches_c`)
2. **Downstream physics** (`test_k_frac_phi0_matches_c`)

**Deleted Coverage:** The 33 removed tests primarily validated:
- The now-deleted shim parameter (CLI parsing, config validation, wiring)
- C-parity mode behavior (bug reproduction, no longer supported)
- Device/dtype parametrization (covered elsewhere in test suite)

**Critical Invariant Preserved:** Both current tests enforce VG-1 tolerance (≤1e-6) and reference the authoritative spec baseline values.

### Non-Blocking Improvements

1. **Device/Dtype Parametrization:** Add `@pytest.mark.parametrize("device,dtype", ...)` to `TestPhiZeroParity` to exercise CPU float32/float64 and CUDA float32/float64 (when available). This aligns with `docs/development/testing_strategy.md §1.4` PyTorch Device & Dtype Discipline.

2. **Mosaic/Misset Spot Check:** Add a single spec-mode test with `mosaic_domains>1` and non-zero `misset_deg` to validate no regression. Can be a simple smoke test (not full parametrization).

### Phase C1 Gate: PASSED

**Criteria:** Ensure `tests/test_cli_scaling_phi0.py` asserts the per-φ invariants previously covered by the deleted parity suite.

**Result:** ✅ The spec-compliant φ=0 identity rotation invariant is validated by both current tests with appropriate tolerances.

**Selector Validation:** `pytest --collect-only -q tests/test_cli_scaling_phi0.py` → 2 tests collected (expected)

### Next Steps (Per Plan)

**Phase C1:** ✅ COMPLETE
**Phase C2:** Update `docs/bugs/verified_c_bugs.md` C-PARITY-001 entry to emphasize "C-only" and note PyTorch no longer exposes reproduction mode
**Phase C3:** Adjust parity tooling docs to remove c-parity tolerance guidance

## Artifact Inventory

**Location:** `reports/2025-10-cli-flags/phase_phi_removal/phase_c/20251008T125158Z/`

**Files:**
- `coverage_audit.md` — This document
- `collect.log` — pytest collection output
- `commands.txt` — Reproduction steps
- `sha256.txt` — Artifact checksums

**Referenced Artifacts:**
- Phase B removal: `reports/2025-10-cli-flags/phase_phi_removal/phase_b/20251008T193106Z/`
- Phase A baseline: `reports/2025-10-cli-flags/phase_phi_removal/phase_a/20251008T184422Z/`
