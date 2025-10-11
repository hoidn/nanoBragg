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

### Status Snapshot (2026-01-22)
- Phase A — Evidence & Guardrail Alignment · **[D]** Phase L + M3 artifacts ingested; spec/arch cross-check complete; findings cross-referenced.
- Phase B — Behavior Contract & Blueprint Refresh · **[P]** Need to ratify the Option A `beam_center_source` approach, document CLI propagation, and capture risk/compatibility notes before coding.
- Phase C — Implementation & Targeted Validation · **[ ]** Pending code/test changes once the blueprint is approved.
- Phase D — Full-Suite Regression & Closure · **[ ]** Pending post-fix chunked rerun, tracker sync, and plan archival.

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
| B1 | Ratify remediation option | [P] | Compare Option A (beam_center_source flag) vs Option B heuristic per `mosflm_offset/summary.md`; document decision + rationale in `reports/.../mosflm_offset/design.md`. Default expectation: adopt Option A for clarity. |
| B2 | Define config/CLI propagation | [P] | Specify required updates to `DetectorConfig`, CLI parsing in `__main__.py`, and any factory helpers so `beam_center_source` is tracked end-to-end. Capture field defaults, enum, and backward compatibility rules. |
| B3 | Map test & doc impacts | [P] | Enumerate the test cases to add/adjust (auto vs explicit, multiple conventions, edge case where explicit equals default). Outline doc sections needing edits (`detector.md`, `c_to_pytorch_config_map.md`). |
| B4 | Risk & compatibility assessment | [P] | Identify interactions with findings API-002/CONVENTION-001, PyTorch dtype/device neutrality, and how CUSTOM/XDS conventions behave. Record in design note. |

### Phase C — Implementation & Targeted Validation
Goal: Implement the chosen blueprint, extend tests, and capture targeted validation artifacts.
Prereqs: Phase B design approved; input.md updated with implementation Do Now.
Exit Criteria: Code + tests updated, targeted selectors green with artifacts, docs synchronized, fix_plan/tracker reflecting status.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Update configuration layer | [ ] | Modify `src/nanobrag_torch/config.py` to include `beam_center_source` (enum or Literal). Ensure editable install entry points propagate the flag. |
| C2 | Adjust CLI parsing | [ ] | In `src/nanobrag_torch/__main__.py`, set `beam_center_source="explicit"` whenever `-Xbeam/-Ybeam`, `--beam-center-*`, or API overrides are supplied; default to `"auto"` otherwise. Maintain determinism with existing defaults. |
| C3 | Apply conditional offset in Detector | [ ] | Update `Detector.__init__` to add +0.5 only when `beam_center_source == "auto"` and convention is MOSFLM. Guard tensor dtype/device; ensure `_is_default_config` remains consistent. |
| C4 | Expand regression coverage | [ ] | Extend `tests/test_detector_config.py` and `tests/test_at_parallel_002.py` with auto vs explicit assertions, plus non-MOSFLM negative controls. Add new test for "explicit matches default" to verify no accidental offset. |
| C5 | Targeted validation bundle | [ ] | Run:
  - `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py`
  - `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation`
 Capture logs + `summary.md` under `reports/2026-01-test-suite-triage/phase_m3/<STAMP>/mosflm_fix/`. |
| C6 | Documentation sync | [ ] | Update `docs/architecture/detector.md` §§8.2/9, `docs/development/c_to_pytorch_config_map.md`, and any quick-reference tables to describe explicit/auto behavior. Note interaction with findings API-002. |
| C7 | Ledger & tracker update | [ ] | Refresh `[DETECTOR-CONFIG-001]` entry in `docs/fix_plan.md` (attempt log + next actions), and update `reports/2026-01-test-suite-triage/phase_j/.../remediation_tracker.md` to mark C8 resolved. |

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
