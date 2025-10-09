# Option 1 Spec Compliance Bundle — Summary

**Date**: 2025-12-20
**Mode**: Documentation
**Scope**: CLI-FLAGS-003 Phase M5d (Option 1 decision capture)

## Purpose
This bundle documents the **Option 1 decision** for CLI-FLAGS-003 Phase M5: accept that PyTorch implements spec-compliant φ rotation behavior, and that exact C-code parity at φ=0 is intentionally NOT achieved due to the documented C-PARITY-001 bug.

## Key Points

### 1. Spec-Compliant Behavior (PyTorch)
Per `specs/spec-a-core.md:204-214`, the normative φ rotation pipeline requires:
> "Fresh rotation of real-space vectors from newly rotated reciprocal vectors at EACH φ step"

**PyTorch Implementation** (`src/nanobrag_torch/models/crystal.py:1194-1292`):
- Applies φ rotation to reciprocal vectors at each step
- Recalculates real vectors from rotated reciprocal vectors
- Uses these fresh real vectors for Miller index calculation
- **Result**: rot_b Y-component = 0.717320 Å (matches C base b = 0.71732 Å)

### 2. C-Code Bug (C-PARITY-001)
The C code has a documented pixel-carryover bug (`docs/bugs/verified_c_bugs.md:166-204`):
- At φ=0, C code reuses stale `ap/bp/cp` vectors from the previous pixel's final φ step
- This causes rot_b Y-component = 0.671588 Å (6.8% error)
- Error propagates: k_frac shifts by +3.0%, causing F_latt sign flip
- Final impact: I_before_scaling is 14.6% lower in PyTorch vs C

### 3. Decision Rationale
**Option 1 Adopted**: Accept spec-compliant divergence
- ✅ **Spec Compliance**: PyTorch matches normative specification exactly
- ✅ **Code Quality**: Maintains correct behavior, does not reproduce bugs
- ✅ **Documentation**: C bug is fully documented and understood
- ✅ **Testing**: All targeted tests pass (`tests/test_cli_scaling_phi0.py`: 2/2 PASSED)
- ⚠️ **Tradeoff**: Cannot achieve exact C parity at φ=0 without emulating the bug

**Deferred Option 2** (Phase M6): Optional `--c-parity-mode` flag
- Would emulate C-PARITY-001 bug for validation against legacy C traces
- Adds complexity without scientific benefit
- Can be revisited if exact C validation becomes critical

## Evidence

### Rotation Vectors Comparison (pixel 685, 1039; φ=0)
```
Component       C Base      PyTorch     C Trace     Delta (Py-C_trace)
-----------     -------     -------     -------     ------------------
rot_b_y (Å)     0.71732     0.71732     0.67159     +0.0457 (+6.8%)
```

### Impact Chain
```
Rotation error (6.8%)
  → k_frac shift (+3.0%: -0.589 → -0.607)
  → sincg zero-crossing (PyTorch: -0.858, C: +1.051)
  → F_latt sign flip
  → I_before_scaling deficit (-14.6%)
```

### Test Results
```bash
$ KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py
tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c PASSED
tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_k_frac_phi0_matches_c PASSED
============================== 2 passed in 2.05s ===============================
```

## Artifacts
- **Blocker Analysis** (with Option 1 addendum): `blocker_analysis.md`
- **Summary**: This document (`summary.md`)
- **Implementation**: `src/nanobrag_torch/models/crystal.py:1194-1292`
- **Tests**: `tests/test_cli_scaling_phi0.py` (validates spec-compliant behavior)
- **C Bug Dossier**: `docs/bugs/verified_c_bugs.md:166-204`
- **Git SHA**: e2bc0ed

## Next Actions (Phase M5e–M5g)

### M5e: Refresh validation scripts
- Update `scripts/validation/compare_scaling_traces.py` (or README) to flag expected φ=0 discrepancy
- Document that legacy C traces include C-PARITY-001 carryover effects
- Adjust automated checks to gate on spec-mode thresholds

### M5f: Targeted regression & CUDA smoke
- ✅ **CPU tests pass** (already confirmed above)
- **CUDA smoke** (if available): Run `pytest -v -m gpu_smoke tests/test_cli_scaling_phi0.py`

### M5g: Plan & ledger sync
- Update `plans/active/cli-noise-pix0/plan.md` (mark M5d–M5f as `[D]`)
- Update `docs/fix_plan.md` Attempts History with Option 1 acceptance
- Update `lattice_hypotheses.md` (close H4/H5 with spec-compliance rationale)

## References
- **Normative Spec**: `specs/spec-a-core.md:204-214` (φ rotation pipeline)
- **C Bug**: `docs/bugs/verified_c_bugs.md:166-204` (C-PARITY-001)
- **Architecture**: `arch.md` ADR-02 (Rotation Order and Conventions), Core Rules #12/#13
- **Plan**: `plans/active/cli-noise-pix0/plan.md` Phase M5
- **Fix Plan**: `docs/fix_plan.md` CLI-FLAGS-003 entry
