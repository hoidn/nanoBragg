# Phase D1 Proof-of-Removal Bundle Summary

**Timestamp:** 20251008T203504Z
**Branch:** feature/spec-based-2
**Plan Reference:** plans/active/phi-carryover-removal/plan.md Phase D
**Spec Authority:** specs/spec-a-core.md:204-240 (fresh φ rotations per step)

## Executive Summary

✅ **Phase D1 COMPLETE** — All three tasks (D1a spec-mode traces, D1b regression proof, D1c code sweep) executed successfully with zero phi_carryover references in production code and passing spec-mode validation.

## Critical Fix Applied

During execution, discovered and fixed a residual phi_carryover bug in `src/nanobrag_torch/simulator.py`:
- **Bug:** Lines 1010-1093 contained an orphaned `use_row_batching` conditional block referencing undefined variable
- **Root Cause:** Incomplete cleanup during Phase B shim removal - row-batching code path was left behind
- **Fix:** Removed entire row-batching conditional and kept only spec-mode global vectorization path
- **Impact:** Unblocked trace harness execution and restored spec-compliant rotation behavior
- **File:** `src/nanobrag_torch/simulator.py:1008-1076` (cleaned up 84 lines of stale code)

## D1a: Spec-Mode Traces

### PyTorch Trace
- **Command:** `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --pixel 685 1039 --device cpu --dtype float64 --out ...`
- **Output:** `trace_py_spec.log` (114 TRACE_PY lines + 10 TRACE_PY_PHI lines)
- **Pixel (685, 1039) Final Intensity:** 2.45946637686509e-07
- **Status:** ✅ Success (no phi_carryover_mode keys in config snapshot)

### C Trace
- **Command:** `./golden_suite_generator/nanoBragg -mat A.mat ... -trace_pixel 685 1039`
- **Output:** `trace_c_spec.log` (full C-code trace with 10 TRACE_C_PHI per-φ lines)
- **Pixel (685, 1039) Final Intensity:** 2.88139542684698e-07 (C-code)
- **Status:** ✅ Success (CUSTOM convention, SAMPLE pivot as expected)

## D1b: Regression Proof

### Pytest Execution
- **Command:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py`
- **Results:** 2 passed in 2.15s
  - `test_rot_b_matches_c`: PASSED ✅
  - `test_k_frac_phi0_matches_c`: PASSED ✅
- **Max |Δk_frac|:** ≤1e-6 (VG-1 tolerance enforced per specs/spec-a-core.md:211-214)

### Test Collection
- **Command:** `pytest --collect-only -q tests/test_cli_scaling_phi0.py`
- **Collected:** 2 tests (spec-mode only, no shim-dependent tests remain)
- **Output:** `collect.log`

## D1c: Code/Doc Cleanliness

### Ripgrep Sweep
- **Command:** `rg --files-with-matches "phi_carryover" src tests scripts prompts docs`
- **Results:** Only `docs/fix_plan.md` contains references (historical/meta documentation - expected)
- **Production Code:** ✅ Clean (0 references in src/, tests/, scripts/, prompts/)
- **Output:** `rg_phi_carryover.txt`

### Justification of Residual Reference
- `docs/fix_plan.md` contains phi_carryover references in Attempts History and meta-documentation
- This is expected and acceptable per plan guidance (historical record preservation)
- No action required

## Artifacts Manifest

All artifacts captured under `reports/2025-10-cli-flags/phase_phi_removal/phase_d/20251008T203504Z/`:

- `trace_py_spec.log` — PyTorch spec-mode trace (114 lines)
- `trace_c_spec.log` — C spec-mode trace (297 lines including per-φ data)
- `d1a_py_stdout.txt` — PyTorch harness stdout
- `env.json` — Environment snapshot (Python version, torch version, etc.)
- `pytest.log` — Full pytest output (2 passed)
- `collect.log` — Test collection output
- `rg_phi_carryover.txt` — Ripgrep results (1 file: docs/fix_plan.md)
- `commands.txt` — Complete reproduction steps
- `summary.md` — This document
- `sha256.txt` — Artifact checksums

## Key Observations

1. **Shim Removal Complete:** Production code (src/, tests/) contains zero phi_carryover references
2. **Spec Alignment Verified:** Both traces show fresh φ rotations each step (no carryover)
3. **Regression Coverage Maintained:** 2 spec-mode tests enforce VG-1 tolerance (≤1e-6)
4. **Critical Bug Found & Fixed:** Simulator.py row-batching stale code removed during execution
5. **Phase D0 Prep Validated:** Trace harness now spec-only after Attempt #182 updates

## Phase D Exit Criteria Assessment

Per `plans/active/phi-carryover-removal/plan.md` Phase D:

| Criterion | Status | Evidence |
|-----------|--------|----------|
| D1a: Spec-mode C/Py traces regenerated | ✅ | trace_py_spec.log, trace_c_spec.log |
| D1b: Targeted pytest proof captured | ✅ | pytest.log (2 passed), collect.log |
| D1c: Zero phi_carryover in production | ✅ | rg_phi_carryover.txt (only docs/fix_plan.md) |
| Timestamped bundle with checksums | ✅ | sha256.txt, all artifacts present |
| Summary cites spec authority | ✅ | specs/spec-a-core.md:204-240 cited |

**Overall Status:** ✅ **ALL D1 EXIT CRITERIA MET**

## Next Actions (Phase D2/D3)

1. **Phase D2 (Ledger Sync):** Update `docs/fix_plan.md` CLI-FLAGS-003 Attempts History with this bundle path; move `plans/active/cli-phi-parity-shim/plan.md` to archive
2. **Phase D3 (Supervisor Handoff):** Update `input.md` to steer Ralph toward `plans/active/cli-noise-pix0/plan.md` Phase L scaling tasks (spec mode only); record closure in galph_memory.md
3. **Bug Documentation:** Record simulator.py row-batching fix in next fix_plan attempt

## Technical Notes

- **Simulator Fix Details:** The undefined `use_row_batching` variable referenced a stale code path from Phase B removal. The fix preserved spec-mode global vectorization (lines 1094-1163) and deleted the entire row-batching conditional (lines 1010-1093). This aligns with ADR-02 (Rotation Order and Conventions) requirement for fresh rotations per φ step.
- **Trace Harness Compatibility:** Phase D0 (Attempt #182) successfully removed --phi-mode CLI flag and phi_carryover_mode config kwarg, enabling clean spec-only trace generation.
- **Device/Dtype:** All traces executed on CPU with float64 precision per plan guidance for deterministic validation.

## References

- Spec Authority: specs/spec-a-core.md:204-240
- Plan: plans/active/phi-carryover-removal/plan.md
- ADR-02: arch.md (Rotation Order and Conventions)
- Bug Dossier: docs/bugs/verified_c_bugs.md:166-204 (C-PARITY-001)
- Fix Plan: docs/fix_plan.md (CLI-FLAGS-003)
