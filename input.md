Summary: Classify the existing pyrefly violations and prep a targeted fix backlog.
Mode: Docs
Focus: STATIC-PYREFLY-001 / Run pyrefly analysis and triage
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: reports/pyrefly/20251009T044937Z/summary.md; reports/pyrefly/20251009T044937Z/commands.txt; docs/fix_plan.md (§STATIC-PYREFLY-001); plans/active/static-pyrefly.md
Do Now: STATIC-PYREFLY-001 Phase C triage — run `pytest --collect-only -q` after updating the triage summary and ledger notes.
If Blocked: Capture blockers in reports/pyrefly/20251009T044937Z/summary.md and log a docs/fix_plan.md Attempt describing why Phase C could not proceed.
Priorities & Rationale:
- plans/active/static-pyrefly.md Phase C open — triage must precede any fix delegation.
- docs/fix_plan.md:3711 — Next Actions already call for severity/owner tagging from the 20251008 baseline.
- reports/pyrefly/20251008T053652Z/summary.md — authoritative raw findings to classify without re-running pyrefly.
- prompts/pyrefly.md — SOP mandates command sourcing and artifact structure for this loop.
- docs/development/testing_strategy.md#1.5 — requires the `pytest --collect-only -q` proof for docs-only work.
How-To Map:
- Review `reports/pyrefly/20251008T053652Z/summary.md` + `pyrefly.log`; copy findings into a new severity table in `reports/pyrefly/20251009T044937Z/summary.md` (use blocker/high/medium/defer buckets).
- For each blocker/high item, note owner + suggested pytest selector (validate with `pytest --collect-only -q <selector>` and append selector lines + exit status to `commands.txt`).
- Update `docs/fix_plan.md` Attempt history (STATIC-PYREFLY-001) with severity counts, artifact paths, and delegated next steps; mirror checklist progress in `plans/active/static-pyrefly.md` (mark C1/C2/C3 as [D] when done).
- After documentation, run `pytest --collect-only -q` from repo root; record the command and result in `commands.txt`.
- Keep all new triage artifacts under `reports/pyrefly/20251009T044937Z/`; do not touch the 20251008 baseline bundle.
Pitfalls To Avoid:
- Do not re-run `pyrefly check src` this loop (baseline already captured).
- Do not modify `[tool.pyrefly]` in pyproject.toml or Protected Assets listed in docs/index.md.
- Avoid deleting/overwriting `reports/pyrefly/20251008T053652Z/*` — Stage new work only under the 20251009 directory.
- Don’t invent pytest selectors; validate each new selector with `--collect-only` before logging it.
- Keep triage edits textual (no spreadsheets) and stay within ASCII.
- Maintain vectorization/device neutrality assumptions when assigning owners — call out tensors vs scalars explicitly.
- Respect git hygiene: no commits until artifacts and ledger updates are complete.
Pointers:
- plans/active/static-pyrefly.md
- docs/fix_plan.md:3711
- reports/pyrefly/20251008T053652Z/summary.md
- reports/pyrefly/20251008T053652Z/pyrefly.log
- prompts/pyrefly.md
- docs/development/testing_strategy.md#1.5
Next Up: Draft input hooks for Phase D delegation after the triage summary lands.
