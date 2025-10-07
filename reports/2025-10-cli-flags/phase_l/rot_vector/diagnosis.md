# CLI-FLAGS-003 Phase L Diagnosis Log

**Status**: Active investigation of φ rotation parity discrepancies
**Current Phase**: L3k (φ=0 Carryover Evidence Collection)
**Last Updated**: 2025-10-07 (ralph i=107)

---

## 2025-10-07: Phase L3k.3c.2 — φ=0 Carryover Evidence Collection

**Summary**: Captured PyTorch φ=0 state probe results. **BLOCKED** awaiting C trace generation (Phase L3k.3b) to compute deltas and complete carryover story.

### Probe Results

From `reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/rot_vector_state_probe.log`:

```
b_base_y 0.7173197865486145
rot_b_phi0_y 0.7173197865486145
rot_b_phi1_y 0.7122385501861572
k_frac_placeholder 980.31396484375
```

### Key Observations

1. **φ=0 Behavior**: `rot_b_phi0_y == b_base_y` (0.7173197865486145 Å)
   - At φ=0, the rotated vector matches the base vector exactly
   - This is the expected behavior (rotation by 0° is identity)
   - No carryover issue detected at the first φ step

2. **φ=0.01° Behavior**: `rot_b_phi1_y = 0.7122385501861572`
   - Small deviation (-5.08e-3 Å) from base vector
   - This is expected for a small rotation
   - Δb_y from φ₀ to φ₁ = -5.08e-3 Å

3. **Vector Magnitude**: |rot_b[0,0]|² = 980.31396484375 Å²
   - Magnitude ≈ 31.31 Å (sqrt of 980.31)
   - Consistent with cell parameter b=100 Å and (36,47,29) N_cells configuration

### Blocking Issue

**Missing C Reference Data**: The expected C trace file `reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/202510070839/c_trace_phi_202510070839.log` does not exist.

**Per input.md "If Blocked" guidance** (lines 8-9):
- Documented the gap in this diagnosis.md
- Captured stub entry in commands.txt explaining missing assets
- Updated sha256.txt with captured artifacts
- Emitted placeholder `delta_metrics.json` noting the missing data
- Proceeding to next action per Phase L3k sequence

### Artifacts

All evidence stored in `reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/`:

- **rot_vector_state_probe.log** — PyTorch probe output (SHA256: ef946e94...)
- **delta_metrics.json** — Status: BLOCKED, awaiting C trace
- **phi0_state_analysis.md** — Detailed analysis with interpretation
- **commands.txt** — Reproduction commands for provenance
- **sha256.txt** — Cryptographic hashes for verification

### Proposed Vectorized Remediation

Based on the φ rotation fix implemented in Attempt #97 (src/nanobrag_torch/models/crystal.py:1008-1035):

**Current Implementation** (Post-Fix):
1. Rotate real vectors (`a`, `b`, `c`) by φ using spindle axis
2. Recompute reciprocal vectors from rotated real vectors via cross products and V_actual

**Proposed Enhancement for φ=0 Carryover** (if needed after C trace comparison):
- Compute all rotated vectors in batched form
- Retain lagged copy via `torch.roll`
- Use φ==0 mask to swap in prior step
- Preserve gradients via masked operations (no Python loops)
- Maintain performance via batched tensor operations

**Critical Constraint**: Any fix MUST preserve the C semantics identified in `golden_suite_generator/nanoBragg.c:3040-3095` where:
- At φ≠0: Real vectors are rotated, reciprocal vectors implicit
- At φ=0: If `if(phi!=0.0)` guard exists, vectors may be stale from previous iteration

### References

- input.md lines 1-114 — Phase L3k.3c.2 steering memo
- golden_suite_generator/nanoBragg.c:3040 — φ rotation loop with `if(phi!=0.0)` guard
- src/nanobrag_torch/models/crystal.py:1057-1084 — Current Python loop (interim hack)
- docs/architecture/pytorch_design.md#vectorization-strategy — Batched flow requirements
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251122/diagnosis.md — Prior per-φ evidence

### Next Steps

**Immediate** (Phase L3k.3b per input.md lines 10-14):
1. Instrument `golden_suite_generator/nanoBragg.c` to emit `TRACE_C_PHI` for all φ steps
2. Rebuild C binary: `make -C golden_suite_generator`
3. Run with supervisor command to generate C trace
4. Execute `scripts/compare_per_phi_traces.py` to compute deltas
5. Update this diagnosis.md with computed Δb_y and Δk_frac values

**After C Trace Available** (Phase L3k.3c.3+):
- If deltas ≈ 0: Close φ=0 carryover investigation, proceed to Phase L3k.4 normalization closure
- If deltas ≠ 0: Implement vectorized fix per proposed remediation, re-verify with VG-1 gates

**Long-Term** (Phase L4):
- Regenerate per-φ traces + nb-compare metrics once VG-1 tolerances pass
- Rerun supervisor command to validate end-to-end parity
- Update fix_checklist.md and close CLI-FLAGS-003

### Risks/Assumptions

- **Assumption**: The φ=0 case returning base vector unchanged is correct behavior
- **Risk**: C trace may reveal unexpected φ=0 handling (e.g., stale values from previous iteration)
- **Mitigation**: Phase L3k.3b C trace generation will validate or refute this assumption
- **Watch**: Ensure gradients remain intact if vectorized mask fix is needed
- **Watch**: Confirm with gradcheck after any implementation changes

---

## Previous Phases

(Prior diagnosis entries preserved below for continuity — see analysis.md for detailed investigations)

### Phase L3j (Attempt #94): Rotation Fix Implementation

**Result**: Successfully implemented φ rotation fix per CLAUDE Rule #13
- Removed independent reciprocal vector rotation (lines 1014-1022 deleted)
- Added reciprocal recomputation from rotated real vectors (cross products + V_actual)
- C-code reference added per CLAUDE Rule #11 (nanoBragg.c:3056-3058)
- All targeted tests pass (57/57 crystal/geometry tests PASSED)
- Test collection succeeds (653 tests)

### Phase L3k.1 (Attempt #96): Implementation Memo

**Result**: Documentation complete for Phase L3k implementation strategy
- Created mosflm_matrix_correction.md Phase L3k memo section
- Created fix_checklist.md with 5-gate verification matrix
- Documented C semantics reference and proposed fix
- Identified thresholds (b_Y ≤1e-6, k_frac ≤1e-6, correlation ≥0.9995, sum_ratio 0.99–1.01)
- Mode: Docs → deferred implementation to next code-focused loop

### Phase L3k.2 (Attempt #97): φ Rotation Fix Applied

**Result**: SUCCESS — Implementation complete
- Crystal.py modified: Step 1 rotates only real vectors; Step 2 recomputes reciprocal
- C-code docstring added (nanoBragg.c:3056-3058)
- Targeted test passes: test_f_latt_square_matches_c PASSED
- Full test sweep: 57 crystal/geometry tests PASSED
- Collection check: 653 tests collected successfully

---

## Exit Criteria for CLI-FLAGS-003

- [ ] Phase L3k.3 gates (VG-1 through VG-5) all pass with documented metrics
- [ ] Per-φ traces show correlation ≥0.9995 and sum_ratio 0.99–1.01
- [ ] nb-compare ROI anomaly resolved (C sum ≠ 0)
- [ ] Supervisor command reproduces with parity metrics meeting thresholds
- [ ] fix_checklist.md fully green
- [ ] All artifacts archived with provenance (commands.txt, sha256.txt, metrics.json)
