# Phase A Baseline Inventory — φ Carryover Shim Surface Area

**Initiative:** Long-term Goal 1 — Remove φ carryover technical debt  
**Generated:** 2025-10-08T18:44:22Z  
**Git Head:** a1e776fd1a283a9912caa369dbcdb191487a45c7  
**Branch:** feature/spec-based-2

## Executive Summary

This document catalogues all references to the `phi_carryover_mode` shim introduced during CLI-FLAGS-003 to replicate C-PARITY-001 (documented in `docs/bugs/verified_c_bugs.md:166-204`). The shim allows opt-in emulation of the C-code bug where φ=0 pixels reuse the previous pixel's final φ rotation state instead of computing fresh rotations per spec (`specs/spec-a-core.md:204-240`).

**Key Finding:** The shim touches 4 production files, 2 test files, 3 active plans, and 40+ historical report artifacts. Removal will require coordinated deletion across code, tests, documentation, and tooling while preserving spec-mode regression coverage.

## Code Files (Production)

### src/nanobrag_torch/__main__.py
- **Line 859:** CLI argument passed to `CrystalConfig(phi_carryover_mode=args.phi_carryover_mode)`
- **Purpose:** CLI parser integration for `--phi-carryover-mode` flag
- **Removal Impact:** Delete argparse option, update help text
- **Dependencies:** Must ensure no callers expect the flag post-removal

### src/nanobrag_torch/config.py
- **Lines 154, 165-168:** Field definition and validation
- **Default:** `phi_carryover_mode: str = "spec"`
- **Validation:** Enforces `["spec", "c-parity"]` choices in `__post_init__`
- **Purpose:** Configuration dataclass field for mode selection
- **Removal Impact:** Delete field, remove validation logic
- **Dependencies:** Crystal model must not reference this field after removal

### src/nanobrag_torch/models/crystal.py
- **Line 1463:** Docstring parameter documentation
- **Line 1482-1484:** Conditional logic `if config.phi_carryover_mode == "c-parity" and self._phi_cache_initialized:`
- **Purpose:** Runtime gating of c-parity carryover path
- **Removal Impact:** Delete conditional branch, preserve vectorized spec-mode rotation pipeline
- **Dependencies:** `_phi_cache_initialized` and `apply_phi_carryover` method must be removed; ensure `_compute_physics_for_position` reverts to pure spec implementation

### src/nanobrag_torch/simulator.py
- **Reference:** Passes `config.phi_carryover_mode` implicitly via CrystalConfig
- **Purpose:** Config forwarding to Crystal model
- **Removal Impact:** None (indirect reference only)
- **Dependencies:** None

## Test Files

### tests/test_phi_carryover_mode.py
- **Purpose:** Dedicated test suite for c-parity mode behavior
- **Removal Impact:** **Delete entire file** in Phase B
- **Dependencies:** Fixtures/helpers may be used elsewhere; audit imports before deletion

### tests/test_cli_scaling_parity.py
- **Purpose:** Tests exercising both spec and c-parity modes for scaling validation
- **Removal Impact:** Keep file but prune c-parity test cases; retain spec-mode coverage
- **Dependencies:** Verify `test_cli_scaling_phi0.py` (baseline spec suite) provides equivalent coverage

## Plans

### plans/active/phi-carryover-removal/plan.md
- **Status:** This document — drives the removal effort
- **Removal Impact:** Archive to `plans/archive/` once Phases A-D complete

### plans/active/cli-noise-pix0/plan.md
- **References:** Delegates φ carryover work to removal plan
- **Removal Impact:** Update Next Actions to drop shim references; focus on `-nonoise`/`-pix0` deliverables

### plans/active/cli-phi-parity-shim/plan.md
- **Status:** Historical plan superseded by removal effort
- **Removal Impact:** Archive to `plans/archive/` in Phase D after docs sync

## Documentation

### docs/fix_plan.md
- **Entry:** CLI-FLAGS-003 ledger (lines 451-520 approx)
- **References:** φ carryover phases and parity tolerances
- **Removal Impact:** Rewrite Attempts History and Next Actions to reflect shim removal; link to this plan

### galph_memory.md
- **References:** Supervisor context about carryover shim decisions
- **Removal Impact:** Update memory to note shim is retired; reference C-PARITY-001 as C-only

### input.md
- **References:** Current Do Now for Phase A execution
- **Removal Impact:** Transient; next supervisor run will overwrite with new tasks

## Scripts & Tooling

### scripts/trace_harness.py (inferred)
- **Reference:** Likely supports `--phi-mode` options including c-parity
- **Removal Impact:** Drop c-parity mode; keep spec-only option
- **Dependencies:** Verify `reports/.../trace_harness.py` variants for similar cleanup

## Reports (Historical Evidence)

**40+ artifact bundles** under `reports/2025-10-cli-flags/phase_l/` reference the shim:

- **parity_shim/**: 10+ timestamped bundles with pytest logs, metrics, design docs
- **scaling_validation/**: 15+ bundles with carryover cache validation, gradcheck probes, diagnostics
- **rot_vector/**: Diagnosis/tolerance sync artifacts
- **phase_c2/**: Implementation checklists and summaries

**Removal Impact:** Keep as historical context; do not delete (archival evidence for future debugging)  
**Dependencies:** Reference these paths in Phase D closure memo to maintain traceability

## Spec & Bug References

### specs/spec-a-core.md:204-240
- **Content:** Normative φ rotation pipeline (fresh rotations each step)
- **Removal Rationale:** Shim deviates from spec; removal restores compliance

### docs/bugs/verified_c_bugs.md:166-204
- **Content:** C-PARITY-001 bug dossier
- **Post-Removal Status:** Amend to emphasize "C-only bug; PyTorch never reproduced post-removal"

## Baseline Test Status

**Collected:** 2025-10-08T18:44:22Z  
**Command:** `pytest --collect-only -q tests/test_cli_scaling_phi0.py`  
**Result:** 2 tests discovered

```
tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c
tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_k_frac_phi0_matches_c
```

**Status:** ✅ Spec-mode baseline suite remains stable  
**Validation:** These tests enforce spec-compliant φ rotation without c-parity shim

## Dependencies & Risks

### Vectorization Preservation
- **Requirement:** Removal must not reintroduce Python loops
- **Mitigation:** Review `crystal.py:1482-1484` deletion to ensure batched φ pipeline intact

### Device/Dtype Neutrality
- **Requirement:** CPU/CUDA smoke checks after removal
- **Mitigation:** Follow `docs/development/pytorch_runtime_checklist.md` §1.4

### Protected Assets
- **Compliance:** No deletion of files listed in `docs/index.md`
- **Verification:** Confirmed; shim files not protected

### Regression Coverage
- **Risk:** Deleting `test_phi_carryover_mode.py` may drop edge-case coverage
- **Mitigation:** Audit fixtures/assertions for migration to spec-mode tests before deletion

## Next Actions (Phase B)

1. Execute plan tasks B1-B3 (deprecate CLI flag, prune config/model plumbing, retire debug harness)
2. Run targeted pytest suite to confirm spec-mode behavior unchanged
3. Capture Phase B artifacts under `reports/.../phase_b/<timestamp>/`
4. Proceed to Phase C test realignment

## Artifact Metadata

**Directory:** `reports/2025-10-cli-flags/phase_phi_removal/phase_a/20251008T184422Z/`  
**Files:**
- `baseline_inventory.md` (this document)
- `collect.log` (pytest --collect-only output)
- `commands.txt` (reproduction commands)
- `env.json` (environment metadata)
- `phi_carryover_refs.txt` (raw grep results)

**SHA256 Checksums:** (to be generated)

## References

- Removal Plan: `plans/active/phi-carryover-removal/plan.md`
- C-Bug Dossier: `docs/bugs/verified_c_bugs.md:166-220`
- Spec Baseline: `specs/spec-a-core.md:204-260`
- CLI-FLAGS-003 Ledger: `docs/fix_plan.md:451-520`
- Testing Strategy: `docs/development/testing_strategy.md`
