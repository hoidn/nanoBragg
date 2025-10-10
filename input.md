Summary: Extend the test-suite triage to cover the 50-failure Attempt #5 dataset and refresh the mappings before remediation work begins.
Mode: Docs
Focus: [TEST-SUITE-TRIAGE-001] Phase C5–C7 triage refresh
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-test-suite-triage/phase_c/20251010T135833Z/triage_summary.md; reports/2026-01-test-suite-triage/phase_c/20251010T135833Z/commands.txt; reports/2026-01-test-suite-triage/phase_c/20251010T135833Z/pending_actions.md
Do Now: [TEST-SUITE-TRIAGE-001] Full pytest run and triage (Phase C5–C7 refresh) — reuse Attempt #5 bundle (reports/2026-01-test-suite-triage/phase_b/20251010T135833Z); pytest repro: KMP_DUPLICATE_LIB_OK=TRUE timeout 3600 pytest tests/ -v --durations=25 --maxfail=0 --junitxml=reports/2026-01-test-suite-triage/phase_b/<STAMP>/artifacts/pytest_full.xml (rerun only if artifacts missing)
If Blocked: Capture triage_summary_stub.md noting which Attempt #5 artifacts are missing, update Attempts History with the blocker, and ping supervisor before rerunning the full suite.
Priorities & Rationale:
- plans/active/test-suite-triage.md:14 keeps Phase C refresh gated on completing the 50-failure classification before Phase D.
- plans/active/test-suite-triage.md:51 calls for new artifacts under C5–C7, including a refreshed triage summary and ledger updates.
- docs/fix_plan.md:37 lists Phase C5–C7 as the next actions; the ledger must reflect the new summary before other work resumes.
- reports/2026-01-test-suite-triage/phase_b/20251010T135833Z/summary.md:41 enumerates all 18 failure clusters that the refreshed triage must cover.
How-To Map:
- Stage the new phase_c directory: `STAMP=20251010T135833Z` ; `mkdir -p reports/2026-01-test-suite-triage/phase_c/$STAMP` ; log commands in `commands.txt`.
- Reconcile failure list: `cp reports/2026-01-test-suite-triage/phase_b/$STAMP/failures_raw.md reports/2026-01-test-suite-triage/phase_c/$STAMP/failures_raw.md` then review each node against the category table in `summary.md`.
- Draft `triage_summary.md` covering all 50 failures, highlighting deltas versus the earlier `phase_c/20251010T134156Z/triage_summary.md` snapshot.
- Update `pending_actions.md` with cluster→fix-plan mapping, noting any new owners or status changes.
- Once docs settle, refresh Attempts History for `[TEST-SUITE-TRIAGE-001]` with the new artifact path and note whether Phase C5–C7 are now [D].
Pitfalls To Avoid:
- Do not overwrite or delete the earlier `phase_c/20251010T134156Z` artifacts; keep both snapshots.
- Avoid rerunning the full pytest suite unless the Attempt #5 bundle is corrupted.
- Preserve Protected Assets listed in docs/index.md (loop.sh, input.md, etc.).
- Keep documentation ASCII-only and retain tables’ column alignment.
- When mapping clusters, ensure every failure ties back to an existing or newly created fix-plan ID—no orphan rows.
Pointers:
- plans/active/test-suite-triage.md:11
- plans/active/test-suite-triage.md:51
- docs/fix_plan.md:3
- docs/fix_plan.md:37
- reports/2026-01-test-suite-triage/phase_b/20251010T135833Z/summary.md:41
Next Up: Draft Phase D handoff (`plans/active/test-suite-triage.md` D1–D4) once the refreshed triage artifacts land.
