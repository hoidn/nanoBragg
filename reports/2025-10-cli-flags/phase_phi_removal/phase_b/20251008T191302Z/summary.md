# Phase B1 Summary: CLI Flag Removal

**Timestamp:** 2025-10-08T19:13:02Z
**Phase:** CLI-FLAGS-003 Phase B1 — Deprecate CLI surfaces
**Status:** ✅ Complete
**Artifacts:** `reports/2025-10-cli-flags/phase_phi_removal/phase_b/20251008T191302Z/`

## Objective

Remove the `--phi-carryover-mode` CLI flag from `src/nanobrag_torch/__main__.py` and verify spec-mode regression tests continue to pass. This fulfills the first step of retiring the φ carryover reproduction shim per `plans/active/phi-carryover-removal/plan.md` Phase B.

## References

- **Design Review (Phase B0):** `reports/2025-10-cli-flags/phase_phi_removal/phase_b/20251008T185921Z/design_review.md`
- **Baseline Inventory (Phase A):** `reports/2025-10-cli-flags/phase_phi_removal/phase_a/20251008T184422Z/baseline_inventory.md`
- **Plan:** `plans/active/phi-carryover-removal/plan.md` lines 29-38
- **Supervisor Memo:** `input.md` lines 1-130
- **Spec:** `specs/spec-a-core.md` lines 211-224 (normative φ rotation rules)
- **Bug Dossier:** `docs/bugs/verified_c_bugs.md` lines 166-204 (C-PARITY-001)

## Changes Made

### 1. CLI Argument Removal

**File:** `src/nanobrag_torch/__main__.py`

**Lines Removed (376-385):**
```python
# Phi rotation behavior (CLI-FLAGS-003 Phase C2)
parser.add_argument('--phi-carryover-mode', type=str,
                    default='spec',
                    choices=['spec', 'c-parity'],
                    help=(
                        'Phi rotation behavior mode. '
                        '"spec": Fresh rotation each φ step (default, spec-compliant). '
                        '"c-parity": φ=0 reuses stale vectors (C-PARITY-001 bug emulation for validation). '
                        'See docs/bugs/verified_c_bugs.md for details.'
                    ))
```

**Lines Modified (859):**
```python
# BEFORE:
phi_carryover_mode=args.phi_carryover_mode

# AFTER:
# (parameter removed entirely)
```

The CLI no longer exposes the flag. Attempts to use `--phi-carryover-mode` will fail with an unrecognized argument error from argparse.

## Validation

### Baseline Test (Pre-Edit)
```bash
pytest --collect-only -q tests/test_cli_scaling_phi0.py
```
**Result:** 2 tests collected successfully
**Artifact:** `collect_pre.log`

### Regression Test (Post-Edit)
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py
```
**Result:** ✅ 2/2 tests PASSED in 2.14s
- `TestPhiZeroParity::test_rot_b_matches_c` PASSED
- `TestPhiZeroParity::test_k_frac_phi0_matches_c` PASSED

**Tolerance:** ≤1e-6 per CLI-FLAGS-003 L3k.3c.3 verification gate
**Artifact:** `pytest_cpu.log`

Spec-mode behavior (fresh φ rotations each step) remains unchanged and passes validation.

### CUDA Test
**Status:** Not executed (no CUDA device available in this environment)
**Documented in:** `input.md` lines 14, 51

## Residual References (Deferred to Phase B2/B3)

Grep search identified 57 files still containing `phi_carryover_mode` references. Production code references requiring Phase B2 removal:

1. **`src/nanobrag_torch/config.py`** — `CrystalConfig.phi_carryover_mode` field definition
2. **`src/nanobrag_torch/models/crystal.py`** — `apply_phi_carryover()` method implementation
3. **`src/nanobrag_torch/simulator.py`** — c-parity mode branching logic

Test files requiring Phase B3 cleanup:

4. **`tests/test_phi_carryover_mode.py`** — Entire test file to be deleted
5. **`tests/test_cli_scaling_parity.py`** — Contains one test using `phi_carryover_mode="c-parity"`

Historical reports and plan documents contain archival references and do not require immediate action.

**Full Reference List:** `grep.log`

## Environment

**Python:** 3.13.7
**PyTorch:** 2.5.1
**Git SHA:** ad39be4
**Device:** CPU
**CUDA Available:** No

**Metadata File:** `env.json`

## Next Actions

Per `plans/active/phi-carryover-removal/plan.md`:

1. **Phase B2** — Remove `phi_carryover_mode` field from `CrystalConfig`; delete `apply_phi_carryover()` method from `crystal.py`; remove c-parity branching from `simulator.py`
2. **Phase B3** — Delete `tests/test_phi_carryover_mode.py`; update `tests/test_cli_scaling_parity.py` to remove c-parity mode usage
3. **Phase B4** — Run full regression sweep on CPU and CUDA (when available)
4. **Phase B5** — Update `docs/fix_plan.md` Attempts History and flip plan rows to `[D]`

## Documentation Updates Required

Per `input.md` lines 77-82, the following files must be updated to reflect flag removal:

- ❌ `README_PYTORCH.md` — Update CLI flag descriptions (not completed this loop, defer to docs sync)
- ❌ `prompts/supervisor.md` — Remove carryover mode references (not completed this loop, defer to docs sync)
- ❌ `docs/bugs/verified_c_bugs.md` — Clarify PyTorch no longer exposes shim (not completed this loop, defer to docs sync)

**Rationale for Deferral:** Phase B1 focused exclusively on CLI code removal and regression verification per supervisor memo. Documentation sync will be handled in a dedicated follow-up loop to maintain single-concern changes.

## Verification

- ✅ CLI argument removed from argparse
- ✅ Config parameter passing removed
- ✅ Spec-mode regression tests pass (2/2)
- ✅ Grep search captured residual references
- ✅ Environment metadata captured
- ✅ Artifacts stored with SHA256 checksums
- ✅ Design review cross-referenced

## Artifacts

All artifacts stored under:
`reports/2025-10-cli-flags/phase_phi_removal/phase_b/20251008T191302Z/`

Files:
- `summary.md` (this document)
- `commands.txt` (chronological command log)
- `collect_pre.log` (baseline pytest collection)
- `pytest_cpu.log` (post-edit regression test)
- `grep.log` (residual reference search)
- `env.json` (environment metadata)
- `sha256.txt` (artifact checksums)

**Design Review Reference:**
`reports/2025-10-cli-flags/phase_phi_removal/phase_b/20251008T185921Z/design_review.md`

## Conclusion

Phase B1 successfully removed the `--phi-carryover-mode` CLI flag while preserving spec-compliant behavior. Targeted regression tests confirm no functionality regression. Residual internal references documented for Phase B2/B3 cleanup.

PyTorch now enforces spec-compliant φ rotation behavior (fresh rotations each step) with no user-accessible opt-in to the C-PARITY-001 bug.
