Summary: Launch Sprint 1 to harden repo-root infrastructure guards (Gap 1) and stabilize nb-compare CLI tooling per Phase M next steps.
Mode: Implementation
Focus: docs/fix_plan.md#test-suite-triage-002-full-pytest-rerun-and-triage-refresh (Next Action 21 — Sprint 1 Gap 1/TOOLS remediation)
Branch: feature/spec-based-2
Mapped tests:
- pytest -vv tests/test_repo_root_fixture.py
- pytest -vv tests/test_cli_flags.py::TestPix0VectorAlias::test_pix0_vector_mm_beam_pivot[cpu]
- pytest -vv tests/test_at_tools_001.py::TestAT_TOOLS_001_DualRunnerComparison::test_script_integration
Artifacts: plans/active/test-suite-triage-phase-h/reports/20260129T044422Z/
Next Up (optional): Sprint 2 dtype reset (VEC-001) if Sprint 1 lands quickly

Do Now: Execute `docs/plans/2026-01-29-sprint1-gap1-plan.md` Tasks 1–4 in order. (1) Introduce the shared `repo_root` helper + `ensure_repo_cwd` guard inside `tests/conftest.py`, add `tests/test_repo_root_fixture.py`, and make C binary / golden asset checks consume the helper — reference `docs/development/testing_strategy.md §1.5` for authoritative NB_C_BIN precedence. (2) Refactor `tests/test_cli_flags.py` to use the new `repo_root` fixture everywhere the tests touch golden assets per `docs/architecture/c_parameter_dictionary.md` beam-center conventions; keep device/dtype guards intact. (3) Harden `tests/test_at_tools_001.py::test_script_integration` so nb-compare resolution follows `scripts/nb_compare` console script semantics from `pyproject.toml` and falls back to `sys.executable -m scripts.nb_compare`; make sure subprocess `cwd` stays at repo root. (4) Update docs/fix_plan.md Attempt history + Next Actions, append Gap 1 lesson to `docs/findings.md`, and capture STAMPed evidence (commands, pytest logs, PATH diagnostics) under `reports/2026-01-test-suite-refresh/phase_n/$STAMP/sprint1/` before committing.

If Blocked: Document the blocker (logs + diagnosis) in `reports/2026-01-test-suite-refresh/phase_n/$STAMP/sprint1/blockers.md`, update fix_plan Attempts with the failure reason, and halt implementation pending supervisor guidance.

Priorities & Rationale:
- `docs/plans/2026-01-29-sprint1-gap1-design.md`: canonical description of Gap 1 impact on CLUSTER-CREF-001 and CLUSTER-CLI-001.
- `plans/active/test-suite-triage-phase-h.md` Phase M rows: ensures Sprint sequencing remains aligned with the remediation tracker.
- `docs/development/testing_strategy.md §§1.4–1.5`: authoritative constraints for NB_C_BIN precedence, infrastructure fixtures, and environment guards.
