Summary: Confirm the dtype blocker is truly cleared by running the determinism smoke test and logging a go/no-go for Sprint 1.
Mode: Parity
Focus: [TEST-SUITE-TRIAGE-001] Full pytest run and triage
Branch: feature/spec-based-2
Mapped tests: tests/test_at_parallel_013.py::test_pytorch_determinism_same_seed
Artifacts: reports/2026-01-test-suite-triage/phase_j/<STAMP>/pre_sprint/{commands.txt,pytest.log,summary.md}
Do Now: [TEST-SUITE-TRIAGE-001] Pre-Sprint blocker verification — CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py::test_pytorch_determinism_same_seed -x
If Blocked: Capture pytest.log plus summary.md noting dtype crash persists, update docs/fix_plan.md Attempts with the log path, and halt Sprint 1 until dtype neutrality is re-fixed.
Priorities & Rationale:
- docs/fix_plan.md:39-54 mandates the Pre-Sprint smoke test before any Sprint 1 remediation.
- plans/active/test-suite-triage.md:131-140 captures Phase J gating deliverables that depend on this verification.
- reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_sequence.md:17-44 defines the exact command and go/no-go decision logic.
- plans/active/determinism.md:1-74 shows Phase A reproduction tasks that this smoke run feeds.
- docs/development/testing_strategy.md:1-120 provides the authoritative env/test discipline (KMP env, targeted selectors only).
How-To Map:
- export STAMP=$(date -u +%Y%m%dT%H%M%SZ); mkdir -p reports/2026-01-test-suite-triage/phase_j/$STAMP/pre_sprint and echo the value into commands.txt alongside the exact pytest command and env vars used.
- Run CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py::test_pytorch_determinism_same_seed -x | tee reports/2026-01-test-suite-triage/phase_j/$STAMP/pre_sprint/pytest.log.
- Summarise pass/fail outcome, presence or absence of dtype crashes, and next-step recommendation in summary.md (include go/no-go for Sprint 1 determinism work).
- Update docs/fix_plan.md `[TEST-SUITE-TRIAGE-001]` Attempts with Attempt #13 (Pre-Sprint verification) referencing the new artifact paths and decision.
- Append a short status line to remediation_tracker.md (under C2/C15 rows) noting Pre-Sprint gate result, linking to summary.md.
Pitfalls To Avoid:
- Do not edit simulator code or widen test scope beyond the mapped selector.
- Keep protected assets untouched and respect docs/index.md guardrails.
- Ensure KMP_DUPLICATE_LIB_OK=TRUE is exported; missing it can crash torch imports.
- Avoid running the full pytest suite; stay within the single determinism test.
- If the test unexpectedly passes, still document correlation/tolerance context before declaring go.
- If dtype crashes reappear, stop and document; do not roll forward to Sprint 1 fixes.
- Maintain device neutrality by forcing CPU (CUDA_VISIBLE_DEVICES=-1) as the plan specifies.
- Record exit code in commands.txt for reproducibility.
- Keep summary.md concise but explicit about next actions (e.g., proceed to determinism Phase A or re-open dtype plan).
- Update fix_plan.md only after artifacts are in place to avoid broken references.
Pointers:
- docs/fix_plan.md:39-55
- plans/active/test-suite-triage.md:131-140
- reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_sequence.md:17-44
- plans/active/determinism.md:1-74
- docs/development/testing_strategy.md:1-120
Next Up: If the gate is green, start Phase A tasks from plans/active/determinism.md (env capture + AT-013/024 reproductions).
