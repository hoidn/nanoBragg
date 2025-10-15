Summary: Restore CLUSTER-CREF-001 parity by making the C reference runner auto-resolve the golden binary so the triclinic vs C test passes.
Mode: Parity
Focus: docs/fix_plan.md#[TEST-SUITE-TRIAGE-002]
Branch: feature/spec-based-2
Mapped tests: tests/test_at_parallel_026.py::TestAT_PARALLEL_026_TriclinicAbsolutePosition::test_triclinic_absolute_peak_position_vs_c
Artifacts: reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CREF-001.md
Do Now: [TEST-SUITE-TRIAGE-002] CLUSTER-CREF-001 — run `NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_026.py::TestAT_PARALLEL_026_TriclinicAbsolutePosition::test_triclinic_absolute_peak_position_vs_c`
If Blocked: Capture the failing output, note the obstacle in cluster_CREF-001.md, and stop before altering runner code.
Priorities & Rationale:
- docs/fix_plan.md:39 ties Phase D launch to clearing CREF/TOOLS/CLI infrastructure blockers first.
- plans/active/test-suite-triage-rerun.md:52 Phase D table assigns cluster briefs + delegation prep for this STAMP.
- docs/development/testing_strategy.md:178 spells out NB_C_BIN precedence; parity tests must auto-find the golden binary.
- tests/test_at_parallel_026.py:147 currently asserts on `c_image is not None`; we need that guard to pass without weakening coverage.
How-To Map:
- Step 1: Reproduce the current failure with the Do Now command; copy stderr summary into cluster_CREF-001.md.
- Step 2: Update `scripts/c_reference_utils.py` so `get_default_executable_path()` honors `NB_C_BIN` first and otherwise returns an absolute repo-root fallback; ensure `validate_executable_exists` resolves symlinks before `os.access`.
- Step 3: Add a short regression note in cluster_CREF-001.md describing the new path-resolution contract and cite the doc sections above; include the exact git diff once ready for review.
- Step 4: Rerun the targeted pytest command (same as Do Now) and, if green, append command + runtime to `reports/.../cluster_CREF-001.md`; leave breadcrumbs if additional parity tests are needed.
Pitfalls To Avoid:
- Don’t hard-code machine-specific absolute paths; derive from repo root + env overrides.
- Keep the existing precedence order documented in testing_strategy (env → golden_suite_generator → root binary). 
- Avoid swallowing subprocess failures—return code mismatches must still surface.
- Do not disable `@pytest.mark.requires_c_binary`; the test should execute once the binary is found.
- Maintain ASCII-only edits and keep doc references in sync if you update behaviour.
Pointers:
- docs/fix_plan.md:39
- plans/active/test-suite-triage-rerun.md:40
- docs/development/testing_strategy.md:178
- scripts/c_reference_utils.py:227
- scripts/c_reference_runner.py:29
- tests/test_at_parallel_026.py:147
Next Up: 1) Draft cluster brief for CLI-001 (missing pix0/scaled assets) once CREF-001 is green.
