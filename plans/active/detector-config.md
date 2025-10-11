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
| B1 | Pinpoint conversion sites | [D] | **Phase M3a findings:** Conversion site confirmed as `Detector.__init__` lines 78-142 (inline, no helpers). Beam center mm→pixel conversion occurs within `__init__` but currently lacks MOSFLM offset. Type guards at lines 109-125 provide pattern reference. Recommendation: apply offset immediately after division, before geometry transforms. Reference: `reports/2026-01-test-suite-triage/phase_m3/20251011T175917Z/mosflm_sync/summary.md` §Code Location Analysis. |
| B2 | Decide offset application strategy | [D] | **Phase M3a decision:** Apply `+0.5` offset during mm→pixel conversion inside `Detector.__init__` with convention guard. Formula: `beam_center_{s,f}_pixels = beam_center_{s,f}_mm / pixel_size_mm + 0.5` (MOSFLM only), unchanged for XDS/DIALS/others. Implementation: use `if self.convention == DetectorConvention.MOSFLM:` conditional. Device/dtype discipline: ensure 0.5 offset tensor matches pixel_size properties. Justification: specs/spec-a-core.md §72, arch.md §ADR-03. Documented in mosflm_sync/summary.md §Current Implementation Status. |
| B3 | Guard against double offsets | [P] | **Phase M3a validation required:** Ralph must inspect `_calculate_pix0_vector` (lines 612-690) and SMV header export (~line 520) to confirm NO re-application of +0.5 offsets. If found, document removal in Attempt log before B2 implementation. Evidence gap: no instrumentation run completed yet; defer to implementation loop. Cite spec-a-core §72 + arch.md ADR-03 for single-application justification. |
| B4 | Outline regression tests | [D] | **Phase M3a spec:** (1) Extend `tests/test_detector_config.py::TestMosflmDefaults` with `test_mosflm_pixel_offset_applied` (expect 513.0 not 512.5) and `test_mosflm_pixel_offset_formula` verifying (51.2/0.1)+0.5=512.5. (2) Add `tests/test_detector_config.py::TestXDSDefaults::test_xds_no_pixel_offset` (expect 128.0 NOT 128.5). (3) Integration: verify `Detector.get_pixel_coords()` returns correct pix0_vector post-fix. Selectors: `pytest -v tests/test_detector_config.py::TestMosflmDefaults::test_mosflm_pixel_offset_applied` (targeted), `pytest -v tests/test_detector_config.py` (module). Expected: all pass post-B2, no regressions in existing 13 passing tests. Documented in mosflm_sync/summary.md §Test Coverage Gaps + Implementation Handoff Checklist. |

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
