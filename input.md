Summary: Reproduce and close CLUSTER-TOOLS-001 by fixing nb-compare path resolution so the dual-runner tool test passes.
Mode: Parity
Focus: [TEST-SUITE-TRIAGE-002] Next Action 6 — CLUSTER-TOOLS-001 (dual-runner tooling)
Branch: feature/spec-based-2
Mapped tests: tests/test_at_tools_001.py::TestAT_TOOLS_001_DualRunnerComparison::test_script_integration
Artifacts: reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-TOOLS-001/<STAMP>/
Do Now: Execute Next Action 6 by running `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_tools_001.py::TestAT_TOOLS_001_DualRunnerComparison::test_script_integration`, repair the nb-compare path issue, and rerun until the test passes; capture results under the cluster artifact root.
If Blocked: Capture the failing pytest.log plus `which nb-compare` output under the cluster directory and note why the path alignment cannot proceed yet in summary.md.
Priorities & Rationale:
- docs/fix_plan.md:60 — Next Action 6 sets CLUSTER-TOOLS-001 as the current blocker on TEST-SUITE-TRIAGE-002.
- plans/active/test-suite-triage-rerun.md:75 — Phase D checklist keeps this cluster open pending tooling fix.
- reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-TOOLS-001.md:1 — Cluster brief captures failure mode, reproduction command, and exit criteria.
- docs/development/testing_strategy.md:1 — Reference for reuse of validation tools and protected asset guardrails during tooling work.
How-To Map:
- `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `mkdir -p reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-TOOLS-001/$STAMP` and record commands in `commands.txt` within that folder.
- Run the reproduction once to confirm the current failure: `set -o pipefail; KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_tools_001.py::TestAT_TOOLS_001_DualRunnerComparison::test_script_integration | tee reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-TOOLS-001/$STAMP/pytest-initial.log; printf '%s\n' "${PIPESTATUS[0]}" > reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-TOOLS-001/$STAMP/exit_code_initial.txt`.
- Implement the tooling fix so `scripts/nb_compare` resolves correctly (align PATH/module invocation per cluster brief and `[TOOLING-DUAL-RUNNER-001]`).
- Re-run the same pytest selector after the fix: `set -o pipefail; KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_tools_001.py::TestAT_TOOLS_001_DualRunnerComparison::test_script_integration | tee reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-TOOLS-001/$STAMP/pytest.log; printf '%s\n' "${PIPESTATUS[0]}" > reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-TOOLS-001/$STAMP/exit_code.txt`; store environment snapshot via `env > reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-TOOLS-001/$STAMP/env.txt` and add `which nb-compare` plus any module invocation notes to `reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-TOOLS-001/$STAMP/tooling_notes.txt`.
- Update `reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-TOOLS-001/$STAMP/summary.md` with reproduction details, changes applied, and confirmation that the test now passes; include SHA256 or git hash references if assets/scripts were touched.
- When satisfied, refresh docs/fix_plan.md Attempts section with the new Attempt entry (include STAMP, results, artifacts) and mark the cluster resolved if applicable; keep `plans/active/test-suite-triage-rerun.md` consistent.
Pitfalls To Avoid:
- Do not modify or relocate protected assets (`loop.sh`, `supervisor.sh`, `input.md`).
- Keep device/dtype neutrality intact; no hard-coded `.cpu()`/`.cuda()` tweaks in tooling helpers.
- Avoid ad-hoc hacks (e.g., editing tests to skip the command); fix the script discovery contract instead.
- Preserve existing NB_C_BIN precedence and validation logic when touching tooling utilities.
- Ensure scripts remain executable on both POSIX and Windows shells (use `python -m` when appropriate).
- Capture before/after logs; do not overwrite failure evidence without archiving.
- Respect docs/findings API-001/002 context—do not regress pix0 handling when editing tooling paths.
Pointers:
- docs/fix_plan.md:60
- plans/active/test-suite-triage-rerun.md:71
- reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-TOOLS-001.md:1
- docs/development/testing_strategy.md:34
Next Up: CLUSTER-GRAD-001 diagnostics (Next Action 7) once tooling path work lands.
