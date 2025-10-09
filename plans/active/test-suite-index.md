## Context
- Initiative: TEST-INDEX-001 — document the pytest suite so engineers can quickly discover relevant coverage, selectors, and authoritative reproduction commands.
- Phase Goal: Produce a discoverable reference under `docs/` that categorises the suite, links each test module to its acceptance criteria, and captures the canonical commands required for reproduction.
- Dependencies:
  - `docs/development/testing_strategy.md` — authoritative testing philosophy, Tier breakdown, and command sourcing rules.
  - `docs/index.md` — must reference the new document to keep it discoverable and protect it under the Protected Assets policy.
  - `docs/fix_plan.md` — ledger entry that will own attempts and cross-link reports.
  - `tests/` package (see `pytest --collect-only`) — source of truth for file names and markers.
  - `prompts/subagent_templates/` (if present) — guidance for spawning helper agents per CLAUDE.md instructions.
- Reporting: Store working artifacts under `reports/2026-01-test-index/phase_<phase>/<STAMP>/` (never commit); record commands and summaries in each bundle.

### Phase A — Baseline Inventory & Data Capture
Goal: Snapshot the current pytest surface (modules, markers, parameterisations) so the documentation reflects HEAD.
Prereqs: Repo clean aside from supervised work; `pip install -e .` available; verify `pytest` imports succeed via collect-only.
Exit Criteria: Timestamped bundle with raw collection output, parsed inventory, and summary ready for outlining.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Collect pytest metadata | [ ] | `NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q > reports/2026-01-test-index/phase_a/<STAMP>/collect.log`; capture exit code and test count. |
| A2 | Parse suite structure | [ ] | Use a subagent to ingest `collect.log` and emit `inventory.json` grouping tests by module/category (Tier, component, marker). Place output + prompt under the same bundle. |
| A3 | Annotate existing docs | [ ] | Record where tests are already documented (e.g., testing_strategy.md sections, plan references) inside `summary.md` to avoid duplication; flag gaps that the new doc must fill. |

### Phase B — Document Design & Outline
Goal: Define the structure, taxonomy, and cross-references for the forthcoming documentation.
Prereqs: Phase A inventory approved and stored; identify stakeholders (vectorization, parity, perf) needing quick selectors.
Exit Criteria: Approved outline and drafting checklist ready for execution.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Draft taxonomy proposal | [ ] | Outline sections (by Tier, component, scenario) and decide how to encode selectors/commands; capture in `reports/2026-01-test-index/phase_b/<STAMP>/outline.md`. |
| B2 | Review with plans/fix_plan | [ ] | Cross-reference existing plan items (e.g., VECTOR-TRICUBIC-002, SOURCE-WEIGHT-001) to ensure the doc highlights their mapped selectors; note expectations in `docs/fix_plan.md` next actions if additional hooks are needed. |
| B3 | Approve writing checklist | [ ] | Produce a drafting checklist (table with modules vs required metadata) under `reports/.../drafting_checklist.md`; confirm scope covers smoke commands, ROI hints, and artifact expectations. |

### Phase C — Document Authoring & Validation
Goal: Write the documentation page under `docs/` and validate that it stays in sync with the suite and guardrails.
Prereqs: Outline and checklist from Phase B complete; confirm doc filename (e.g., `docs/development/test_catalog.md`) with Protected Assets awareness.
Exit Criteria: Doc drafted, reviewed via collect-only, and linked in docs/index.md.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Produce initial draft | [ ] | Use parallel subagents to divide sections (e.g., Tier 1 vs Tier 2/3); ensure each includes selectors, purpose, acceptance thresholds, and report expectations. Store drafts under `reports/.../drafts/`. |
| C2 | Run validation checks | [ ] | `NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q` after applying doc changes to confirm suite still imports; capture log under Phase C bundle. |
| C3 | Update docs index & protections | [ ] | Insert link into `docs/index.md` and add the file to any relevant guard lists; document the change rationale in `summary.md`. |

### Phase D — Handoff, Maintenance Hooks & Closure
Goal: Integrate the new resource into workflows and establish maintenance cadence.
Prereqs: Document merged locally and referenced by plans/fix_plan entries.
Exit Criteria: Maintenance SOP captured, fix_plan updated, plan ready for archive once adoption verified.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Log ledger and plan updates | [ ] | Add attempts to `docs/fix_plan.md` `[TEST-INDEX-001]` noting artifact paths, approvals, and responsibilities; ensure dependent plans reference the new doc. |
| D2 | Define refresh cadence | [ ] | Document in `reports/2026-01-test-index/phase_d/<STAMP>/maintenance.md` how often to rerun collect-only (e.g., quarterly or after major test additions) and who owns the updates. |
| D3 | Archive or transition | [ ] | Once maintenance hooks live, move this plan to `plans/archive/` with closure summary, and note residual risks (e.g., dynamic markers) in `galph_memory.md`. |

## Interfaces & Expectations
- Subagents: When splitting authoring work, include full prompts + required artifacts so stateless agents can operate independently (per CLAUDE.md instructions).
- Commands: Source pytest selectors and CLI examples from `docs/development/testing_strategy.md`; if gaps exist, expand that doc as part of Phase C.
- Protected Assets: Once the doc is created, add it to `docs/index.md` in the core guides section and treat it as protected during hygiene passes.
- Artifacts: Reference (not commit) report directories in fix_plan attempts; include timestamps, commands, and decision notes for auditability.
