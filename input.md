Summary: Capture the STATIC-PYREFLY-001 baseline so we know the current pyrefly violations before delegating fixes.
Mode: Docs
Focus: STATIC-PYREFLY-001 / Run pyrefly analysis and triage (docs/fix_plan.md)
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/pyrefly/20251008T053652Z/{commands.txt,pyrefly.log,summary.md,env.json,README.md}
Do Now: STATIC-PYREFLY-001 Phase B1–B3 — run `pyrefly check src | tee reports/pyrefly/20251008T053652Z/pyrefly.log`, capture exit status + env metadata, then draft summary.md grouping diagnostics by severity.
If Blocked: If pyrefly exits non-zero or CLI missing, record the full command + stderr + exit code in commands.txt, append a TODO + Attempt in docs/fix_plan.md, and stop before making code changes.

Priorities & Rationale:
- docs/fix_plan.md:2943 — Next actions already call for the Phase B baseline run; completing it unblocks triage and delegation.
- plans/active/static-pyrefly.md:23 — Phase B checklist defines deliverables (log, env snapshot, grouped summary) we must produce this loop.
- prompts/pyrefly.md:35 — Step 1 requires capturing pyrefly output verbatim before attempting any fixes; follow the SOP literally.
- prompts/pyrefly.md:59 — Finalize step mandates logging commands + artifacts in docs/fix_plan.md Attempts, even for evidence-only loops.
- docs/development/testing_strategy.md:30 — Supervisor Do Now must cite authoritative commands; we avoid pytest runs here per evidence-only policy.
- pyproject.toml:9 — `[tool.pyrefly]` confirms config scope; verify against this stanza before trusting CLI defaults.
- docs/index.md:14 — Protected Assets reminder; ensure we do not modify indexed files while gathering logs.
- galph_memory.md (latest entry) — notes that Phase A succeeded with directory 20251008T053652Z; reuse it to keep artifacts organized.
- plans/active/static-pyrefly.md:1 — Context section reiterates artifact policy; cite it in summary.md to prove compliance.
- docs/fix_plan.md:2964 — Supervisor next actions explicitly list Phase B1–B3; referencing them demonstrates alignment with ledger expectations.
- prompts/pyrefly.md:73 — Completion checklist demands zero Protected Asset edits and plan updates; treat as acceptance criteria for this loop.
- docs/development/testing_strategy.md:32 — Collect-only pytest permitted for docs loops; plan ahead in case pyrefly flags import errors.

How-To Map:
- Step 1: Confirm you are on branch `feature/spec-based-2` and worktree is clean with `git status --short`.
- Step 2: Re-read `docs/fix_plan.md` entry at lines 2943-2968 to align on success criteria before running commands.
- Step 3: Inspect `reports/pyrefly/20251008T053652Z/` (create if absent) and ensure `commands.txt` and `README.md` from Phase A remain; do not commit this directory.
- Step 4: Append the commands you plan to run to `reports/pyrefly/20251008T053652Z/commands.txt` before execution, noting UTC timestamps.
- Step 5: Execute `pyrefly check src | tee reports/pyrefly/20251008T053652Z/pyrefly.log`; immediately record the exit status and runtime duration in commands.txt.
- Step 6: Capture environment metadata: run `python -V`, `pyrefly --version`, `git rev-parse HEAD`, and `python -m site` (or `env` for virtualenv info); collate into a well-formed JSON object stored at `reports/pyrefly/20251008T053652Z/env.json`.
- Step 7: Validate JSON structure using `python -m json.tool reports/pyrefly/20251008T053652Z/env.json > /tmp/env.pretty` and inspect the pretty output before overwriting the original.
- Step 8: Parse pyrefly.log, grouping findings by severity (blocker/high/medium/defer) and rule ID; note counts per group.
- Step 9: Create a scratchpad (e.g., `reports/pyrefly/20251008T053652Z/findings.tsv`) while triaging to avoid re-parsing logs; do not commit scratchpad.
- Step 10: Draft `reports/pyrefly/20251008T053652Z/summary.md` with sections for Overview, Command & Exit Code, Findings by Severity, Deferred Items, and Next Steps; include file:line anchors for each finding.
- Step 11: Update `reports/pyrefly/20251008T053652Z/README.md` with a short Phase B status blurb referencing summary.md and env.json.
- Step 12: Append Attempt #2 under STATIC-PYREFLY-001 in docs/fix_plan.md, citing artifacts, exit status, and a ranked list of blocker/high findings (leave fixes for later phases).
- Step 13: Add a note in docs/fix_plan.md Attempt about whether follow-up requires collect-only pytest or code changes, so future loops know the gating conditions.
- Step 14: Run `pytest --collect-only -q` ONLY if pyrefly highlights import errors that might block collection; otherwise, skip tests this loop per evidence-only gate.
- Step 15: Double-check that no tracked files were modified inadvertently with `git status --short`; revert accidental edits before finishing.
- Step 16: Record the loop outcome in `reports/pyrefly/20251008T053652Z/commands.txt` Attempts section, noting whether further investigation (Phase C) is needed immediately.
- Step 17: Ensure timestamps use UTC (`date -u +%Y-%m-%dT%H:%M:%SZ`) for reproducibility; add them beside each command entry.
- Step 18: Capture any CLI warnings or deprecation notices verbatim in summary.md so Phase C can weigh urgency.
- Step 19: If pyrefly output references configuration adjustments, cross-check with `pyproject.toml` before documenting potential remediation paths.
- Step 20: Before ending the loop, skim `summary.md` for accidental secrets or PII (none expected) and confirm wording is concise yet actionable.
- Step 21: Back up pyrefly.log to a temporary location if you plan to filter it; always keep an unedited copy in the reports directory.
- Step 22: Leave TODO placeholders (e.g., `- [ ] OWNER?`) in summary.md for findings that clearly map to other initiatives; Phase C will replace them with concrete assignments.

Pitfalls To Avoid:
- Do not modify source files or apply pyrefly auto-fixes; this loop is evidence-only per Mode: Docs.
- Avoid creating a new timestamp folder; Phase A established `20251008T053652Z` and should host all Phase B artifacts.
- Never commit `reports/pyrefly/` contents; confirm `.gitignore` coverage before staging files.
- Do not delete or edit Protected Assets listed in docs/index.md while updating documentation.
- Do not summarize findings without rule IDs and file:line anchors; Phase C relies on precise references.
- Avoid interpreting pyrefly severities heuristically; use the rule IDs and message text as reported.
- Refrain from running the full pytest suite; collect-only is permitted only if you must validate selectors mentioned in findings.
- Do not overwrite commands.txt history; append new entries with timestamps to preserve provenance from Phase A.
- Skip speculative fixes or TODO pruning until Phase C triage defines scope; just document what you observe.
- Ensure env.json is valid JSON (double quotes, proper commas) so downstream tooling can parse it without manual repair.
- Resist the urge to condense multiple findings into one bullet; separate entries keep delegation manageable.
- Do not replace pyrefly.log with a filtered version; store filters separately if needed for readability.
- Avoid referencing private developer machines or paths in summary.md; keep notes portable and repo-relative.
- Do not assume rule severities; if uncertain, copy the pyrefly classification verbatim into summary.md.
- Prevent accidental whitespace cleanup in docs/fix_plan.md outside the Attempt block; maintain existing formatting.

Pointers:
- docs/fix_plan.md:2943 — STATIC-PYREFLY-001 ledger with current Attempt history and required evidence.
- plans/active/static-pyrefly.md:23 — Phase B table describing required artifacts (pyrefly.log, env.json, summary.md).
- prompts/pyrefly.md:19 — Ground rules covering tool usage, artifact storage, and two-message cadence.
- prompts/pyrefly.md:35 — Step 1 reproduction instructions for capturing pyrefly output verbatim.
- prompts/pyrefly.md:47 — Step 3 reminds us no fixes in this pass; cite when resisting edits.
- prompts/pyrefly.md:58 — Step 5 finalize instructions for updating docs/fix_plan.md and keeping artifacts offline.
- pyproject.toml:9 — Location of `[tool.pyrefly]` block confirming repository configuration.
- docs/development/testing_strategy.md:28 — Loop execution notes dictating when collect-only pytest is appropriate.
- docs/index.md:14 — Protected-asset list underpinning the no-touch rule during evidence collection.
- galph_memory.md (latest entry) — Documents that Phase A completed; ensure your Attempt #2 references the same directory and momentum.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251007T222548Z/phase_m1_summary.md — Example of artifact summary structure to mimic in pyrefly summary.md for consistency.
- input.md (previous revision) — Review prior Mode and Do Now to maintain continuity; document differences explicitly in summary.md.

Documentation Checklist:
- [ ] commands.txt updated with every command, timestamp, and exit status.
- [ ] pyrefly.log captured without truncation (confirm file size reasonable and includes header/footer).
- [ ] env.json validated through `python -m json.tool` before finalizing.
- [ ] summary.md includes Overview, Severity Buckets, Deferred Items, Next Steps, and Artifact Paths sections.
- [ ] README.md refreshed with Phase B completion note and links to summary.md/env.json.
- [ ] docs/fix_plan.md Attempt #2 appended with metrics, artifacts, and follow-up bullets.
- [ ] No other repo files modified; `git status --short` clean at loop end.
- [ ] Notes on potential cross-initiative impact (e.g., CLI, detector) recorded in summary.md for Phase C triage.
- [ ] commands.txt end-of-loop entry captures whether collect-only pytest was required.
- [ ] Summary explicitly states Mode: Docs / evidence-only so history stays clear.

Next Up:
- Phase C (plans/active/static-pyrefly.md:34) — Once summary.md exists, prepare to classify findings and map them to owners/tests.
- CLI-FLAGS-003 Phase M (plans/active/cli-noise-pix0/plan.md:72) — Hold until pyrefly backlog is triaged; note this in docs/fix_plan.md next actions if findings touch CLI code.

Reference Commands:
- `pyrefly check src | tee reports/pyrefly/20251008T053652Z/pyrefly.log` — primary baseline run; expect non-zero exit if violations exist.
- `python -m json.tool reports/pyrefly/20251008T053652Z/env.json` — sanity-check env metadata formatting.
- `sed -n '1,40p' reports/pyrefly/20251008T053652Z/pyrefly.log` — quick header review to ensure command recorded correctly.
- `tail -n 40 reports/pyrefly/20251008T053652Z/pyrefly.log` — confirm trailer contains exit summary.
- `rg "^\[" reports/pyrefly/20251008T053652Z/pyrefly.log` — fast scan for rule IDs while drafting summary.
- `pytest --collect-only -q tests` — only if needed to validate selectors referenced in pyrefly blockers; otherwise leave unused.
- `date -u +%Y-%m-%dT%H:%M:%SZ` — generate UTC timestamps for commands.txt entries.
- `git diff --stat` — verify only docs/fix_plan.md changed before considering staging (should remain clean if no doc edits).
- `python - <<'PY'
import json,sys
path='reports/pyrefly/20251008T053652Z/summary.md'
print(f"Reminder: update {path} with severity buckets and owner guesses before finishing.")
PY` — optional reminder script; do not commit output.
- `ls -R reports/pyrefly/20251008T053652Z` — confirm expected files exist (commands.txt, README.md, env.json, pyrefly.log, summary.md).

