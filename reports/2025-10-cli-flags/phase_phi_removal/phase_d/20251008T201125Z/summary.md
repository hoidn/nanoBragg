# Phase D: φ-Carryover Removal Proof-of-Removal Bundle
**Status:** ❌ BLOCKED
**Date:** 2025-10-08T20:11:25Z
**Plan Reference:** `plans/active/phi-carryover-removal/plan.md` Phase D (rows D1a-D1c)

## Executive Summary

Phase D1a trace generation **blocked** by stale diagnostic harness. Production code successfully removed all `phi_carryover_mode` references (Phases B-C complete per Attempts #179-180), but the scaling audit trace harness (`reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py:167`) still passes the removed parameter to `CrystalConfig.__init__()`.

## Blocker Details

### Error Message
```
TypeError: CrystalConfig.__init__() got an unexpected keyword argument 'phi_carryover_mode'
```

### Location
`reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py:167`

### Code Snippet
```python
crystal_config = CrystalConfig(
    cell_a=cell_a,
    # ... other params ...
    phi_carryover_mode=args.phi_mode,  # ← STALE: parameter removed in shim cleanup
    **params['crystal']
)
```

### Root Cause Analysis

1. **Production Code:** ✅ Clean - All `phi_carryover_mode` references removed from `src/` per Phase C sweep (Attempt #180)
2. **Tests:** ✅ Clean - `tests/test_cli_scaling_parity.py` deleted; `tests/test_cli_scaling_phi0.py` uses spec-only path
3. **Diagnostic Harness:** ❌ Stale - `trace_harness.py` predates shim removal and still references legacy parameter

### Impact

Cannot capture Phase D1a evidence (spec-mode PyTorch trace) required for proof-of-removal bundle. Phase D tasks D1a-D1c remain blocked until harness is updated.

## Attempted Tasks

### D1a: Regenerate spec-mode traces
- **Status:** ❌ BLOCKED
- **Command:** (see `commands.txt`)
- **Exit Code:** Non-zero (TypeError exception)
- **Artifacts:**
  - `d1a_py_stdout.txt` (error traceback)
  - `commands.txt` (reproduction steps)

### D1b: Capture regression proof
- **Status:** ⏸️ PENDING (blocked by D1a)
- **Reason:** Cannot run pytest until trace harness compatible

### D1c: Confirm code/doc cleanliness
- **Status:** ⏸️ PENDING (blocked by D1a)
- **Reason:** Evidence bundle incomplete

## Recommended Fix

Update `trace_harness.py:157-169` to remove `phi_carryover_mode=args.phi_mode` line and any related CLI parsing for `--phi-mode`. The spec-only rotation path is now the canonical behavior (no mode selection needed).

**Minimal Diff:**
```diff
--- a/reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py
+++ b/reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py
@@ -164,7 +164,6 @@ def main():
         mosflm_a_star=torch.tensor(a_star, dtype=dtype, device=device),
         mosflm_b_star=torch.tensor(b_star, dtype=dtype, device=device),
         mosflm_c_star=torch.tensor(c_star, dtype=dtype, device=device),
-        phi_carryover_mode=args.phi_mode,  # Phase M1: route supervisor override
         **params['crystal']
     )
```

Also remove `--phi-mode` from argparse setup if present.

## Next Actions

1. **Supervisor handoff:** Report blocker via this summary.md
2. **Harness update:** Remove `phi_carryover_mode` from trace harness in next Ralph loop
3. **Phase D retry:** Re-execute D1a-D1c once harness updated
4. **Ledger sync:** Update fix_plan.md Attempt log with blocker details

## Artifact Manifest

```
reports/2025-10-cli-flags/phase_phi_removal/phase_d/20251008T201125Z/
├── summary.md           ← This file
├── commands.txt         ← Command log + blocker details
└── d1a_py_stdout.txt   ← Error traceback
```

## Exit Criteria (From Plan)

**Original:**
> Timestamped Phase D bundle contains real C/Py traces + targeted pytest proof with zero `phi_carryover_mode` references

**Current Status:** Bundle incomplete - tooling blocker prevents trace generation. Production code is clean, but infrastructure must catch up before evidence can be captured.
