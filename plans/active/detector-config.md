## Context
- Initiative: DETECTOR-CONFIG-001 — audit and remediate detector default handling so MOSFLM conventions (including the +0.5 pixel offset) match spec and unblock Sprint 1.3.
- Plan Goal: Deliver a staged implementation + validation track ensuring DetectorConfig/Detector apply MOSFLM offsets correctly without regressing other conventions, with evidence logged and docs synced.
- Dependencies:
  - specs/spec-a-core.md §§68–73 — authoritative detector convention defaults and MOSFLM +0.5 pixel rules.
  - arch.md §ADR-03 — beam-center mapping decisions (MOSFLM offset, CUSTOM caveats).
  - docs/architecture/detector.md §§8.2, 9 — detector unit system + conversion guidance (needs refresh once fix lands).
  - docs/development/c_to_pytorch_config_map.md (Beam Parameters table) — CLI ↔ config mapping sanity check.
  - reports/2026-01-test-suite-triage/phase_l/20251011T104618Z/detector_config/analysis.md — Phase L failure brief.
  - docs/fix_plan.md §[TEST-SUITE-TRIAGE-001] (Phase L) and §[DETECTOR-CONFIG-001] — ledger entries and exit criteria.

### Phase A — Evidence & Guardrail Alignment
Goal: Confirm Phase L artifacts, spec references, and runtime guardrails are captured so implementation starts from a clean footing.
Prereqs: None (executed before code edits).
Exit Criteria: Phase L bundle linked, spec/arch deltas enumerated, tracker cross-check noted.

| ID | Task Description | State | How/Why & Guidance (including API / document / artifact / source file references) |
| --- | --- | --- | --- |
| A1 | Log Phase L detector-config evidence consumption | [D] | Review `reports/2026-01-test-suite-triage/phase_l/20251011T104618Z/detector_config/analysis.md`; capture key findings in docs/fix_plan.md Attempts log (already done Attempt #17). |
| A2 | Extract canonical spec guidance | [D] | Specs §§68–73 + arch.md §ADR-03 quoted in analysis.md; no conflicts detected. Note doc drift (detector.md examples still use 51.2 mm). |
| A3 | Tracker sync gating note | [ ] | Update `reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/analysis/summary.md` and `remediation_tracker.md` once fix verified (tie-in with Phase C3). |

### Phase B — Implementation Blueprint
Goal: Define the exact code touch-points and safeguards for MOSFLM offset application without double-applying in downstream geometry.
Prereqs: Phase A complete; engineer has reviewed `Detector.__init__` flow.
Exit Criteria: Annotated blueprint covering code edits, regression risks, and test scaffolding is documented (input.md Do Now references these steps).

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Pinpoint conversion sites | [ ] | Inspect `src/nanobrag_torch/models/detector.py` lines ~70–120 (beam center tensors) and `_calculate_pix0_vector` (~640–660). Confirm only the initialization path needs +0.5 for MOSFLM, while downstream `Fclose/Sclose` logic already adds offsets conditionally. |
| B2 | Decide offset application strategy | [ ] | Preferred: add convention-aware +0.5 in Detector.__init__ when translating mm→pixels (so `beam_center_*` tensors represent pixel corners per spec). Ensure config-level defaults remain physical mm distances (51.25 mm), not pre-offset. |
| B3 | Guard against double offsets | [ ] | Audit `_calculate_pix0_vector` and header update block (lines ~520–590) to ensure applying +0.5 during initialization doesn’t require subtracting offsets elsewhere. Document adjustments needed (e.g., update MOSFLM branch subtracting 0.5 when mapping back to mm). |
| B4 | Outline regression tests | [ ] | Plan targeted assertions: retain existing tests in `tests/test_detector_config.py`; add parametrised case covering MOSFLM vs DENZO vs XDS to verify only MOSFLM gains +0.5. Consider adding property test for `Detector.get_pixel_coords()` verifying beam center maps to correct physical position. |

### Phase C — Implementation, Validation, and Documentation
Goal: Execute the fix, refresh tests/docs, and close ledger items with reproducible evidence.
Prereqs: Phase B blueprint signed off.
Exit Criteria: Detector fixes merged, targeted + full-suite validations recorded, docs/fix_plan + tracker updated, plan archived or transitioned to monitoring.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Implement MOSFLM offset fix | [ ] | Modify `Detector.__init__` conversion (and any dependent helpers identified in B3). Maintain dtype/device neutrality; avoid `.item()` on tensors. |
| C2 | Extend regression coverage | [ ] | Update `tests/test_detector_config.py` (and add new parametrised cases if needed). Run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py`. Store logs under `reports/2026-01-test-suite-triage/phase_l/<STAMP>/detector_config/`. |
| C3 | Update docs + trackers | [ ] | Refresh `docs/architecture/detector.md` §§8.2/9 to cite convention-aware formula; ensure `docs/development/c_to_pytorch_config_map.md` beam-center row clarifies offset. Update `docs/fix_plan.md` ([DETECTOR-CONFIG-001] → in_progress → done once validated) and `remediation_tracker.md` (C8 cluster progress). |
| C4 | Full-suite regression (gate) | [ ] | Once targeted tests pass, rerun `CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --maxfail=0 --durations=25` (Phase L follow-up). Capture artifacts under `reports/2026-01-test-suite-triage/phase_l/<STAMP>/full_suite/`. |
| C5 | Plan closure | [ ] | When C1–C4 complete, archive this plan (move to `plans/archive/`) and mark `[DETECTOR-CONFIG-001]` done with Attempt summary in docs/fix_plan.md.

