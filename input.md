Summary: Close Phase O by logging the VG-5 ledger entry and archiving the accepted supervisor bundle so CLI-FLAGS-003 can move on to the Phase P watch tasks.
Mode: Docs
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q tests/test_cli_scaling_phi0.py
Artifacts: docs/fix_plan.md, plans/active/cli-noise-pix0/plan.md, reports/2025-10-cli-flags/phase_l/supervisor_command/20251009T024433Z/, reports/archive/cli-flags-003/supervisor_command/20251009T024433Z/
Do Now: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm — Update the VG-5 ledger entry with the 20251009T024433Z supervisor run, refresh the plan status, mirror the bundle into reports/archive, then run `pytest --collect-only -q tests/test_cli_scaling_phi0.py` to record collection proof.

If Blocked: Note the issue in reports/archive/cli-flags-003/supervisor_command/blocked.md with the attempted command/output, then append the blocker summary to docs/fix_plan.md Attempts instead of forcing progress.

Priorities & Rationale:
- docs/fix_plan.md:474-475 already acknowledge Attempts #202/#203; adding a VG-5 closure Attempt keeps the ledger consistent.
- plans/active/cli-noise-pix0/plan.md:88-99 now expects O2/O3 to finish before Phase P; status snapshot must show Phase O complete.
- reports/cli-flags-o-blocker/summary.md documents why the supervisor sum ratio is acceptable; reference it when updating analysis.md and the ledger.
- reports/2025-10-cli-flags/phase_l/supervisor_command/20251009T024433Z/analysis.md still says “BLOCKER” — flip it to PASS with a short addendum citing Attempt #203.
- docs/index.md lists input.md and loop.sh as protected assets — keep archival copies under reports/archive, not by renaming existing files.

How-To Map:
- Edit reports/2025-10-cli-flags/phase_l/supervisor_command/20251009T024433Z/analysis.md: change the Status banner to a pass case and add a brief “Resolution” paragraph linking to reports/cli-flags-o-blocker/summary.md.
- Record a fresh Attempt in docs/fix_plan.md under CLI-FLAGS-003: summarize correlation 0.9966, sum_ratio 1.26451e5, note C-PARITY-001 tolerance, and state that O2/O3 are underway; include both bundle paths.
- Update plans/active/cli-noise-pix0/plan.md: adjust the status snapshot to say Phase O closed, mark rows O2/O3 [D], and note the archive path.
- Create reports/archive/cli-flags-003/supervisor_command/20251009T024433Z/: copy the existing bundle contents, add summary.md capturing acceptance metrics + tolerance statement, and write commands.txt with the cp commands you used (one line per command).
- After documentation and archive updates, run `pytest --collect-only -q tests/test_cli_scaling_phi0.py` and save the log as reports/archive/cli-flags-003/supervisor_command/pytest_collect.log for provenance.

Pitfalls To Avoid:
- Do not rerun nb-compare; reuse the existing 20251009T024433Z outputs.
- Leave reports/cli-flags-o-blocker/ intact — no overwrites.
- Keep archive copies byte-identical; use cp -a rather than editing files in place.
- Don’t modify galph_memory.md; flag closure via the new Attempt so the supervisor can log it next loop.
- Ensure paths under reports/archive use lower case and no spaces; match the directory name exactly.
- No code changes or new tests; this loop is documentation/archival only.
- Respect Protected Assets (docs/index.md) and do not move input.md/loop.sh.
- When editing markdown, stay ASCII and avoid trailing whitespace so diffs stay clean.

Pointers:
- docs/fix_plan.md:474-475 — target location for the new VG-5 Attempt entry.
- plans/active/cli-noise-pix0/plan.md:35-37,95-97 — bullets and table rows to update once archives are in place.
- reports/cli-flags-o-blocker/summary.md — authoritative explanation for the accepted sum ratio.
- reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/results/summary.json — ROI metrics to cite when contrasting supervisor vs ROI.
- specs/spec-a-core.md:204-237 — reiterates the fresh φ rotation rule; mention it when framing why Option 1 is the accepted path.

Next Up:
- 1) Draft Phase P watch checklist (nb-compare smoke cadence + trace harness reminders) once archives are in place.
- 2) Kick off STATIC-PYREFLY-001 Phase A to capture the tool availability baseline after the CLI plan closes.
