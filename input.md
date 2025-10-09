Summary: Accept the Option 1 nb-compare results and record the documented C-PARITY-001 divergence in the ledger so the CLI parity effort can move forward to the supervisor rerun.
Mode: Docs
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: docs/fix_plan.md, plans/active/cli-noise-pix0/plan.md, reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/results/analysis.md
Do Now: CLI-FLAGS-003 N3 ledger update — pytest --collect-only -q
If Blocked: Capture a short note in reports/2025-10-cli-flags/phase_l/nb_compare/ATTEMPT_<stamp>/notes/blockers.md describing why the ledger update could not be completed; add the attempted command log to docs/fix_plan.md Attempts.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:75-84 now expects N3 to document the Option 1 acceptance before anything else proceeds.
- docs/fix_plan.md:452-510 needs a fresh Attempt entry referencing the 20251009T020401Z metrics so VG-3/VG-4 close cleanly.
- reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/results/analysis.md already explains the 0.9852 correlation and 1.159e5 sum_ratio; reuse those exact numbers to avoid drift.
- specs/spec-a-core.md:232-254 plus docs/bugs/verified_c_bugs.md:166-204 justify keeping the spec-compliant φ rotation (no shim reinstatement).
- galph_memory.md expects a follow-on note confirming the ledger closure before we can schedule the supervisor command rerun.
How-To Map:
- Review the nb-compare bundle (`analysis.md`, `summary.json`, PNGs) to lift exact correlation/sum_ratio values; no new run required.
- Append a new Attempt in docs/fix_plan.md under CLI-FLAGS-003 describing the Option 1 acceptance, citing the artifact paths and metrics; update Next Actions to point at the supervisor command rerun once done.
- Flip row N3 in plans/active/cli-noise-pix0/plan.md from [ ] to [D] and refresh the Status Snapshot bullet that still references the pending ledger update.
- Run pytest --collect-only -q from the repo root to confirm selectors remain valid; capture the command in Attempts History.
- Update galph_memory.md with a tight summary of the ledger changes and the handoff expectation for the supervisor rerun.
Pitfalls To Avoid:
- Do not edit the recorded nb-compare metrics or rerun the comparison; the evidence is already canonical.
- Do not resurrect the old phi-carryover shim or alter Option 1 thresholds.
- Keep Protected Assets (docs/index.md, loop.sh, supervisor.sh, input.md) untouched except for the intended updates.
- No production code changes—this is a docs-only loop.
- Avoid adding new artifacts outside the established reports/2025-10-cli-flags/phase_l/ tree.
- Ensure pytest is only executed with --collect-only for this documentation loop.
- Preserve vectorization/device notes in the plan; do not soften the spec references when editing.
- Maintain chronological numbering in docs/fix_plan.md Attempts; do not overwrite prior entries.
- Sync timestamps using existing bundle folders; do not create duplicate stamp directories.
- Double-check spelling of C-PARITY-001 and metric magnitudes (use scientific notation if space is tight).
Pointers:
- plans/active/cli-noise-pix0/plan.md:75-84 (N1–N3 task table)
- docs/fix_plan.md:452-510 (CLI-FLAGS ledger and Next Actions)
- reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/results/analysis.md
- specs/spec-a-core.md:232-254
- docs/bugs/verified_c_bugs.md:166-204
Next Up: 1) Nudge the supervisor command rerun (O1/O2) once ledger sync is complete; 2) Prep an archival note for Phase O3 if time allows.
