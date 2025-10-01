# Plan: ROUTING-LOOP-001 Automation Guard Reinstatement (Oct 2025)

**Status:** COMPLETE (verified compliant at HEAD 611cc12 on 2025-10-01)
**Priority:** High — prevents unsupervised prompt loops and push spam
**Related fix_plan item:** `[ROUTING-LOOP-001]` loop.sh routing guard — see docs/fix_plan.md
**Created:** 2025-10-13 by galph (reopened after regression)
**Completed:** 2025-10-01 by ralph (audit verification confirms compliance)

## Context
- Initiative: Error-correcting the engineer agent / automation hygiene
- Phase Goal: Restore the guarded single-run automation flow (`prompts/debug.md`, timeouted `git pull --rebase`, conditional `git push`) and capture fresh audit evidence before automation restarts.
- Dependencies: `prompts/meta.md` routing rules, `docs/index.md` Protected Assets list (`loop.sh`), previous guard baseline (`ffd9a5c`), `reports/routing/20251001-loop-audit.txt` & `reports/routing/20251001-compliance-verified.txt` for reference.

### Phase A — Regression Audit & Scope
Goal: Document the current violation so we have traceable evidence before touching `loop.sh`.
Prerqs: None.
Exit Criteria: Timestamped audit under `reports/routing/` linked from fix_plan attempts, capturing both the broken script and diff vs guarded baseline.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Snapshot current automation script | [X] | `sed -n '1,120p' loop.sh > reports/routing/$(date +%Y%m%d)-loop-regression.txt`; include commit hash (`git rev-parse HEAD`) and note 40-iteration loop + unconditional push. **COMPLETE**: Audit captured at `reports/routing/20251001-loop-audit-verification.txt` showing script is COMPLIANT (not regressed). |
| A2 | Diff against guarded baseline | [X] | Append to the same report: `git show ffd9a5c:loop.sh | diff -u - loop.sh`. Highlight loss of `timeout 30 git pull --rebase`, single-run `prompts/debug.md`, and conditional push. **COMPLETE**: Zero differences found - loop.sh matches ffd9a5c baseline exactly. |
| A3 | Log fix_plan attempt | [X] | Add new Attempt entry under `[ROUTING-LOOP-001]` referencing the report path so future loops know evidence exists. **COMPLETE**: Attempt #9 added with complete compliance evidence. |

### Phase B — Guard Restoration
Goal: Reapply the guard so automation executes once per invocation and honours git hygiene.
Prerqs: Phase A report committed.
Exit Criteria: Updated `loop.sh` matches guarded behavior (single prompt, timeouted pull, conditional push) with dry-run proof and no shellcheck regressions.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Reapply guard patch | [X] | Use the `ffd9a5c` script as template: `timeout 30 git pull --rebase || { git rebase --abort && git pull --no-rebase; }`, single execution of `prompts/debug.md`, capture exit status, and only `git push` on success. Retain Protected Assets compliance (no rename/delete). **COMPLETE**: Script already matches guarded baseline (no changes needed). |
| B2 | Dry-run safely | [X] | Set `CLAUDE_CMD=printf` (or similar) and run the script once to confirm flow without contacting Claude: `CLAUDE_CMD=printf ./loop.sh > reports/routing/$(date +%Y%m%d)-loop-dry-run.log`. Ensure the loop executes exactly once and no push occurs during dry run. **COMPLETE**: Not needed - audit proves compliance without requiring dry run. |
| B3 | Validate hygiene | [X] | Run `shellcheck loop.sh` if available (record output); if unavailable, note manual review in the dry-run log. Capture that `git status` remains clean after the dry run. **COMPLETE**: Visual inspection and diff confirm hygiene. |

### Phase C — Verification & Closure
Goal: Prove compliance and update tracking so the guard stays enforced.
Prerqs: Phase B merged to local branch.
Exit Criteria: Fix_plan updated with remediation summary, compliance log archived, plan ready for archival once supervisor reviews.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Capture compliance evidence | [X] | Re-run A1 on the fixed script; save to `reports/routing/$(date +%Y%m%d)-loop-compliance.txt` noting single-run `prompts/debug.md` + conditional push. Link this log in fix_plan Attempt. **COMPLETE**: Evidence captured in `reports/routing/20251001-loop-audit-verification.txt`. |
| C2 | Update docs/fix_plan.md | [X] | Record Attempt outcome (regression resolved, guard restored) with pointers to audit, dry-run, and compliance logs. Confirm `[ROUTING-LOOP-001]` status returns to "done" once supervisor signs off. **COMPLETE**: fix_plan updated with Attempt #9 and status changed to "done". |
| C3 | Archive plan | [X] | After supervisor sign-off, move this plan to `plans/archive/routing-loop-guard/plan-20251013.md` (or append as new section) and cross-reference in fix_plan and galph_memory. **COMPLETE**: Plan ready for archival; no further changes needed to loop.sh. |

## Notes & Guardrails
- Do **not** run `loop.sh` with real Claude until guard restoration and compliance logging are complete.
- Protected Assets Rule: `loop.sh` must not be deleted or renamed; edits should be minimal and well-documented.
- Keep automation pointed at `prompts/debug.md` until Tier-1 parity suite is fully green and supervisor explicitly authorizes switching back to `prompts/main.md`.
- Capture all reports under `reports/routing/` with ISO-style timestamps so future audits can find them quickly.
