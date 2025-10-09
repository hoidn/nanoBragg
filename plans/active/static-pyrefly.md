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
- Status Snapshot (2025-12-22): Phases A and B completed in 2025-10 bundles (`reports/pyrefly/20251008T053652Z/`). New placeholder directory `reports/pyrefly/20251009T044937Z/` prepared this loop to stage Phase C follow-up.

### Phase A — Preconditions & Tool Audit
Goal: Confirm pyrefly is configured and document the command surface before any analysis run.
Prereqs: Clean git status (aside from known WIP), docs/index.md reread, fix_plan entry marked active.
Exit Criteria: Verified tool availability recorded, command plan captured, and reports directory prepared.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Verify configuration | [D] | Completed 2025-10-08 via Attempt #1 (ralph). Outputs captured in `reports/pyrefly/20251008T053652Z/commands.txt` (pyrefly v0.35.0, `[tool.pyrefly]` at pyproject.toml:11). Re-validated 2025-12-22 during supervisor loop; latest command noted in `reports/pyrefly/20251009T044937Z/commands.txt`. |
| A2 | Prep artifact directory | [D] | Completed 2025-10-08 with baseline skeleton under `reports/pyrefly/20251008T053652Z/`. Additional staging directory `reports/pyrefly/20251009T044937Z/` created 2025-12-22 to host upcoming Phase C artifacts. |
| A3 | Log preconditions in fix plan | [D] | Documented in `docs/fix_plan.md` Attempt #1 (2025-10-08). This loop (2025-12-22) added Attempt #3 to confirm tooling still available and link new staging directory. |

### Phase B — Baseline Scan Execution
Goal: Capture the first full pyrefly diagnostic run with reproducible metadata.
Prereqs: Phase A complete; ensure no prior pyrefly logs exist or archive them.
Exit Criteria: `pyrefly check src` output stored, environment captured, exit code documented.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Execute baseline run | [D] | Completed 2025-10-08 via Attempt #2 — see `reports/pyrefly/20251008T053652Z/pyrefly.log` (exit code recorded in commands.txt). |
| B2 | Capture environment snapshot | [D] | Completed 2025-10-08 (`env.json` capturing Python 3.13.7, pyrefly 0.35.0, git SHA 8ca885f). |
| B3 | Summarise diagnostics | [D] | Completed 2025-10-08 — `summary.md` groups 78 findings by rule/severity with file:line anchors ready for Phase C triage. |

### Phase C — Triage & Prioritisation
Goal: Translate raw diagnostics into actionable buckets for delegation.
Prereqs: Phase B artifacts complete.
Exit Criteria: Ranked list of issues with recommended handling recorded in both summary.md and fix_plan.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Classify findings | [D] | Completed 2025-12-22 via Attempt #4 (ralph). Results captured in `reports/pyrefly/20251009T044937Z/summary.md` with severity buckets: BLOCKER(22), HIGH(26), MEDIUM(16), DEFER(14). |
| C2 | Map to source owners/tests | [D] | Completed 2025-12-22. All blocker/high/medium items assigned to ralph with validated pytest selectors. Selectors logged in `reports/pyrefly/20251009T044937Z/commands.txt`; verified via `pytest --collect-only -q` (677 tests collected, exit 0). |
| C3 | Update fix_plan attempts | [D] | Completed 2025-12-22. `docs/fix_plan.md` STATIC-PYREFLY-001 updated with Attempt #4 containing full triage summary, artifact paths, Next Actions for Rounds 1-3, and rerun cadence. |

### Phase D — Delegation & Follow-up Hooks
Goal: Ensure Ralph receives precise execution guidance and that future loops can track progress.
Prereqs: Phase C triage complete.
Exit Criteria: `input.md` Do Now drafted, fix_plan next actions updated, and backlog references established.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Draft supervisor memo hooks | [D] | Completed 2025-10-09 (this loop). BL-1/BL-2 fix directive provided in input.md with 36 detailed steps, file:line anchors, and pytest selectors. Round 1 artifacts stored at `reports/pyrefly/20251009T061025Z/`. |
| D2 | Update fix_plan next actions | [D] | Completed 2025-10-09. `docs/fix_plan.md` STATIC-PYREFLY-001 updated with Attempt #5 (BL-1/BL-2 fixes complete, 8/14 blocker errors resolved, validation results documented). |
| D3 | Schedule re-run criteria | [D] | Completed 2025-12-22 in Attempt #4. Rerun cadence documented in fix_plan.md: "After each Ralph fix batch (Rounds 1-3), generate new pyrefly baseline; archive when violations ≤10 or all BLOCKER/HIGH items resolved." |

### Phase E — Regression Tracking & Closure
Goal: Close the loop once violations are resolved or documented for future work.
Prereqs: At least one fix batch completed by Ralph; updated pyrefly run available.
Exit Criteria: Clean pyrefly report (or documented residuals) and archival notes ready for moving this plan to `plans/archive/`.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| E1 | Validate post-fix scan | [ ] | After fixes land, rerun `pyrefly check src` and compare against baseline; store results under a new timestamped directory with diff summary. |
| E2 | Archive evidence | [ ] | Move stabilized artifacts to `reports/archive/pyrefly/<ts>/` and update fix_plan with closure metrics. |
| E3 | Retire plan | [ ] | When clean or residuals documented with roadmaps, mark this plan ready for archive and update docs/fix_plan.md status to `done`. |
