# Cluster CLUSTER-TOOLS-001 — Dual Runner Tooling Failure

## Summary
- Tests: `tests/test_at_tools_001.py::TestAT_TOOLS_001_DualRunnerComparison::test_script_integration`
- Classification: Infrastructure gap (tooling path resolution)
- Failure mode: CLI invocation of `scripts/nb_compare` exits with code 2 because the script path is resolved relative to CWD rather than repository root.
- Evidence: `reports/2026-01-test-suite-refresh/phase_b/20251015T113531Z/pytest.log` ("No such file or directory: nb_compare" stack trace around lines 2603-2638).

## Reproduction Command
```bash
KMP_DUPLICATE_LIB_OK=TRUE \
pytest -v tests/test_at_tools_001.py::TestAT_TOOLS_001_DualRunnerComparison::test_script_integration
```
- Guard: run from repo root so `scripts/nb_compare` is discoverable; confirm `loop.sh`/`supervisor.sh` (Protected Assets) remain untouched.

## Downstream Plan Alignment
- Primary owner: `[TOOLING-DUAL-RUNNER-001]` — Restore dual-runner parity & script integration.
- Supporting docs: `scripts/validation/README.md` for canonical invocation; `docs/development/testing_strategy.md §1.5` (validation script reuse policy).
- Findings linkage: none yet; create new finding if path contract needs specification.

## Recommended Next Actions
1. Audit `scripts/nb_compare` entry-point to ensure it can be executed via `python -m` or relative path; consider packaging as console script.
2. Update `tests/test_at_tools_001.py` fixture or helper to set `PYTHONPATH`/`PATH` accordingly, aligning with `TOOLING-DUAL-RUNNER-001` plan guidance.
3. Capture successful rerun log and store under `reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-TOOLS-001/` when resolved.
4. Reflect decision in `docs/fix_plan.md` Next Actions (marking dependency unblocked).

## Exit Criteria
- Test passes locally with documented reproduction command.
- Tooling contract update committed (plan + fix_plan) referencing this brief.
- Artifacts saved (commands.txt, pytest.log) under cluster directory verifying success.
