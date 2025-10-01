# Plan: ROUTING-LOOP-001 Automation Guard Refresh

**Status:** Active (supervisor-created)
**Priority:** High — protects prompt routing and prevents regression loops
**Related fix_plan item:** `[ROUTING-LOOP-001]` loop.sh routing guard — docs/fix_plan.md
**Created:** 2025-10-06 by galph (refresh after regression)

## Context
- Initiative: Error-correcting the engineer agent (automation hygiene)
- Phase Goal: Ensure `loop.sh` invokes the correct prompt (`prompts/debug.md`) once per loop cycle and performs required git hygiene without spamming `git push`.
- Dependencies: `docs/index.md` Protected Assets list, `prompts/meta.md` routing rules, `docs/fix_plan.md` entry `[ROUTING-LOOP-001]`.

### Phase A — Regression Confirmation & Scope
Goal: Capture concrete evidence that `loop.sh` currently violates routing rules.
Prerqs: None.
Exit Criteria: Report summarizing observed behavior committed under `reports/routing/` and linked from fix_plan attempts.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Record current automation script | [ ] | Run `sed -n '1,80p loop.sh'` and save output to `reports/routing/$(date +%Y%m%d)-loop-audit.txt`. Note prompt path, loop count, and git commands. |
| A2 | Diff vs prior guarded version | [ ] | Use `git show 56c46b2:loop.sh` (or other guarded commit) to capture expected behavior; include diff summary in the same report. |
| A3 | Update fix_plan attempt log | [ ] | Append Attempt entry under `[ROUTING-LOOP-001]` documenting regression evidence and linking the new report. |

### Phase B — Script Remediation
Goal: Restore guardrails so automation executes `prompts/debug.md` once per invocation and performs a single `git pull --rebase` / conditional push.
Prerqs: Phase A report filed.
Exit Criteria: Updated `loop.sh` matches routing spec; manual shellcheck passes; supervisor review complete.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Draft corrective changes | [ ] | Modify `loop.sh` to: (1) run `timeout 30 git pull --rebase` before the loop, (2) call `prompts/debug.md` exactly once, (3) push only after successful loop, and (4) respect exit codes. |
| B2 | Validate with shellcheck | [ ] | Run `shellcheck loop.sh`; address warnings without breaking Protected Assets rule (`loop.sh` listed in `docs/index.md`). |
| B3 | Dry-run automation | [ ] | Execute `./loop.sh` in a safe environment (set `CLAUDE_CMD` to `echo` for dry run) and capture output to `reports/routing/<date>-dry-run.log`. |

### Phase C — Verification & Closure
Goal: Confirm routing compliance and prevent future regressions.
Prerqs: Phase B merged in working branch.
Exit Criteria: fix_plan entry updated with metrics/artifacts; plan archived.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Final supervisor check | [ ] | Re-run A1 on merged script to confirm compliance; attach diff summary to fix_plan Attempt entry. |
| C2 | Update documentation | [ ] | Ensure `docs/fix_plan.md` Attempt references the dry-run log and notes the corrected behavior; highlight that automation must use `prompts/debug.md` while AT parity incomplete. |
| C3 | Archive plan | [ ] | Move this file to `plans/archive/routing-loop-guard/plan.md` once C1–C2 complete. |

## Notes & Guardrails
- `loop.sh` is listed in `docs/index.md` (Protected Assets rule); do not delete or rename it.
- Coordinate with ongoing parity efforts; automation must remain on `prompts/debug.md` until parity suite is green.
- Avoid reintroducing verification-only loops; ensure prompts continue to enforce authoritative test execution per `prompts/meta.md`.
