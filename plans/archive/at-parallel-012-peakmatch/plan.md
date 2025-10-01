# Plan: AT-PARALLEL-012 Peak Match Restoration

**Status:** Archived – completed 2025-09-30 (supervisor-created)
**Priority:** High – acceptance test violated spec (peak-match relaxed to 86%)
**Related fix_plan item:** `[AT-PARALLEL-012-PEAKMATCH]` Restore 95% Peak Match Criterion — see docs/fix_plan.md
**Created:** 2025-10-02 by galph
**Completion Summary (2025-09-30):** Float64 peak detection noise was the sole blocker; casting the PyTorch image to `float32` before `find_peaks` restored 50/50 matches with 0.0 px mean distance. Artifacts recorded under `reports/2025-09-30-AT-012-peakmatch/` and tests tightened back to the ≥95 % requirement in `tests/test_at_parallel_012.py`.

## Context
- Initiative: AT-PARALLEL-012-PEAKMATCH (restore ≥95% peak alignment for simple_cubic harness)
- Phase Goal: Diagnose and eliminate the five missing peaks preventing ≥95% matches, then tighten the assertion.
- Dependencies: `specs/spec-a-parallel.md` (peak matching contract), `docs/architecture/pytorch_design.md` §4.2 (detector ROI/intensity pipeline), existing parity artifacts under `reports/2025-09-29-AT-PARALLEL-012/`.

## Phase Overview
- **Phase A — Baseline Reproduction & Artifact Refresh:** Capture authoritative metrics and visuals for the current failure.
- **Phase B — Divergence Localization:** Trace missing peaks back to specific physics components (ROI mask, intensity scaling, polarization, etc.).
- **Phase C — Implement & Validate Fix:** Apply targeted code changes, restore ≥95% matches, and confirm no regressions elsewhere.
- **Phase D — Tighten Assertion & Document:** Update the acceptance test back to spec thresholds and archive the diagnostic trail.

---

### Phase A — Baseline Reproduction & Artifact Refresh
Goal: Produce up-to-date evidence of the peak shortfall and store it under a dedicated report directory.
Prerqs: Ensure AT-012 correlates at ≥0.999 (already true per fix_plan Attempt #16).
Exit Criteria: Report directory `reports/2025-10-02-AT-012-peakmatch/` (or newer) contains test run logs, peak tables, and image overlays showing the five missing peaks; docs/fix_plan.md updated with artifact paths.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Re-run simple_cubic parity test and capture JSON metrics | [D] | Executed pytest run recorded inside `reports/2025-09-30-AT-012-peakmatch/final_summary.json`; stdout attached in commit `a2a9e83`. |
| A2 | Generate peak comparison tables & overlays | [D] | `reports/2025-09-30-AT-012-peakmatch/peak_detection_summary.json` captures matched/missing peak counts; image overlays were unnecessary once dtype fix eliminated divergence. |
| A3 | Summarize baseline in fix_plan | [D] | Attempt #3 under `[AT-PARALLEL-012-PEAKMATCH]` documents baseline metrics and artifact paths. |

### Phase B — Divergence Localization
Goal: Identify whether missing peaks stem from ROI masking, intensity thresholds, orientation, or other physics discrepancies.
Prerqs: Phase A artifacts ready.
Exit Criteria: Root cause hypothesis documented with supporting traces (pixel-level logs or targeted comparisons).

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Inspect ROI mask & threshold handling | [D] | Waived—dtype experiment (B4) isolated the issue; no ROI anomalies observed in artifacts. |
| B2 | Trace representative missing peak | [D] | Waived after B4 confirmed dtype mismatch; no additional pixel trace required. |
| B3 | Evaluate polarization/solid-angle factors | [D] | Waived—float32 casting resolved the divergence; polarization/Ω parity already matched (see Attempt #16 notes). |
| B4 | Check dtype sensitivity of peak detection | [D] | Completed via float32 cast experiment; metrics logged in `reports/2025-09-30-AT-012-peakmatch/final_summary.json`. |

> 2025-10-02 note: Supervisor reproduction confirmed that casting the PyTorch image to float32 prior to `find_peaks` yields 50/50 matches with 0.0 px mean distance, whereas the current float64 path produces only 45 peaks (43 matched). Treat this as the leading hypothesis until refuted by Phase B traces.

### Phase C — Implement & Validate Fix
Goal: Apply targeted corrections (ROI mask caching, intensity scaling, etc.) and restore ≥95% peak matches without breaking other variants.
Prerqs: Hypothesis from Phase B rubber-stamped in `divergence.md`.
Exit Criteria: PyTorch simple_cubic run matches ≥95% peaks; triclinic/tilted variants remain green; new code passes core + AT suites.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Implement physics/ROI correction | [D] | Addressed at test layer: casting PyTorch image to `float32` prior to `find_peaks` (commit `a2a9e83`) restored ≥95 % matches without physics changes. |
| C2 | Re-run focused tests | [D] | `tests/test_at_parallel_012.py` suite re-run (`suite: pass` in commit `a2a9e83`); triclinic and tilted variants recorded as PASS in final_summary.json. |
| C3 | Update artifacts | [D] | Reports under `reports/2025-09-30-AT-012-peakmatch/` capture before/after metrics and rationale. |

### Phase D — Tighten Assertion & Document
Goal: Align acceptance test with spec and close the fix plan item with full traceability.
Prerqs: Phase C proving ≥95% matches.
Exit Criteria: Test asserts `n_matches >= len(golden_peaks) * 0.95`, docs updated, plan archived.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Update test threshold & remove stale TODO | [D] | Assertion restored to ≥95 % in `tests/test_at_parallel_012.py` (commit `a2a9e83`). |
| D2 | Final validation sweep | [D] | AT-012 family rerun alongside smoke set; commit message documents passing results. |
| D3 | Close loops | [D] | Fix-plan Attempt #3 records closure; plan archived here for reference (reports retained under 2025-09-30 timestamp).

## Notes & Guardrails
- Work must happen under `prompts/debug.md`; parity tuning outside debug mode is prohibited.
- Preserve existing instrumentation quotes from nanoBragg.c; augment rather than replace when documenting fixes.
- Respect Protected Assets Rule before deleting or relocating any report artifacts; coordinate with docs/index.md.
- If investigation reveals a broader detector geometry issue, escalate to supervisor before implementing sweeping changes.

## Phase Status Snapshot (final)
- Phase A: [D]
- Phase B: [D]
- Phase C: [D]
- Phase D: [D]
