# Plan: AT-PARALLEL-012 Peak Match Restoration

**Status:** Active (supervisor-created)
**Priority:** High – acceptance test currently violates spec (peak-match relaxed to 86%)
**Related fix_plan item:** `[AT-PARALLEL-012-PEAKMATCH]` Restore 95% Peak Match Criterion — see docs/fix_plan.md
**Created:** 2025-10-02 by galph

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
| A1 | Re-run simple_cubic parity test and capture JSON metrics | [ ] | `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_simple_cubic_correlation -vv --json-report --json-report-file reports/2025-10-02-AT-012-peakmatch/test_results.json`; include stdout in `run.log`. |
| A2 | Generate peak comparison tables & overlays | [ ] | Use `nb-compare` or `scripts/debug_pixel_trace.py --mode peaks` with identical detector config; save CSV of matched/missing peaks plus diff heatmap PNGs into the report directory. |
| A3 | Summarize baseline in fix_plan | [ ] | Append current match count (e.g., 43/50) and artifact paths to `[AT-PARALLEL-012-PEAKMATCH]` entry. |

### Phase B — Divergence Localization
Goal: Identify whether missing peaks stem from ROI masking, intensity thresholds, orientation, or other physics discrepancies.
Prerqs: Phase A artifacts ready.
Exit Criteria: Root cause hypothesis documented with supporting traces (pixel-level logs or targeted comparisons).

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Inspect ROI mask & threshold handling | [ ] | Instrument `Simulator.run` (temporary logging or tensor dumps under `reports/.../roi_debug.pt`) to verify ROI mask zeros align with missing peaks; respect Instrumentation Rule #0. |
| B2 | Trace representative missing peak | [ ] | Use `scripts/debug_pixel_trace.py --pixel <slow> <fast>` with coordinates from A2 to compare C vs PyTorch intensities; store trace logs in the report folder. |
| B3 | Evaluate polarization/solid-angle factors | [ ] | For the traced pixel, compare intermediate multipliers (polarization, omega, lattice factor); note first divergence in a markdown summary (`reports/.../divergence.md`). |

### Phase C — Implement & Validate Fix
Goal: Apply targeted corrections (ROI mask caching, intensity scaling, etc.) and restore ≥95% peak matches without breaking other variants.
Prerqs: Hypothesis from Phase B rubber-stamped in `divergence.md`.
Exit Criteria: PyTorch simple_cubic run matches ≥95% peaks; triclinic/tilted variants remain green; new code passes core + AT suites.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Implement physics/ROI correction | [ ] | Modify simulator/crystal code per findings; ensure no `.item()` is introduced on grad tensors and follow vectorization rules. Document rationale inline sparingly. |
| C2 | Re-run focused tests | [ ] | `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_simple_cubic_correlation -vv`; if ROI changes touched other paths, rerun AT-012 tilt/triclinic variants. |
| C3 | Update artifacts | [ ] | Overwrite or append peaks tables, diff images, and trace summaries showing ≥95% matches. |

### Phase D — Tighten Assertion & Document
Goal: Align acceptance test with spec and close the fix plan item with full traceability.
Prerqs: Phase C proving ≥95% matches.
Exit Criteria: Test asserts `n_matches >= len(golden_peaks) * 0.95`, docs updated, plan archived.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Update test threshold & remove stale TODO | [ ] | Edit `tests/test_at_parallel_012.py` accordingly; ensure comment references spec and new artifact path. |
| D2 | Final validation sweep | [ ] | Run `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_parallel_*.py -k ATParallel012 -vv` plus spot-check of triclinic/tilted cases. |
| D3 | Close loops | [ ] | Update docs/fix_plan.md attempt history with final metrics, move report to `reports/archive/` if appropriate, and archive this plan (`plans/archive/at-parallel-012-peakmatch/`). |

## Notes & Guardrails
- Work must happen under `prompts/debug.md`; parity tuning outside debug mode is prohibited.
- Preserve existing instrumentation quotes from nanoBragg.c; augment rather than replace when documenting fixes.
- Respect Protected Assets Rule before deleting or relocating any report artifacts; coordinate with docs/index.md.
- If investigation reveals a broader detector geometry issue, escalate to supervisor before implementing sweeping changes.

## Phase Status Snapshot (initial)
- Phase A: [ ]
- Phase B: [ ]
- Phase C: [ ]
- Phase D: [ ]

