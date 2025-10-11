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
| B3 | Guard against double offsets | [D] | 20251011T181150Z refresh verified `_calculate_pix0_vector` (src/nanobrag_torch/models/detector.py:522-549) and SMV header path (~520) reuse the already-offset pixel values; no double +0.5 reapplication. Evidence captured in `reports/2026-01-test-suite-triage/phase_m3/20251011T181150Z/mosflm_sync/summary.md`. |
| B4 | Outline regression tests | [D] | **Phase M3a spec:** (1) Extend `tests/test_detector_config.py::TestMosflmDefaults` with `test_mosflm_pixel_offset_applied` (expect 513.0 not 512.5) and `test_mosflm_pixel_offset_formula` verifying (51.2/0.1)+0.5=512.5. (2) Add `tests/test_detector_config.py::TestXDSDefaults::test_xds_no_pixel_offset` (expect 128.0 NOT 128.5). (3) Integration: verify `Detector.get_pixel_coords()` returns correct pix0_vector post-fix. Selectors: `pytest -v tests/test_detector_config.py::TestMosflmDefaults::test_mosflm_pixel_offset_applied` (targeted), `pytest -v tests/test_detector_config.py` (module). Expected: all pass post-B2, no regressions in existing 13 passing tests. Documented in mosflm_sync/summary.md §Test Coverage Gaps + Implementation Handoff Checklist. |

### Phase C — Implementation, Validation, and Documentation
Goal: Execute the fix, refresh tests/docs, and close ledger items with reproducible evidence.
Prereqs: Phase B blueprint signed off.
Exit Criteria: Detector fixes merged, targeted + full-suite validations recorded, docs/fix_plan + tracker updated, plan archived or transitioned to monitoring.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Implement MOSFLM offset fix | [D] | **Attempt #39 (commit 95b0dbc3)** updates `DetectorConfig.__post_init__` to use `(detsize + pixel)/2` defaults for MOSFLM/DENZO while keeping the +0.5 mapping inside `Detector.__init__`. Targeted selectors now report 513.0 px (1024²) and 1024.5 px (2048²); logs live under `reports/2026-01-test-suite-triage/phase_m3/20251011T182635Z/mosflm_fix/`. |
| C2 | Extend regression coverage | [D] | Attempt #39 refreshed `tests/test_detector_config.py` + `tests/test_at_parallel_002.py`; module run (15/15) and targeted selectors succeeded. Capture a fresh stamp on the next rerun so artefacts include the updated expectations. |
| C3 | Update docs + trackers | [D] | Same commit revised `docs/architecture/detector.md` §§8.2/9 and `docs/development/c_to_pytorch_config_map.md`; `docs/fix_plan.md` now records Attempt #39. Tracker refresh remains linked to C4. |
| C4 | Full-suite regression (gate) | [P] | Latest run (`pytest_full_suite.log` in `mosflm_fix/`) stopped at 390/570 before the chunked workflow was applied. Rerun the Phase M chunk map post-fix so we have an apples-to-apples failure delta. |
| C5 | Plan closure | [ ] | When C1–C4 complete, archive this plan (move to `plans/archive/`) and mark `[DETECTOR-CONFIG-001]` done with Attempt summary in docs/fix_plan.md. |
