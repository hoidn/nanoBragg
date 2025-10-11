Summary: Publish the Phase I classification bundle for the freshly rerun test suite so we can unblock remediation sequencing.
Mode: Docs
Focus: [TEST-SUITE-TRIAGE-001] Full pytest run and triage
Branch: main
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-test-suite-triage/phase_i/<STAMP>/{triage_summary.md,classification_overview.md,commands.txt}

Do Now: [TEST-SUITE-TRIAGE-001] Phase I classification (plan I1–I2) — create a new timestamped `phase_i` bundle with refreshed triage_summary.md and classification_overview.md; docs-only, no pytest run.
If Blocked: Log `phase_i/<STAMP>/blocked.md` with the missing data/artifact and update `docs/fix_plan.md` Attempt #11 with the blocker summary.
Priorities & Rationale:
- plans/active/test-suite-triage.md:11-21 promotes Phase I as the active gate after Attempt #10; we need the new tables to progress.
- docs/fix_plan.md:5-8 now lists Phase I artifacts as the critical focus; ledger must reflect Attempt #11.
- reports/2026-01-test-suite-triage/phase_h/20251011T033418Z/docs/summary.md documents the 36 failing selectors we must reclassify.
- docs/development/testing_strategy.md:15-35 defines reporting cadence and evidence expectations for suite-wide analysis.
How-To Map:
- `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)` then `mkdir -p reports/2026-01-test-suite-triage/phase_i/${STAMP}/{docs}`; record the commands you run into `reports/.../phase_i/${STAMP}/commands.txt` (keep ASCII).
- Use `reports/2026-01-test-suite-triage/phase_f/20251010T184326Z/triage_summary.md` as the structural template; clone the table layout into the new `docs/triage_summary.md` and fill counts/deltas from the Phase H junit (`phase_h/.../artifacts/pytest_full.xml`) and log (`phase_h/.../full_suite/pytest_full.log`).
- Build `docs/classification_overview.md` summarising tallies by label (Implementation Bug, Likely Deprecation, Needs Verification) and cite supporting evidence (spec sections, doc notes) per failure cluster.
- Capture any supporting snippets (e.g., `pytest --junitxml` parsing, `grep` commands) directly in `commands.txt`; include line-count checks that prove all 36 failures were reviewed.
- Once docs are written, update `docs/fix_plan.md` Attempt #11 with the new stamp, counts by classification bucket, and primary deltas vs Attempt #8; add a brief galph_memory note covering outcomes + Phase J readiness checklist.
Pitfalls To Avoid:
- Do not rerun pytest; analysis must stick to existing Phase H artifacts.
- Keep all new files ASCII and within `reports/.../phase_i/${STAMP}/`.
- Preserve triage table formatting (pipe tables) so diff noise stays low.
- Reference authoritative doc sections (spec/arch/test strategy) when justifying deprecation calls.
- Maintain fix_plan attempt numbering continuity; do not overwrite Attempt #10 details.
- Do not edit `input.md` or rename any assets listed in `docs/index.md`.
Pointers:
- docs/fix_plan.md:5
- plans/active/test-suite-triage.md:11-21
- reports/2026-01-test-suite-triage/phase_h/20251011T033418Z/docs/summary.md
- docs/development/testing_strategy.md:15-60
Next Up:
- Sketch the Phase J remediation tracker stub once Phase I docs land (plans/active/test-suite-triage.md:137-150).
