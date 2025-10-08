# CLI-FLAGS-003 Phase L3k.3c.3: Spec Baseline Refresh

**Date:** 2025-10-07
**Loop:** Ralph #104
**Focus:** Verify φ=0 rotations remain spec-compliant before expanding parity shim

## Execution Summary

### Commands Run

**CPU Baseline Tests:**
```bash
env KMP_DUPLICATE_LIB_OK=TRUE pytest \
  tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c \
  tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_k_frac_phi0_matches_c \
  -v
```

**CUDA Tests:**
Not applicable - these tests hard-code `device = torch.device('cpu')` at line 61 of test_cli_scaling_phi0.py. CUDA device available on system but not used by these particular tests.

### Results

**CPU Tests: PASSED ✅**
- `test_rot_b_matches_c`: PASSED
- `test_k_frac_phi0_matches_c`: PASSED
- Duration: 2.13s
- Platform: Linux, Python 3.13.7, pytest-8.4.2

### Spec Compliance Confirmation

The tests verify that the default `phi_carryover_mode="spec"` behavior remains correct:

1. **test_rot_b_matches_c**: Confirms that reciprocal basis vector `b*` matches spec-mandated fresh rotations at φ=0 (no carryover from C-bug)
2. **test_k_frac_phi0_matches_c**: Validates fractional k-index calculations at φ=0 under spec mode

Both tests pass, confirming:
- Default code path enforces spec rotations (specs/spec-a-core.md:211)
- C-PARITY-001 bug remains documented as non-normative (docs/bugs/verified_c_bugs.md:166)
- No regression in spec baseline implementation (src/nanobrag_torch/models/crystal.py:1106)

### Artifacts

- CPU test log: `reports/2025-12-cli-flags/phase_l/spec_baseline_refresh/pytest_cpu.log`
- This summary: `reports/2025-12-cli-flags/phase_l/spec_baseline_refresh/summary.md`
- Commands record: `reports/2025-12-cli-flags/phase_l/spec_baseline_refresh/commands.txt`

### CUDA Status

CUDA device available (torch.cuda.is_available() = True), but tests hard-code CPU execution. These tests validate spec-compliant rotation math on CPU as primary purpose. GPU smoke testing not applicable to this validation loop.

### Next Steps

Per `input.md` and `plans/active/cli-phi-parity-shim/plan.md`:
- This documentation refresh satisfies VG-1 gate for Phase L3k.3c.3
- Phase C4 (parity shim per-φ trace deltas) can proceed once parity shim evidence is ready
- No code changes required in this loop (docs/evidence only)

### Compliance Notes

- Environment: `KMP_DUPLICATE_LIB_OK=TRUE` set per CLAUDE.md:120
- No modifications to spec files (maintained as normative)
- Protected assets (docs/index.md) honored - no deletions
- Test collection verified before execution
