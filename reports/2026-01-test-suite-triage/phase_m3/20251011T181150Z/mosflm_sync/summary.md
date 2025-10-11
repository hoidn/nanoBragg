# Phase M3a — MOSFLM Remediation Sync (Refresh)

**Initiative:** TEST-SUITE-TRIAGE-001  
**Phase:** M3a — MOSFLM Beam-Center Offset  
**Timestamp:** 20251011T181150Z  
**Mode:** Docs-only (reuse existing test evidence; no new pytest execution)

---

## Executive Recap
- `tests/test_detector_config.py` now passes end-to-end (15/15) per `reports/2026-01-test-suite-triage/phase_m/current/detector_config/pytest.log`.
- `Detector.__init__` applies the MOSFLM +0.5 pixel offset during mm→pixel conversion (`src/nanobrag_torch/models/detector.py:90-107`).
- `_calculate_pix0_vector` consumes the already-offset pixel values, so there is no double-application of the 0.5 correction (`src/nanobrag_torch/models/detector.py:522-549`).
- Phase M3a remains complete; this refresh confirms the blueprint is still correct and promotes B3 (double-offset guard) to **[D]one** in `plans/active/detector-config.md`.

**Current Failure Count:** 0 open failures attributable to MOSFLM offset. Remaining suite gaps belong to other clusters (C8, C9).

---

## Evidence
- **Targeted test log:** `reports/2026-01-test-suite-triage/phase_m/current/detector_config/pytest.log` (shows 15/15 tests passing in 2.95s).
- **Code inspection:**
  - `src/nanobrag_torch/models/detector.py:90-107` — converts beam centers to pixels and adds 0.5 when `DetectorConvention.MOSFLM`.
  - `src/nanobrag_torch/models/detector.py:522-549` — converts the stored pixel values back to meters; no additional +0.5 is applied.
- **Spec references:** `specs/spec-a-core.md:60-87` (MOSFLM convention), `arch.md:60-120` (ADR-03 mapping), `docs/development/c_to_pytorch_config_map.md` (Detector parameters table).

---

## Reproduction Commands
- **Targeted selector:**
  ```bash
  KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py::TestDetectorInitialization::test_default_initialization
  ```
- **Module coverage:**
  ```bash
  KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py
  ```

(Logs above were captured previously; no new run performed this loop.)

---

## Plan & Ledger Updates
- `plans/active/detector-config.md` — mark Phase B task **B3 Guard against double offsets** as `[D]` with a note referencing the code audit above.
- `docs/fix_plan.md` — record Attempt #32 summarising this refresh and drop the Phase M3a Next Action (Task #1) from `[TEST-SUITE-TRIAGE-001]`.
- `remediation_tracker.md` (Phase J bundle) — already notes C6 as resolved; reference this refresh if additional confirmation is desired.

---

## Next Steps
1. **Phase M3b — Detector orthogonality owner notes (Cluster C8).** Draft `reports/2026-01-test-suite-triage/phase_m3/$STAMP/detector_ortho/notes.md` capturing owners, reproduction command `pytest -v tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_large_detector_tilts`, and outstanding questions.
2. **Phase M3c — Mixed-units hypothesis pack (Cluster C9).** After M3b notes land, prepare `mixed_units/hypotheses.md` linking to `[VECTOR-PARITY-001]` mixed-unit investigations.
3. When implementation resumes, rerun the targeted detector-config module and append the new log under the corresponding `phase_m3/$STAMP/` directory.

---

## Checklist Summary
| Item | Status | Notes |
| --- | --- | --- |
| Verify targeted tests still pass | ✅ | `phase_m/current/detector_config/pytest.log` shows 15/15 passing |
| Confirm single +0.5 application | ✅ | `detector.py:90-107` and `detector.py:522-549` reviewed |
| Update detector-config plan (B3) | ✅ | Marked [D] in this loop |
| Refresh fix_plan attempts | ✅ | Added Attempt #32 (refresh) |
| Prepare handoff to M3b | ⏳ | Pending new `input.md` directive |

---

_No new code or tests were executed; this loop revalidated documentation and plan accuracy for MOSFLM offset remediation._
