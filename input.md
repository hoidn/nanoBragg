Summary: Capture the C15 mixed-units zero-intensity failure and launch the callchain evidence pack to locate the first divergence.
Mode: Parity
Focus: TEST-SUITE-TRIAGE-001 / Sprint 1.3 (C15 mixed-units callchain)
Branch: feature/spec-based-2
Mapped tests: tests/test_at_parallel_015.py::TestATParallel015::test_mixed_units_comprehensive
Artifacts: reports/2026-01-test-suite-triage/phase_m3/$STAMP/mixed_units/{commands.txt,pytest_before.log}; reports/2026-01-test-suite-triage/phase_m3/$STAMP/mixed_units_callchain/{callchain/static.md,summary.md,trace/tap_points.md,env/trace_env.json}
Do Now: [TEST-SUITE-TRIAGE-001] Sprint 1.3 (C15 mixed-units callchain) — env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_015.py::TestATParallel015::test_mixed_units_comprehensive
If Blocked: Save stdout/stderr plus context to reports/2026-01-test-suite-triage/phase_m3/$STAMP/mixed_units/blocked.md and flag the blocker in docs/fix_plan.md Attempts History; pause for supervisor guidance.
Priorities & Rationale:
- docs/fix_plan.md:48 — Next Action #4 now calls for Sprint 1.3 mixed-units callchain with explicit S1–S3 tasks.
- plans/active/test-suite-triage.md:292 — Phase N closed; next focus directs Sprint 1.3 using the mixed-units brief.
- reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/mixed_units/summary.md:1 — Contains hypotheses, suspected code paths, and trace strategy you must reference.
- docs/development/testing_strategy.md:32 — Reiterates required env guards (KMP_DUPLICATE_LIB_OK, CPU-first) for deterministic parity runs.
How-To Map:
1. export STAMP=$(date -u +%Y%m%dT%H%M%SZ); mkdir -p reports/2026-01-test-suite-triage/phase_m3/$STAMP/mixed_units reports/2026-01-test-suite-triage/phase_m3/$STAMP/mixed_units_callchain; tee all commands into mixed_units/commands.txt.
2. Run the Do Now command, capture output via `2>&1 | tee reports/2026-01-test-suite-triage/phase_m3/$STAMP/mixed_units/pytest_before.log`; note failing assertion details.
3. Prepare callchain inputs: read the brief, extract ROI + suspected modules; then invoke prompts/callchain.md with parameters — analysis_question="Why does the mixed-units comprehensive test produce zero intensity?", initiative_id="mixed-units-callchain", scope_hints='["unit conversions","stol/dmin","scattering vector"]', roi_hint="64 64", namespace_filter="nanobrag_torch", time_budget_minutes=45.
4. Follow the callchain SOP exactly; emit artifacts under mixed_units_callchain/ (static.md, dynamic.txt if captured, tap_points.md, summary.md, env/trace_env.json). Include both C and PyTorch taps when feasible; if a hook cannot be gathered, document why in tap_points.md.
5. Update mixed_units/summary.md with an addendum summarising first-divergence findings and next validation steps; reflect status in reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md and add the Attempt to docs/fix_plan.md referencing STAMP + artifacts.
Pitfalls To Avoid:
- Do not modify production code this loop; evidence-only per Sprint 1.3 entry.
- Keep KMP_DUPLICATE_LIB_OK=TRUE on every pytest/trace invocation.
- Use fresh STAMP directories—never overwrite 20251011T193829Z evidence.
- Ensure callchain taps reuse production helpers (no re-derived math) per debugging SOP.
- Capture command provenance in commands.txt; no ad-hoc shell history reliance.
- Preserve device neutrality; stay on CPU unless evidence demands GPU follow-up.
- Record any deviations (missing taps, trace schema changes) inside tap_points.md.
- Respect Protected Assets (docs/index.md listings) during edits of trackers or summaries.
Pointers:
- docs/fix_plan.md:48
- plans/active/test-suite-triage.md:292
- reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/mixed_units/summary.md:1
- docs/development/testing_strategy.md:32
- prompts/callchain.md:1
Next Up: After callchain results, triage the first divergence and map remediation tasks for UNIT-CONV-001.
