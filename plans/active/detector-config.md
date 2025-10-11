## Context
- Initiative: DETECTOR-CONFIG-001 — restore specification-compliant handling of detector defaults and MOSFLM convention so explicit beam centers remain unmodified while auto-derived defaults carry the required +0.5 pixel offset.
- Plan Goal: Deliver a sequenced blueprint that distinguishes MOSFLM default vs explicit beam-center flows, implements the configuration/CLI/data-model changes, and validates the fix through targeted selectors and the Phase M chunked suite rerun.
- Dependencies:
  - specs/spec-a-core.md §§68–73 — authoritative description of MOSFLM mapping and default beam-center formulas.
  - arch.md §ADR-03 — implementation decision regarding +0.5 pixel offsets and CUSTOM convention fallbacks.
  - docs/architecture/detector.md §§8.2 & 9 — detector hybrid-unit conventions to update post-fix.
  - docs/development/c_to_pytorch_config_map.md (Detector Parameters table) — CLI ↔ config parity that must reflect the new explicit/auto distinction.
  - docs/findings.md entries API-002 & CONVENTION-001 — warn about existing beam-center override semantics that interact with this fix.
  - reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/mosflm_offset/summary.md — latest failure analysis and recommended remediation option (beam_center_source flag).

### Status Snapshot (2026-01-21)
- Phase A — Evidence & Guardrail Alignment · **[D]** Phase L + M3 artifacts ingested; spec/arch cross-check complete; findings cross-referenced.
- Phase B — Behavior Contract & Blueprint Refresh · **[D]** Option A design complete (STAMP 20251011T214422Z); `beam_center_source` approach ratified with CLI propagation, test/doc impacts, and risk assessment documented in `reports/2026-01-test-suite-triage/phase_m3/20251011T214422Z/mosflm_offset/design.md`.
- Phase C — Implementation & Targeted Validation · **[P]** Awaiting supervisor approval and implementation handoff (tasks C1-C7, estimated 3-5 hours).
- Phase D — Full-Suite Regression & Closure · **[P]** Pending Phase M chunked rerun, tracker sync, and plan archival.

### Phase A — Evidence & Guardrail Alignment
Goal: Ensure prior evidence, specs, and findings are captured so implementation starts from an aligned baseline.
Prereqs: None.
Exit Criteria: Phase L/M3 evidence cited, spec statements confirmed, and interacting findings catalogued.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Digest Phase L + M3 evidence bundles | [D] | `reports/2026-01-test-suite-triage/phase_l/20251011T104618Z/detector_config/analysis.md` and `.../phase_m3/20251011T193829Z/mosflm_offset/summary.md` summarise current failures and recommended fix (Option A). |
| A2 | Confirm spec/arch statements | [D] | specs/spec-a-core.md §§68–73 & arch.md §ADR-03 explicitly require +0.5 pixel mapping for defaults only; documented in the Phase M3 summary and this plan. |
| A3 | Link active findings | [D] | docs/findings.md entries API-002 (pix0 overrides beam center) and CONVENTION-001 (CUSTOM disables offset) logged here to inform remediation risks. |

### Phase B — Behavior Contract & Blueprint Refresh
Goal: Finalise the remediation blueprint that differentiates MOSFLM default vs explicit beam centers and defines required code-touch points.
Prereqs: Phase A complete; engineering owner available to draft design note.
Exit Criteria: Design artifact captured under `reports/2026-01-test-suite-triage/phase_m3/<STAMP>/mosflm_offset/`, input.md references it, and plan tasks specify concrete implementation steps (Option A adopted or alternative ratified with rationale).

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Ratify remediation option | [D] | Compare Option A (beam_center_source flag) vs Option B heuristic per `mosflm_offset/summary.md`; document decision + rationale in `reports/.../mosflm_offset/design.md`. Default expectation: adopt Option A for clarity. |
| B2 | Define config/CLI propagation | [D] | Config/CLI propagation fully specified in design.md §§1–3 with code examples: `DetectorConfig` field addition, CLI detection logic (8 explicit flags), header ingestion handling, and conditional offset in `Detector` properties. |
| B3 | Map test & doc impacts | [D] | Test/doc impacts enumerated in design.md §§Test Impact Matrix & Documentation Impact: 5 new test cases, 3 existing files requiring updates, 3 doc files needing sync (detector.md, c_to_pytorch_config_map.md, findings.md). |
| B4 | Risk & compatibility assessment | [D] | Risk assessment complete in design.md §Risk Assessment: API-002/CONVENTION-001/header ingestion interactions documented, PyTorch device/dtype/differentiability neutrality verified, backward compatibility preserved via default="auto". |

### Phase C — Implementation & Targeted Validation
Goal: Implement the chosen blueprint, extend tests, and capture targeted validation artifacts.
Prereqs: Phase B design approved; input.md updated with implementation Do Now.
Exit Criteria: Code + tests updated, targeted selectors green with artifacts, docs synchronized, fix_plan/tracker reflecting status.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Update configuration layer | [D] | `src/nanobrag_torch/config.py` includes `BeamCenterSource` enum with AUTO/EXPLICIT values; `DetectorConfig.beam_center_source` field added with default=AUTO. Verified via test_detector_config.py (15/15 passed). |
| C2 | Adjust CLI parsing | [D] | `src/nanobrag_torch/__main__.py` detects 8 explicit beam center flags (beam_center_s/f, Xbeam/Ybeam, Xclose/Yclose, ORGX/ORGY) and sets `beam_center_source=EXPLICIT`; defaults to AUTO otherwise. Verified via CLI integration tests. |
| C3 | Apply conditional offset in Detector | [D] | `src/nanobrag_torch/models/detector.py` beam_center_s_pixels/beam_center_f_pixels properties apply +0.5 offset ONLY when `source==AUTO` and `convention==MOSFLM`. Verified via test_at_parallel_003 (PASSED). |
| C4 | Expand regression coverage | [D] | `tests/test_beam_center_source.py` added with comprehensive auto vs explicit validation; `tests/test_at_parallel_003.py` extended for explicit preservation; non-MOSFLM negative controls included. All tests passing. |
| C5 | Targeted validation bundle | [D] | Executed both commands; 16/16 tests passed in 1.95s. Logs + summary.md captured at `reports/2026-01-test-suite-triage/phase_m3/20251011T213351Z/mosflm_fix/`. No regressions detected. |
| C6 | Documentation sync | [D] | `docs/architecture/detector.md` §Beam Center Mapping updated; `docs/development/c_to_pytorch_config_map.md` MOSFLM convention row clarified with source distinction; API-002 interaction documented. |
| C7 | Ledger & tracker update | [D] | `docs/fix_plan.md` [DETECTOR-CONFIG-001] updated with Attempt #42 (this loop); C8 cluster marked RESOLVED in remediation_tracker.md (pending commit). |

### Phase D — Full-Suite Regression & Closure
Goal: Demonstrate suite-wide health post-fix, archive plan, and unblock downstream work.
Prereqs: Phase C complete; targeted bundle green.
Exit Criteria: Chunked suite rerun captured with ≤ the pre-fix 13 failures (ideally 12 once C8 resolved), fix_plan/tracker updated, plan archived.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Phase M chunked rerun | [ ] | Execute 10-command ladder from `plans/active/test-suite-triage.md` Phase M under new STAMP. Store logs in `reports/.../phase_m/<STAMP>/chunks/` and summarise failure deltas vs 20251011T193829Z baseline. |
| D2 | Synthesis & publication | [ ] | Update `reports/2026-01-test-suite-triage/phase_k/.../analysis/summary.md` and `phase_m3/.../mosflm_offset/summary.md` with post-fix results. Note any residual anomalies. |
| D3 | Plan archival | [ ] | Once D1–D2 complete, move this file to `plans/archive/` and mark `[DETECTOR-CONFIG-001]` status "done" in fix_plan. |

### References & Reproduction Commands
- Targeted tests: `pytest -v tests/test_detector_config.py`, `pytest -v tests/test_at_parallel_002.py`, `pytest -v tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation`.
- Full-suite rerun: follow Phase M chunk ladder (10 commands) with `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE` prefix per `plans/active/test-suite-triage.md`.
- Design artifacts: maintain under `reports/2026-01-test-suite-triage/phase_m3/<STAMP>/mosflm_offset/`.
