# Phase B Design Review: φ Carryover Shim Removal

**Date:** 2025-10-08T18:59:21Z
**Initiative:** CLI-FLAGS-003 Long-term Goal 1 — Retire φ carryover reproduction path
**Phase:** B0 (Design review & artifact prep)
**Status:** Design-only (no code changes in this loop)

## Executive Summary

This document outlines the planned removal of the `--phi-carryover-mode` CLI flag and all associated infrastructure that was added to reproduce the C-PARITY-001 bug (documented in `docs/bugs/verified_c_bugs.md:166-204`). The shim was implemented as an **opt-in** feature to enable validation against the C code's buggy behavior, but is not needed for spec-compliant operation.

**Key Principle:** PyTorch's default behavior (`--phi-carryover-mode spec`) is already spec-compliant and implements fresh φ rotations at each step per `specs/spec-a-core.md:211-214`. The removal will:
- Eliminate technical debt
- Simplify the codebase
- Preserve all spec-compliant functionality
- Maintain vectorization and gradient flow

## Normative References

### Spec Requirements
- **`specs/spec-a-core.md:211-214`** — Authoritative φ rotation pipeline:
  > "φ step: φ = φ0 + (step index)·phistep; rotate the reference cell (a0,b0,c0) about u by φ to get (ap,bp,cp)."

  This requires **fresh rotations each φ step**, not carryover from previous pixels.

### Bug Documentation
- **`docs/bugs/verified_c_bugs.md:166-204`** — C-PARITY-001 bug dossier:
  > "Inside the φ loop, the rotated vectors `ap/bp/cp` are only updated when `phi != 0.0`; otherwise, they retain the previous state (often from the prior pixel's final φ step)."

  **Critical:** This is a **C-only bug**. PyTorch must not preserve this behavior post-removal.

### Plan Context
- **`plans/active/phi-carryover-removal/plan.md`** — This removal plan (phases A-E)
- **`plans/active/cli-phi-parity-shim/plan.md`** — Original shim implementation plan (to be archived)
- **`plans/active/cli-noise-pix0/plan.md`** — Parent CLI-FLAGS-003 plan (needs reprioritization)

## Impacted Files Analysis

### Production Code (4 files to modify)

#### 1. `src/nanobrag_torch/__main__.py`
**Lines:** 377-380, 859
**Changes:**
- Remove `--phi-carryover-mode` argument parser definition
- Remove help text explaining the mode
- Remove `phi_carryover_mode=args.phi_carryover_mode` assignment to CrystalConfig

**Dependencies:** CrystalConfig must drop this parameter first (see #2)

#### 2. `src/nanobrag_torch/config.py`
**Lines:** 154, 165-168
**Changes:**
- Remove `phi_carryover_mode: str = "spec"` field from CrystalConfig
- Remove validation logic in `__post_init__` that checks mode values

**Critical:** This is a dataclass field removal. All callers must be updated first.

#### 3. `src/nanobrag_torch/models/crystal.py`
**Lines:** 245-248, 385-388, 1482-1487
**Changes:**
- Delete `apply_phi_carryover()` method (lines 245-388 approximately)
- Remove `_phi_cache_initialized` flag and related cache tensors
- Remove `initialize_phi_cache()` method
- Remove conditional carryover application in `get_rotated_vectors_per_pixel()`
- **Preserve:** All spec-compliant rotation logic (default path)

**Gradient Flow:** The existing spec-mode path already maintains gradient flow correctly (verified in Phase L). No changes to differentiability.

**Vectorization:** The existing spec-mode path is already fully vectorized. No risk of re-introducing Python loops.

#### 4. `src/nanobrag_torch/simulator.py`
**Lines:** 767
**Changes:**
- Remove conditional check `if self.crystal.config.phi_carryover_mode == "c-parity":`
- Remove cache initialization call
- Remove `use_row_batching` branching logic
- **Preserve:** Global vectorization path (already the default for spec mode)

### Test Files (2 files to modify/delete)

#### 5. `tests/test_phi_carryover_mode.py`
**Action:** **DELETE** (entire file, ~200 lines)
**Rationale:** This file exclusively tests the c-parity mode CLI flag wiring. With the shim gone, these tests have no purpose.

**Migration Assessment:** No assertions need migration. The file tests:
- CLI flag parsing (no longer exists)
- Config validation (no longer exists)
- Cache initialization (no longer exists)
- Parity thresholds (c-parity mode specific)

#### 6. `tests/test_cli_scaling_phi0.py`
**Action:** **KEEP** (already tests spec-compliant behavior)
**Current Coverage:** 2 tests (`test_rot_b_matches_c`, `test_k_frac_phi0_matches_c`)
**Changes:** None required — these tests validate **spec mode** (the behavior we're keeping)

**Evidence:** Pytest collection confirms these tests use spec-compliant assertions:
```
tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c
tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_k_frac_phi0_matches_c
```

### Documentation Files (5+ files to update)

#### 7. `README_PYTORCH.md`
**Action:** Remove references to `--phi-carryover-mode` flag (if any)
**Search:** Grep for `phi-carryover-mode` in user-facing docs

#### 8. `docs/bugs/verified_c_bugs.md`
**Lines:** ~180-190 (PyTorch Parity Shim section)
**Action:** Update C-PARITY-001 entry to clarify:
- "PyTorch **no longer provides** a reproduction mode"
- "This bug is **C-only**; PyTorch implements spec-compliant behavior by default"
- Add removal date and this design review reference

#### 9. `prompts/supervisor.md`
**Action:** Remove any references to c-parity mode or carryover shim in Do Now templates

#### 10. `plans/active/cli-noise-pix0/plan.md`
**Action:** Update Next Actions to remove carryover-related tasks and point to this removal plan

#### 11. `plans/active/cli-phi-parity-shim/plan.md`
**Action:** Mark all phases complete and prepare for archival to `plans/archive/`

### Reports & Artifacts (50+ files, archive-only)

**Action:** No changes needed. Historical artifacts remain for traceability.
**Examples:**
- `reports/2025-10-cli-flags/phase_l/parity_shim/*` — Implementation evidence
- `reports/2025-10-cli-flags/phase_l/rot_vector/*` — Base vector debugging
- `reports/2025-10-cli-flags/phase_phi_removal/phase_a/*` — Baseline inventory

## Validation Plan

### Phase B4: Targeted Regression Sweep

**Pre-removal baseline:**
```bash
pytest --collect-only -q tests/test_cli_scaling_phi0.py
# Expected: 2 tests collected successfully
```

**Post-removal validation:**
```bash
# CPU validation
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py

# GPU validation (if available)
KMP_DUPLICATE_LIB_OK=TRUE CUDA_VISIBLE_DEVICES=0 pytest -v tests/test_cli_scaling_phi0.py
```

**Success Criteria:**
- Both tests pass (correlation/tolerance thresholds unchanged)
- No import errors or collection failures
- Gradient flow preserved (existing gradcheck tests pass)
- Vectorization maintained (no performance regression)

### Acceptance Gates

**MUST PASS before marking Phase B complete:**
1. ✅ `pytest --collect-only -q` succeeds (imports clean)
2. ✅ `tests/test_cli_scaling_phi0.py` passes on CPU
3. ✅ (Optional) GPU smoke test if CUDA available
4. ✅ Full test suite passes: `pytest -v tests/`
5. ✅ No references to `phi_carryover_mode` in production code (grep verification)

## Risk Assessment

### Low Risk Items ✅
- **Spec compliance:** Default behavior is already correct
- **Vectorization:** No changes to spec-mode path (pure deletion)
- **Gradient flow:** No changes to differentiable paths
- **Test coverage:** `test_cli_scaling_phi0.py` validates the kept behavior

### Medium Risk Items ⚠️
- **Documentation drift:** Must update all references to avoid confusion
- **Plan synchronization:** Multiple plans reference the shim (need coordinated updates)

### Mitigations
- This design review captures all touchpoints
- Phase C focuses exclusively on doc/plan updates
- Artifacts under `reports/.../phase_b/` provide traceability

## Removal Order (Dependencies)

**Phase B1-B3 execution sequence:**

1. **B1: CLI surfaces** — Remove `--phi-carryover-mode` from argument parser
2. **B2: Config/model plumbing** — Remove CrystalConfig field, Crystal methods, Simulator branching
3. **B3: Tests/tooling** — Delete `test_phi_carryover_mode.py`, update validation scripts

**Critical Path:**
- B1 must precede B2 (config field removal breaks CLI wiring)
- B2 must precede B3 (test deletion requires clean imports)

## Protected Assets Compliance

**Per `docs/index.md` Protected Assets Rule:**
- ✅ No deletions of index-referenced files planned
- ✅ `loop.sh`, `supervisor.sh`, `input.md` remain untouched
- ✅ All spec files preserved

## Spec vs Implementation Alignment

**Post-removal state:**
- ✅ PyTorch behavior matches `specs/spec-a-core.md:211-214` (fresh φ rotations)
- ✅ C-PARITY-001 documented as C-only bug (PyTorch does not reproduce)
- ✅ No divergence between spec and implementation

## Next Steps (Phase B1-B3)

**B1: Deprecate CLI surfaces**
- Files: `src/nanobrag_torch/__main__.py`, `README_PYTORCH.md`
- Deliverable: CLI parser no longer exposes `--phi-carryover-mode`

**B2: Prune config/model plumbing**
- Files: `src/nanobrag_torch/config.py`, `models/crystal.py`, `simulator.py`
- Deliverable: No `phi_carryover_mode` parameters or branching logic

**B3: Retire shim tooling/tests**
- Files: `tests/test_phi_carryover_mode.py` (delete)
- Deliverable: Only spec-compliant tests remain

**B4: Targeted regression sweep**
- Commands: `pytest -v tests/test_cli_scaling_phi0.py` (CPU + GPU)
- Deliverable: Pass logs captured in Phase B artifacts

**B5: Ledger & plan sync**
- Files: `docs/fix_plan.md`, `plans/active/cli-noise-pix0/plan.md`
- Deliverable: Attempt entry logged, Next Actions updated

## Artifact Manifest

**This design bundle includes:**
1. ✅ `design_review.md` (this file)
2. ✅ `collect.log` (pytest collection baseline)
3. ⏳ `commands.txt` (to be added: shell history)
4. ⏳ `env.json` (to be added: git SHA + Python version)

**Storage:** `reports/2025-10-cli-flags/phase_phi_removal/phase_b/20251008T185921Z/`

## References

- Plan: `plans/active/phi-carryover-removal/plan.md` (Phase B0-B5)
- Spec: `specs/spec-a-core.md:211-214` (normative φ rotation)
- Bug: `docs/bugs/verified_c_bugs.md:166-204` (C-PARITY-001 dossier)
- Tests: `docs/development/testing_strategy.md` (validation cadence)
- Evidence: `reports/2025-10-cli-flags/phase_l/parity_shim/` (shim implementation artifacts)

---

**Design Review Status:** ✅ Complete
**Next Phase:** B1 (CLI surfaces removal, to be executed by Ralph in follow-up loop)
