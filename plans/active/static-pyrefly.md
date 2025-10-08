## Context
- Initiative: STATIC-PYREFLY-001 — establish a repeatable static-analysis loop for `pyrefly` so we can triage violations and delegate fixes without blocking runtime work.
- Phase Goal: Produce a clear, timestamped baseline of pyrefly diagnostics, map them to fix-plan priorities, and hand Ralph a scoped backlog with authoritative commands and artifact locations.
- Dependencies: 
  - `prompts/pyrefly.md` — SOP for running the static-analysis loop.
  - `docs/development/testing_strategy.md` §1.5 — testing cadence and command sourcing rules.
  - `docs/fix_plan.md` — active item ledger for logging attempts and delegations.
  - `pyproject.toml` `[tool.pyrefly]` — configuration guardrail (must remain untouched).
  - Environment availability of the `pyrefly` CLI (verify via `command -v pyrefly`).
- Artifact Policy: Store every run under `reports/pyrefly/<YYYYMMDDTHHMMSSZ>/` with `commands.txt`, raw logs, `summary.md`, and `env.json`. Never commit these directories; reference them from fix_plan attempts.

### Phase A — Preconditions & Tool Audit
Goal: Confirm pyrefly is configured and document the command surface before any analysis run.
Prereqs: Clean git status (aside from known WIP), docs/index.md reread, fix_plan entry marked active.
Exit Criteria: Verified tool availability recorded, command plan captured, and reports directory prepared.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Verify configuration | [ ] | Run `rg -n "^\[tool\.pyrefly\]" pyproject.toml` and `pyrefly --version`. Record outputs in `reports/pyrefly/<ts>/commands.txt`. If missing, stop and add TODO to docs/fix_plan.md per prompts/pyrefly.md. |
| A2 | Prep artifact directory | [ ] | Create `reports/pyrefly/<ts>/` with skeleton files (`commands.txt`, `README.md` stub) so later runs stay consistent. |
| A3 | Log preconditions in fix plan | [ ] | Update `docs/fix_plan.md` Attempt with tool availability status and pointer to this plan (Phase A). |

### Phase B — Baseline Scan Execution
Goal: Capture the first full pyrefly diagnostic run with reproducible metadata.
Prereqs: Phase A complete; ensure no prior pyrefly logs exist or archive them.
Exit Criteria: `pyrefly check src` output stored, environment captured, exit code documented.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Execute baseline run | [ ] | From repo root: `pyrefly check src | tee reports/pyrefly/<ts>/pyrefly.log`. Preserve exit status in `commands.txt`. |
| B2 | Capture environment snapshot | [ ] | Record `python -V`, `pyrefly --version`, `git rev-parse HEAD`, and active virtualenv info into `reports/pyrefly/<ts>/env.json` (structured JSON preferred). |
| B3 | Summarise diagnostics | [ ] | Create `reports/pyrefly/<ts>/summary.md` listing violations grouped by rule/severity with file:line anchors. Highlight blockers (undefined names/import errors) vs style-only findings. |

### Phase C — Triage & Prioritisation
Goal: Translate raw diagnostics into actionable buckets for delegation.
Prereqs: Phase B artifacts complete.
Exit Criteria: Ranked list of issues with recommended handling recorded in both summary.md and fix_plan.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Classify findings | [ ] | Tag each issue as `blocker`, `high`, `medium`, or `defer`. Use pyrefly rule IDs and reason phrases. |
| C2 | Map to source owners/tests | [ ] | For each blocker/high item, identify likely module owner (e.g., detector, crystal, CLI) and candidate pytest selectors (validated via `pytest --collect-only`). Record in `summary.md`. |
| C3 | Update fix_plan attempts | [ ] | Append Attempt to `docs/fix_plan.md` with ranked findings, artifact paths, and recommended next steps (e.g., "delegate to Ralph in next input.md"). |

### Phase D — Delegation & Follow-up Hooks
Goal: Ensure Ralph receives precise execution guidance and that future loops can track progress.
Prereqs: Phase C triage complete.
Exit Criteria: `input.md` Do Now drafted, fix_plan next actions updated, and backlog references established.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Draft supervisor memo hooks | [ ] | In `input.md` (next supervisor run), reference this plan’s Phase B/C artifacts, provide exact `pyrefly` command, and enumerate top 1–2 findings to fix. |
| D2 | Update fix_plan next actions | [ ] | Under STATIC-PYREFLY-001, add bullet list of the immediate fixes to pursue (with rule IDs, file paths, and expected pytest selectors). |
| D3 | Schedule re-run criteria | [ ] | Define when to rerun pyrefly (e.g., after each fix batch or weekly). Document in fix_plan and `summary.md` to avoid redundant scans. |

### Phase E — Regression Tracking & Closure
Goal: Close the loop once violations are resolved or documented for future work.
Prereqs: At least one fix batch completed by Ralph; updated pyrefly run available.
Exit Criteria: Clean pyrefly report (or documented residuals) and archival notes ready for moving this plan to `plans/archive/`.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| E1 | Validate post-fix scan | [ ] | After fixes land, rerun `pyrefly check src` and compare against baseline; store results under a new timestamped directory with diff summary. |
| E2 | Archive evidence | [ ] | Move stabilized artifacts to `reports/archive/pyrefly/<ts>/` and update fix_plan with closure metrics. |
| E3 | Retire plan | [ ] | When clean or residuals documented with roadmaps, mark this plan ready for archive and update docs/fix_plan.md status to `done`. |
