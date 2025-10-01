# Plan: AT-TIER2-GRADCHECK Completion

**Status:** Active (new 2025-10-15)
**Priority:** High — spec compliance blocker (testing_strategy §4.1)
**Related fix_plan item:** `[AT-TIER2-GRADCHECK]` — docs/fix_plan.md
**Created:** 2025-10-15 by galph

## Context
- Initiative: Ensure differentiability guarantees (long-term goal: autodiff-based refinement showcase).
- Phase Goal: Close the remaining Tier-2 gradcheck gaps called out in testing_strategy.md §4.1: `misset_rot_x`, beam `lambda_A`, and `fluence`.
- Current State: Commit 0e3054c implemented gradchecks for unit-cell lengths/angles and detector distance/beam_center_f. Commit d45a0f3 introduced `NANOBRAGG_DISABLE_COMPILE` to work around torch.compile bugs. However, no coverage exists yet for misset rotations or beam parameters, and the harness still emits contradictory compile-mode toggles (`NB_DISABLE_COMPILE` vs `NANOBRAGG_DISABLE_COMPILE`). The spec remains unmet.
- Dependencies: `tests/test_gradients.py`, `tests/test_suite.py::TestTier2GradientCorrectness`, `docs/development/testing_strategy.md §4.1`, `arch.md §15`, perf plan task B7 (env-var alignment for compile toggles).

### Phase A — Baseline Audit & Environment Alignment
Goal: Capture authoritative evidence of current coverage gaps and ensure the compile-disable switch is consistent across harnesses before adding new tests.
Prereqs: None.
Exit Criteria: Audit note summarising missing parameters, baseline gradcheck log attached, and env-var naming decision recorded (either standardise on `NANOBRAGG_DISABLE_COMPILE` or support both).

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Document current coverage vs spec | [ ] | Review `tests/test_suite.py` and `tests/test_gradients.py`; produce `reports/gradients/<date>-tier2-baseline.md` listing which §4.1 parameters have tests, citing line numbers. |
| A2 | Capture baseline gradcheck run | [ ] | Run `env KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest tests/test_suite.py::TestTier2GradientCorrectness -vv` and archive log alongside audit. Note runtime and any skips/xfails. |
| A3 | Align compile-disable env var | [ ] | Decide on canonical env var (recommend `NANOBRAGG_DISABLE_COMPILE`) and update harness/tests accordingly, or implement compatibility shim that mirrors to both. Coordinate with PERF plan task B7; record decision in the Phase A report. |

### Phase B — Misset Rotation Gradcheck
Goal: Add gradcheck coverage for `CrystalConfig.misset_deg[0]` (rot_x) without regressing existing tests.
Prereqs: Phase A report committed; baseline tests green.
Exit Criteria: New gradcheck test passing locally with evidence logged.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Design loss function for misset_rot_x | [ ] | Reuse `Crystal` helpers to build a scalar depending on rotated reciprocal vectors; ensure gradients propagate through misset pipeline (Core Rule #12). Document reasoning in code comments referencing nanoBragg.c lines 1521–1527. |
| B2 | Implement gradcheck | [ ] | Add test in `tests/test_suite.py::TestTier2GradientCorrectness` (or helper in `tests/test_gradients.py`) invoking `torch.autograd.gradcheck` on rot_x at 89° baseline; keep dtype=torch.float64. |
| B3 | Run targeted gradcheck suite | [ ] | Execute `env KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest tests/test_suite.py::TestTier2GradientCorrectness::test_gradcheck_misset_rot_x -vv` and attach log to `reports/gradients/<date>-tier2-phaseB.log`. |

### Phase C — Beam Parameter Gradchecks
Goal: Cover beam `lambda_A` and `fluence` parameters, ensuring loss functions remain cheap enough for gradcheck.
Prereqs: Phase B tests passing.
Exit Criteria: Both new tests landed, logs captured, tolerances justified.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Craft differentiable beam configs | [ ] | Extend existing gradient fixtures to accept tensor-valued `BeamConfig` fields (avoid `.item()` conversions). Verify simulator honours float64 inputs without torch.compile. |
| C2 | Implement gradcheck_lambda | [ ] | Add `test_gradcheck_beam_wavelength` using a scalar loss (e.g., sum of final intensities for 8×8 ROI) to keep runtime manageable; cite spec requirement. |
| C3 | Implement gradcheck_fluence | [ ] | Add `test_gradcheck_fluence` verifying linear scaling of final intensity; leverage small detector ROI to keep the computation light. |
| C4 | Execute beam gradchecks | [ ] | Run `env KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest tests/test_suite.py::TestTier2GradientCorrectness -k "beam" -vv` and store log in `reports/gradients/<date>-tier2-phaseC.log`. |

### Phase D — Documentation & Regression Safeguards
Goal: Update documentation/fix_plan, ensure new tests wired into CI guidance, and add regression notes where needed.
Prereqs: Phases B & C merged.
Exit Criteria: Fix-plan attempt recorded, docs updated, optional helper utilities refactored.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Update fix_plan entry | [ ] | Record Attempt #'s with artifact paths; mark `[AT-TIER2-GRADCHECK]` ready for closure once upstream accepts. |
| D2 | Sync documentation | [ ] | Amend `docs/development/testing_strategy.md` (Tier-2 matrix) and `arch.md §15` with new coverage description; cite the new test names. |
| D3 | Add regression note | [ ] | If helper utilities were added/modified for gradient paths, document usage in `docs/development/pytorch_runtime_checklist.md` or equivalent. |

## Exit Criteria Summary
- All spec-mandated parameters (`misset_rot_x`, `lambda_A`, `fluence`) have gradcheck tests using float64 and complying with torch.compile disable guard.
- Harness consistently honours compile-disable env var with documented rationale.
- Logs under `reports/gradients/` provide reproducibility trail for each phase.
- docs/fix_plan.md `[AT-TIER2-GRADCHECK]` marked complete and plan ready for archival.
