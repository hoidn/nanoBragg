# Phase M5c Blocker Analysis

## Summary
The φ rotation + reciprocal recompute fix has been implemented correctly according to the C code logic (nanoBragg.c:3198-3210), but validation against the C trace reveals a fundamental conflict between two project goals:

1. **Goal A**: Match C code output for validation (CLI-FLAGS-003 objective)
2. **Goal B**: Be spec-compliant and NOT reproduce C bugs (CLAUDE.md principle, docs/bugs/verified_c_bugs.md:180-183)

## Implementation Status

### ✅ Completed
- Implemented conditional reciprocal vector recomputation matching C logic
- Real vectors remain unchanged after φ/mosaic rotations
- Reciprocal vectors recalculated from real vectors when `phi != 0.0 || mos_tic > 0`
- At φ=0 with mos_tic=0, base reciprocal vectors preserved (spec-compliant)
- All targeted tests pass (2/2 in test_cli_scaling_phi0.py)
- Core geometry tests pass (33/33)

### ❌ Blocker: C-PARITY-001 Conflict

**Observation**: PyTorch rot_b Y-component = 0.717320 Å matches C BASE b (0.71732 Å), but C TRACE shows rot_b Y-component = 0.671588 Å for pixel (685, 1039) at φ=0.

**Root Cause**: The C-PARITY-001 bug causes φ=0 to use stale ap/bp/cp values from the previous pixel's final φ step. Since the C trace was generated for pixel (685, 1039) (NOT the first pixel), it carries over state from pixel (684,1039) or similar.

**Spec-Compliant Behavior** (current PyTorch):
- At φ=0, apply identity rotation → use base vectors
- rot_b Y = 0.717320 Å (matches C base b = 0.71732 Å)

**C-Buggy Behavior** (actual C trace):
- At φ=0, skip rotation → reuse stale vectors from previous pixel
- rot_b Y = 0.671588 Å (from previous pixel's φ=0.09° state)

## Evidence

### C Code Base Vectors (After MOSFLM + Duality)
```
TRACE: After computing real-space vectors:
TRACE:   b = [-11.4987, 0.71732, -29.1132] |b| = 31.31
```

### C Trace at Pixel (685, 1039), φ=0
```
TRACE_C: rot_b_angstroms -11.4986968432508 0.671588233999813 -29.1143056268565
```

### PyTorch Trace (Spec-Compliant)
```
TRACE_PY: rot_b_angstroms -11.4986968432508 0.717320030990266 -29.1132147806318
```

### Comparison
- C base b Y-component: 0.71732 Å
- PyTorch rot_b Y (φ=0): 0.71732 Å ✅ MATCHES C base
- C rot_b Y (φ=0): 0.67159 Å ❌ DIVERGES due to carryover bug
- Delta: 0.71732 - 0.67159 = 0.0457 Å (6.4% error, causing 14.6% I_before_scaling deficit)

## Decision Required

**Option 1**: Accept spec-compliant divergence
- PyTorch remains correct per spec
- Document that C trace includes C-PARITY-001 bug effects
- Update validation to compare against spec-compliant C trace (regenerate with single-pixel run)
- **Pros**: Maintains code quality, spec compliance
- **Cons**: Cannot validate against existing C trace baseline

**Option 2**: Implement C-PARITY-001 bug emulation
- Add optional `--c-parity-mode` flag to reproduce bug for validation
- Default behavior remains spec-compliant
- **Pros**: Can validate against existing C trace
- **Cons**: Adds complexity, maintains bug for parity

**Option 3**: Regenerate C baseline
- Modify C code to fix C-PARITY-001 bug
- Regenerate golden trace from fixed C code
- **Pros**: Clean comparison, no bug preservation
- **Cons**: Requires C code modification, may affect other validations

## Recommendation

**Proceed with Option 1** with the following approach:

1. Update `lattice_hypotheses.md` to document that H4 (φ-Rotation Application Inconsistency) is RESOLVED in PyTorch - the 14.6% deficit was caused by the C-PARITY-001 bug, not a PyTorch error
2. Document that PyTorch is spec-compliant and C trace divergence at φ=0 is EXPECTED due to the documented C bug
3. Mark CLI-FLAGS-003 Phase M5 as COMPLETE with the caveat that exact C parity requires C bug emulation
4. Create follow-up task for Phase M6 to add optional `--c-parity-mode` flag if exact validation is still required

## Artifacts
- Fixed implementation: `src/nanobrag_torch/models/crystal.py:1204-1276`
- Fresh trace: `reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T235045Z/trace_py_scaling.log`
- Final intensity: 2.45946637686509e-07 (unchanged from baseline, as expected for spec-compliant path)
- Git SHA: e2bc0ed

## Next Actions
- Await supervisor decision on which option to pursue
- If Option 1: Update hypothesis docs and mark phase complete
- If Option 2: Implement carryover cache (Phase M2g infrastructure exists but disabled)
- If Option 3: Coordinate C code fix with upstream maintainers
