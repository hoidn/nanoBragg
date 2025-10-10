## Context
- Initiative: TEST-SUITE-TRIAGE-001 — obey long-term directive to run the full PyTorch nanoBragg pytest suite, capture failures, and classify them for remediation sequencing.
- Phase Goal: Establish a reproducible, artifact-backed understanding of current test health (`pytest tests/`) before authorising any other feature work.
- Dependencies:
  - `docs/development/testing_strategy.md` — authoritative guidance for test ordering, environment variables, and smoke test expectations.
  - `arch.md` §2 & §15 — runtime guardrails (device/dtype, differentiability) that must stay intact during triage.
  - `docs/fix_plan.md` — ledger for logging attempts, failure classifications, and follow-up tasks.
  - `docs/development/pytorch_runtime_checklist.md` — sanity checklist before executing PyTorch-heavy tests (KMP env, device neutrality).
  - `prompts/callchain.md` — fallback SOP if targeted tracing is required for specific failures (defer until triage completes).

### Status Snapshot (2026-01-12)
- Phase A ✅ complete (Attempt #1 — `reports/2026-01-test-suite-triage/phase_a/20251010T131000Z/`); 692 tests collected, no errors.
- Phase B pending: need fresh timestamped bundle capturing full-suite run, junit XML, and failure summary before triage (Phase C) can begin.

### Phase A — Preflight & Inventory
Goal: Confirm environment readiness and enumerate suite metadata so the full run is reproducible and guarded.
Prereqs: None; execute prior to any full-suite invocation.
Exit Criteria: Preflight checklist logged in `reports/2026-01-test-suite-triage/phase_a/<STAMP>/preflight.md` with env summary, disk budget, and test inventory snapshot.

| ID | Task Description | State | How/Why & Guidance (including API / document / artifact / source file references) |
| --- | --- | --- | --- |
| A1 | Confirm guardrails & env | [D] | Attempt #1 → `preflight.md` records Python 3.13, PyTorch 2.7.1+cu126, CUDA 12.6 availability; referenced `docs/development/testing_strategy.md` §§1.4–1.5. |
| A2 | Disk & cache sanity check | [D] | Attempt #1 → `disk_usage.txt` shows 77 GB free (83 % used); cleanup not required. |
| A3 | Test inventory snapshot | [D] | Attempt #1 → `collect_only.log` captured 692 collected tests, 0 errors; summarised inside `preflight.md`. |
| A4 | Update fix_plan attempts ledger | [D] | Attempt #1 logged in `docs/fix_plan.md` under `[TEST-SUITE-TRIAGE-001]` with artifact paths and counts. |

### Phase B — Full Suite Execution & Logging
Goal: Execute `pytest tests/` once, capturing complete logs, timings, and failure summaries for downstream triage.
Prereqs: Phase A checklist complete (A1–A4).
Exit Criteria: Full run log + junit/xml archived under `reports/2026-01-test-suite-triage/phase_b/<STAMP>/`; failure summary extracted into `failures_raw.md`.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Prepare reporting directory | [D] | Attempt #2 → Created `reports/2026-01-test-suite-triage/phase_b/20251010T132406Z/` with `logs/`, `artifacts/`. Documented command in `commands.txt`. |
| B2 | Execute full test suite | [⚠️] | Attempt #2 → PARTIAL (timeout after 600 s). Reached ~75 % completion (520/692 tests). Log captured to `logs/pytest_full.log` (530 lines). Observed 34 failures; ~172 tests never executed. **Next:** Attempt #5 must rerun with an extended budget (`KMP_DUPLICATE_LIB_OK=TRUE timeout 3600 pytest tests/ -v --durations=25 --maxfail=0 --junitxml=reports/2026-01-test-suite-triage/phase_b/<STAMP>/artifacts/pytest_full.xml`) and archive logs under a fresh `phase_b/<STAMP>/`. |
| B3 | Extract failure list | [D] | Attempt #2 → Extracted 34 failures into `failures_raw.md`. Categorized by test area (determinism, sourcefile, grazing, detector, debug, CLI). Noted 172 tests not reached (25% coverage gap). |
| B4 | Update fix_plan attempt entry | [D] | Attempt #2 → Updated `docs/fix_plan.md` [TEST-SUITE-TRIAGE-001] with runtime=600s, failures=34 (partial), artifact path, and recommendations for split execution. |

### Phase C — Failure Classification & Triage Ledger
Goal: Categorise failures into implementation bugs vs deprecated/obsolete tests and map them to remediation owners or follow-up plans.
Prereqs: Phase B artifacts ready.
Exit Criteria: `triage_summary.md` capturing classification table; fix_plan updated with sub-actions or delegations for each bucket.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Create triage worksheet | [D] | Attempt #3 → `reports/2026-01-test-suite-triage/phase_c/20251010T134156Z/triage_summary.md` captures classification table + context. |
| C2 | Determine category for each failure | [D] | Attempt #3 → All 34 observed failures classified as implementation bugs (triage summary §Classification Table). Remaining ~172 unexecuted tests still pending full-suite rerun (Phase B extension required). |
| C3 | Align with fix_plan | [D] | Attempt #4 → All 14 clusters mapped to fix-plan entries in `triage_summary.md` Pending Actions table. 7 new IDs created: `[CLI-DEFAULTS-001]`, `[DETERMINISM-001]`, `[DETECTOR-GRAZING-001]`, `[SOURCE-WEIGHT-002]`, `[TOOLING-DUAL-RUNNER-001]`, `[DEBUG-TRACE-001]`, `[DETECTOR-CONFIG-001]`. Index updated in `docs/fix_plan.md`. |
| C4 | Capture blockers & next steps | [D] | Attempt #4 → "Pending Actions" section added to `triage_summary.md` with cluster→fix-plan mapping table and 172 unexecuted test note. All clusters assigned owners (ralph/galph) and status (in_planning/in_progress). |

### Phase D — Remediation Roadmap Handoff
Goal: Produce a ready-to-execute backlog for Ralph (or subagents) to address failing tests without ambiguity.
Prereqs: Phase C checklist complete.
Exit Criteria: `handoff.md` summarising priority order, owners, and verifying commands; input.md instructions referencing highest-priority failure fix.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Synthesize remediation priorities | [ ] | Convert `triage_summary.md` into ordered list (P0/P1/P2). Reference spec/arch citations per failure. |
| D2 | Produce reproduction commands | [ ] | For each priority failure, note exact pytest selectors & required env (per testing_strategy §1.5). |
| D3 | Update documentation touchpoints | [ ] | Ensure `docs/fix_plan.md` Active Focus reflects remediation queue; cross-link `handoff.md`. If semantics change, flag relevant specs/tests for update. |
| D4 | Publish supervisor input template | [ ] | Once ready, craft `input.md` instructions guiding Ralph to tackle highest-priority fix; ensure Do Now references authoritative commands. |

### Exit Criteria (Plan Completion)
- Phases A–D marked complete with `[D]` status in tables.
- All artifacts stored under `reports/2026-01-test-suite-triage/` with timestamped folders and referenced in `docs/fix_plan.md`.
- `triage_summary.md` identifies categories for every failing test and maps each to a next action (bug fix, test removal request, infrastructure follow-up).
- `handoff.md` approved (by supervisor) and used to steer subsequent loops; once remediation backlog is underway, this plan can move to archive.

### Metrics & Reporting Guidelines
- Capture total runtime, pass/fail counts, and slowest tests (top 25) from `--durations=25` output.
- For each failure category, note whether GPU/CPU impact differs (device neutrality check).
- Maintain Attempt numbering continuity in `docs/fix_plan.md`; include `pytest` exit code and timestamp.

### Risks & Mitigations
- **Long runtime / timeouts:** If the full suite exceeds loop budget, split run via `pytest tests/test_*pattern*.py`; document split and recombine results in `triage_summary.md`.
- **Environment drift:** Re-run Phase A if dependencies change (new torch version, GPU availability changes).
- **Protected Assets:** Ensure `docs/index.md` references (`loop.sh`, `input.md`) remain untouched; do not delete artifacts listed there during cleanup.
- **Flaky tests:** Mark with `Needs Reproduction` status; capture rerun commands and conditions.

### References
- `docs/development/testing_strategy.md`
- `docs/architecture/pytorch_design.md`
- `specs/spec-a-core.md`
- `docs/fix_plan.md`
- `reports/` index for previous pytest attempts (search `reports/*pytest_full.log`)
