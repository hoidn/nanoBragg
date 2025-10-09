# Plan: ROUTING-SUPERVISOR-001 Supervisor Automation Guard

**Status:** Active (new 2025-10-13)
**Priority:** High — prevents runaway supervisor loops and unsafeguarded pushes
**Related fix_plan item:** `[ROUTING-SUPERVISOR-001]` supervisor.sh automation guard — see docs/fix_plan.md
**Created:** 2025-10-13 by galph

## Context
- Initiative: Error-correcting the engineer agent / automation hygiene
- Phase Goal: Bring `supervisor.sh` up to the same guarded, single-iteration standard as `loop.sh` (timeouted pull, single prompt execution, conditional push) before the supervisor harness runs again.
- Dependencies: `prompts/meta.md` routing rules, `docs/index.md` (Protected Assets — currently only `loop.sh`; Phase B must add `supervisor.sh` so the guard is enforced by policy), `plans/active/routing-loop-guard/plan.md` (reference implementation), commit `853cf08` (`loop.sh` guard), existing audit logs in `reports/routing/`.

---

### Phase A — Regression Audit & Scope Definition
Goal: Capture authoritative evidence of the current violation before editing `supervisor.sh`.
Prereqs: None.
Exit Criteria: Timestamped audit under `reports/routing/` capturing script snapshot + guard diff, and `[ROUTING-SUPERVISOR-001]` attempts log updated with the artifact path.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Snapshot current script | [ ] | `mkdir -p reports/routing` then `sed -n '1,160p' supervisor.sh > reports/routing/$(date +%Y%m%d-%H%M%S)-supervisor-regression.txt`; prepend commit hash via `git rev-parse HEAD`. |
| A2 | Highlight guard gaps | [ ] | Append to the same report: `git show 853cf08:loop.sh | diff -u - supervisor.sh` to document missing timeout guard, single-run flow, and conditional push. Comment the three violations explicitly. |
| A3 | Log attempt in fix_plan | [ ] | Under `[ROUTING-SUPERVISOR-001]`, add Attempt entry pointing to the audit file; note regression scope and that implementation will follow Phase B. |

---

### Phase B — Guard Design & Implementation
Goal: Design and apply a guarded single-run workflow mirroring `loop.sh`, with fallback handling for failed rebases.
Prereqs: Phase A audit committed/pushed.
Exit Criteria: `supervisor.sh` updated with timeouted pull (`timeout 30 git pull --rebase` + fallback), single execution of `prompts/supervisor.md`, conditional push guard, and dry-run evidence stored.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Draft guard design note | [D] | ✅ Complete 20251009T044254Z — Memo: `reports/routing/20251009T044254Z-supervisor-guard-design.md` (comprehensive design with guard parity table, timeout/fallback flow, single-iteration contract, conditional push logic, verification checklist, roadmap). References `loop.sh` (commit 853cf08) and specifies fallback logic: on timeout, run `git rebase --abort` then `git pull --no-rebase`. |
| B2 | Implement guarded script | [ ] | Edit `supervisor.sh` to: (1) run the timeouted pull with fallback, (2) execute `prompts/supervisor.md` exactly once via `${CODEX_CMD}`, (3) capture exit status, (4) only `git push` when local commits exist and command succeeded. Preserve logging (`tmp/supervisorlog*.txt`) and Protected Assets constraints. |
| B3 | Guarded dry run | [ ] | Run `CODEX_CMD=printf ./supervisor.sh > reports/routing/<stamp>-supervisor-dry-run.log 2>&1`. Confirm log shows single iteration, demonstrates fallback warning path, and no push attempt on dry run. |
| B4 | Hygiene verification | [ ] | `bash -n supervisor.sh` (or `shellcheck` if available) and record results in `reports/routing/<stamp>-supervisor-hygiene.txt`, including `git status` output showing expected changes only. |
| B5 | Mark supervisor.sh as protected asset | [ ] | Update `docs/index.md` Core Guides list so it includes `supervisor.sh` alongside `loop.sh`; store diff in `reports/routing/<stamp>-supervisor-protected-asset.md` and note the change in fix_plan Attempt log. |

---

### Phase C — Compliance Verification & Closure
Goal: Prove the guard is in place and update tracking so the plan can be archived.
Prereqs: Phase B changes reviewed.
Exit Criteria: Compliance log + fix_plan updates committed/pushed; plan ready to archive after supervisor sign-off.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Capture compliance snapshot | [ ] | Repeat Phase A snapshot after the fix: `sed -n '1,160p' supervisor.sh > reports/routing/<stamp>-supervisor-compliance.txt` plus note for single-run flow. Attach diff vs guard baseline showing no outstanding deviations. |
| C2 | Update docs/fix_plan.md | [ ] | Add Attempt entries for Phase B/C outcomes with links to dry-run, hygiene, and compliance logs; update status towards "done" once review complete. |
| C3 | Archive plan | [ ] | Once supervisor approves, move this file to `plans/archive/supervisor-loop-guard/plan-20251013.md` (or similar) and cross-reference in fix_plan and `galph_memory.md`. |

---

## Notes & Guardrails
- Do **not** delete or rename `supervisor.sh`; treat it as a Protected Asset and make the docs/index.md update in Phase B5 to formalise the policy before rerunning automation.
- Keep automation pointed at `prompts/supervisor.md`; no switch back to `prompts/main.md` without supervisor directive.
- Ensure the script respects exit codes: on non-zero prompt failure, skip push and surface the error in logs.
- Maintain parity with `loop.sh` guard logic so future audits can diff the two scripts easily.
- Store all reports under `reports/routing/` using `YYYYMMDD-HHMMSS` stamps for traceability.
