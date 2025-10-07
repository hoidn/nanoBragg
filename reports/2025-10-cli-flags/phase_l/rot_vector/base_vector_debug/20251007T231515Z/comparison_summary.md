# φ=0 Spec Baseline Evidence - CLI-FLAGS-003 L3k.3c.3

## Summary

**Status:** ✅ PASSED  
**Date:** 2025-10-07T23:15:15Z  
**Commit:** 4cb561b4e3e28184d2c8cb7a4662114389bfdf8d  
**Plan Reference:** plans/active/cli-noise-pix0/plan.md L3k.3c.3

## Verification Results

### Test Suite
- **Command:** `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py::TestPhiZeroParity -v`
- **Result:** 2 passed in 2.14s
- **Device:** CPU (torch 2.8.0+cu128)

### Baseline Values (Spec-Compliant φ=0)

| Metric | Expected Value | Measured Value | Tolerance | Status |
|--------|---------------|----------------|-----------|--------|
| rot_b[0,0,1] (Y component) | 0.7173197865 Å | 0.7173197865 Å | ≤1e-6 | ✅ PASS |
| k_frac (φ=0, pixel 685,1039) | 1.6756687164 | 1.6756687164 | ≤1e-6 | ✅ PASS |

## Interpretation

Per specs/spec-a-core.md:211-214, rotation by φ=0° should be the identity transformation,
yielding base lattice vectors unchanged. Both test cases confirm the PyTorch implementation
correctly implements this specification:

1. **test_rot_b_matches_c:** Validates that the rotated b-vector Y component at φ=0
   equals the base lattice vector, proving identity rotation behavior.

2. **test_k_frac_phi0_matches_c:** Validates that Miller indices calculated at φ=0
   use the base lattice vectors, confirming proper physics calculation.

## C-PARITY-001 Note

The C binary produces different values at φ_tic=0 due to stale vector carryover
(C-PARITY-001, documented in docs/bugs/verified_c_bugs.md:166-204):
- C rot_b_y: 0.6715882339 Å (carryover bug)
- C k_frac: -0.607256 (incorrect due to buggy vectors)

An opt-in C-parity shim will be added in Phase L3k.3c.4 to reproduce this behavior
for validation harnesses without compromising the spec-compliant default path.

## Artifacts

- `pytest_phi0.log` - Test execution output (2 passed)
- `metadata.txt` - Environment metadata (torch version, git SHA, device info)
- `sha256.txt` - Checksums for artifact integrity

## Next Actions

- ✅ L3k.3c.3 complete - spec baselines locked with ≤1e-6 deltas
- → L3k.3c.4 - Design opt-in C-parity shim for validation harnesses
- → L3k.3d - Resolve nb-compare ROI parity (VG-3/VG-4)
