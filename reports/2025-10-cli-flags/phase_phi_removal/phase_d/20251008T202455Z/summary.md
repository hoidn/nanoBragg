# Phase D0 Complete: Trace Harness Refresh

**Date:** 2025-12-14
**Engineer:** Ralph (loop i=179)
**Plan Reference:** `plans/active/phi-carryover-removal/plan.md` Phase D0
**Commit:** (pending)

## Objective
Remove legacy `phi_carryover_mode` parameter handling from the scaling audit trace harness so it instantiates spec-only `CrystalConfig` per `specs/spec-a-core.md:204-240`.

## Changes Made

### File: `reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py`

1. **Removed CLI argument** (lines 51-52):
   - Deleted `--phi-mode` argument with choices `['spec', 'c-parity']`
   - Removed help text referencing "phi carryover mode"

2. **Removed CrystalConfig parameter** (line 167):
   - Deleted `phi_carryover_mode=args.phi_mode` kwarg
   - Updated comment to reference Phase D0 and spec compliance

3. **Removed config snapshot field** (line 204):
   - Deleted `'phi_carryover_mode': crystal_config.phi_carryover_mode` from snapshot

## Verification

### Test Collection
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py
```
**Result:** ✅ 2 tests collected successfully in 0.78s

### Code Sweep
```bash
rg --files-with-matches "phi_carryover" src tests scripts prompts docs
```
**Result:** ✅ Only `docs/fix_plan.md` contains historical references (expected)

## Exit Criteria

- [X] `--phi-mode` CLI argument removed
- [X] `phi_carryover_mode=args.phi_mode` kwarg removed
- [X] Config snapshot no longer logs removed parameter
- [X] Test collection (`pytest --collect-only`) succeeds
- [X] No `phi_carryover` references in `src/`, `tests/`, `scripts/`, `prompts/` (excluding `reports/` archives)

## Next Actions

Phase D1 tasks can now proceed:
- **D1a:** Run refreshed harness to generate spec-mode PyTorch trace
- **D1b:** Execute `pytest -v tests/test_cli_scaling_phi0.py`
- **D1c:** Confirm zero `phi_carryover` references in production code

## Artifacts
- Summary: `reports/2025-10-cli-flags/phase_phi_removal/phase_d/20251008T202455Z/summary.md`
- Commands: (captured in fix_plan Attempt log)
- Modified file: `reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py`
