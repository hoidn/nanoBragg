## Context
- Initiative: TEST-SUITE-TRIAGE-001 — obey long-term directive to run the full PyTorch nanoBragg pytest suite, capture failures, and classify them for remediation sequencing.
- Phase Goal: Establish a reproducible, artifact-backed understanding of current test health (`pytest tests/`) before authorising any other feature work.
- Dependencies:
  - `docs/development/testing_strategy.md` — authoritative guidance for test ordering, environment variables, and smoke test expectations.
  - `arch.md` §2 & §15 — runtime guardrails (device/dtype, differentiability) that must stay intact during triage.
  - `docs/fix_plan.md` — ledger for logging attempts, failure classifications, and follow-up tasks.
  - `docs/development/pytorch_runtime_checklist.md` — sanity checklist before executing PyTorch-heavy tests (KMP env, device neutrality).
  - `prompts/callchain.md` — fallback SOP if targeted tracing is required for specific failures (defer until triage completes).

### Status Snapshot (2026-01-13)
- Phase A ✅ complete (Attempt #1 — `reports/2026-01-test-suite-triage/phase_a/20251010T131000Z/`); 692 tests collected, no errors.
- Phase B ✅ complete (Attempt #5 — `reports/2026-01-test-suite-triage/phase_b/20251010T135833Z/`); full suite executed in 1865 s with 50 failures captured across 18 clusters.
- Phase C refresh **pending:** existing triage summary (`phase_c/20251010T134156Z/`) only covers the 34-failure partial run; we must extend classification/mapping to the 50-failure Attempt #5 set before Phase D handoff.

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
| B2 | Execute full test suite | [D] | Attempt #5 → ✅ Completed with extended timeout (`reports/2026-01-test-suite-triage/phase_b/20251010T135833Z/`). Runtime 1864.76 s, 50 failures recorded, junit XML archived. Prior timeout resolved. |
| B3 | Extract failure list | [D] | Attempt #2 → Extracted 34 failures into `failures_raw.md`. Categorized by test area (determinism, sourcefile, grazing, detector, debug, CLI). Noted 172 tests not reached (25% coverage gap). |
| B4 | Update fix_plan attempt entry | [D] | Attempt #2 → Updated `docs/fix_plan.md` [TEST-SUITE-TRIAGE-001] with runtime=600s, failures=34 (partial), artifact path, and recommendations for split execution. |

### Phase C — Failure Classification & Triage Ledger
Goal: Categorise failures into implementation bugs vs deprecated/obsolete tests and map them to remediation owners or follow-up plans.
Prereqs: Phase B artifacts ready (Attempt #5 bundle).
Exit Criteria: Updated `triage_summary.md` covering the full 50-failure dataset, plus refreshed fix_plan mappings and pending-actions table referencing the new artifact timestamp.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Create triage worksheet | [D] | Attempt #3 → `reports/2026-01-test-suite-triage/phase_c/20251010T134156Z/triage_summary.md` captures classification table + context for the partial run. |
| C2 | Determine category for each failure | [D] | Attempt #3 → All 34 observed failures classified as implementation bugs (triage summary §Classification Table). Remaining tests flagged pending rerun. |
| C3 | Align with fix_plan | [D] | Attempt #4 → Mapped initial clusters to fix-plan entries (`[CLI-DEFAULTS-001]`, `[DETERMINISM-001]`, etc.). |
| C4 | Capture blockers & next steps | [D] | Attempt #4 → "Pending Actions" section added to `triage_summary.md` with cluster→fix-plan mapping + coverage gap callout. |
| C5 | Harvest Attempt #5 failure set | [ ] | Create new timestamped bundle `reports/2026-01-test-suite-triage/phase_c/20251010T135833Z/` and ingest `failures_raw.md`, junit XML, and duration data from Attempt #5 (50 failures). |
| C6 | Extend classification to full dataset | [ ] | Update `triage_summary.md` (new timestamp) with 18-cluster coverage, marking deltas vs the 34-failure snapshot. Preserve original file for traceability; new summary should reference both Attempt #2 and Attempt #5 bundles. |
| C7 | Refresh fix_plan & plan linkages | [ ] | Update `docs/fix_plan.md` `[TEST-SUITE-TRIAGE-001]` next actions + attempts to cite the new triage artifacts; ensure plan tables (this file) reference the refreshed timestamp before moving to Phase D. |

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
