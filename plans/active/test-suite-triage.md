## Context
- Initiative: TEST-SUITE-TRIAGE-001 — obey long-term directive to run the full PyTorch nanoBragg pytest suite, capture failures, and classify them for remediation sequencing.
- Phase Goal: Establish a reproducible, artifact-backed understanding of current test health (`pytest tests/`) before authorising any other feature work.
- Dependencies:
  - `docs/development/testing_strategy.md` — authoritative guidance for test ordering, environment variables, and smoke test expectations.
  - `arch.md` §2 & §15 — runtime guardrails (device/dtype, differentiability) that must stay intact during triage.
  - `docs/fix_plan.md` — ledger for logging attempts, failure classifications, and follow-up tasks.
  - `docs/development/pytorch_runtime_checklist.md` — sanity checklist before executing PyTorch-heavy tests (KMP env, device neutrality).
  - `prompts/callchain.md` — fallback SOP if targeted tracing is required for specific failures (defer until triage completes).

### Phase A — Preflight & Inventory
Goal: Confirm environment readiness and enumerate suite metadata so the full run is reproducible and guarded.
Prereqs: None; execute prior to any full-suite invocation.
Exit Criteria: Preflight checklist logged in `reports/2026-01-test-suite-triage/phase_a/<STAMP>/preflight.md` with env summary, disk budget, and test inventory snapshot.

| ID | Task Description | State | How/Why & Guidance (including API / document / artifact / source file references) |
| --- | --- | --- | --- |
| A1 | Confirm guardrails & env | [ ] | Review `docs/development/testing_strategy.md` §§1.4–1.5; ensure `KMP_DUPLICATE_LIB_OK=TRUE`, `NB_C_BIN` precedence known, GPU availability noted. Capture environment via `python -m site` + `python -c "import torch; print(torch.__version__, torch.cuda.is_available())"` into `preflight.md`. |
| A2 | Disk & cache sanity check | [ ] | Ensure `reports/` has ≥2 GB free (`df -h .`). If insufficient, coordinate cleanup (respect Protected Assets). Record finding in `preflight.md`. |
| A3 | Test inventory snapshot | [ ] | Run `pytest --collect-only tests -q` (with KMP env) and store output as `collect_only.log` under Phase A stamp. Summarise counts (total tests, deselected markers) inside `preflight.md`. |
| A4 | Update fix_plan attempts ledger | [ ] | Log Phase A completion under `[TEST-SUITE-TRIAGE-001]` in `docs/fix_plan.md` with artifact paths and suite counts to keep ledger in sync. |

### Phase B — Full Suite Execution & Logging
Goal: Execute `pytest tests/` once, capturing complete logs, timings, and failure summaries for downstream triage.
Prereqs: Phase A checklist complete (A1–A4).
Exit Criteria: Full run log + junit/xml archived under `reports/2026-01-test-suite-triage/phase_b/<STAMP>/`; failure summary extracted into `failures_raw.md`.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Prepare reporting directory | [ ] | Create `reports/2026-01-test-suite-triage/phase_b/<STAMP>/` with subdirs `logs/`, `artifacts/`. Document command scaffolding in `commands.txt`. |
| B2 | Execute full test suite | [ ] | Run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --durations=25 --maxfail=0 --junitxml=artifacts/pytest_full.xml | tee logs/pytest_full.log`. Capture wall-clock runtime. |
| B3 | Extract failure list | [ ] | Parse `logs/pytest_full.log` to produce `failures_raw.md` summarising each failing test (module::test, failure type, top traceback excerpt). Attach counts (xfail, skipped). |
| B4 | Update fix_plan attempt entry | [ ] | Record Attempt ID with runtime, number of fails, and artifact paths under `[TEST-SUITE-TRIAGE-001]`. |

### Phase C — Failure Classification & Triage Ledger
Goal: Categorise failures into implementation bugs vs deprecated/obsolete tests and map them to remediation owners or follow-up plans.
Prereqs: Phase B artifacts ready.
Exit Criteria: `triage_summary.md` capturing classification table; fix_plan updated with sub-actions or delegations for each bucket.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Create triage worksheet | [ ] | Draft `triage_summary.md` with table: `Test Node | Failure Type | Root Cause Hypothesis | Category (Bug/Deprecation/Config) | Next Action | Owner`. Populate initial entries from `failures_raw.md`. |
| C2 | Determine category for each failure | [ ] | Use logs + specs to label each test. For uncertain cases, flag `Needs Investigation` with reference to spec/arch section. |
| C3 | Align with fix_plan | [ ] | For each bug-classified failure, either reference existing fix_plan item or create sub-task bullet under `[TEST-SUITE-TRIAGE-001]` (or spawn new IDs). For deprecation candidates, document rationale and propose retirement steps (requires spec update). |
| C4 | Capture blockers & next steps | [ ] | Append "Pending Actions" section to `triage_summary.md` listing tasks to delegate (e.g., targeted fixes, doc updates). Update fix_plan and, if needed, corresponding plans/active/ documents. |

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
