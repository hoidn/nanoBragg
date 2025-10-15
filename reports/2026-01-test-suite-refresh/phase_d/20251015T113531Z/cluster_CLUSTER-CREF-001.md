# Cluster CLUSTER-CREF-001 — C Reference Harness Bootstrap

## Summary
- Tests: `tests/test_at_parallel_026.py::TestAT_PARALLEL_026_TriclinicAbsolutePosition::test_triclinic_absolute_peak_position_vs_c`
- Classification: Infrastructure gap (C runner unavailable) — **Resolved in Attempt #4**
- Failure mode: Pre-fix, `scripts/c_reference_runner.py` reported `NB_C_BIN` unresolved so the parity leg never launched. Attempt #4 updated `scripts/c_reference_utils.py` to honor the precedence order (`NB_C_BIN` → golden binary → root binary), eliminating the failure.
- Evidence: `reports/2026-01-test-suite-refresh/phase_b/20251015T113531Z/pytest.log` (lines ~1892-1910) captures the original error; post-fix success verified via targeted rerun (Attempt #4 notes in `docs/fix_plan.md`).

## Reproduction Command
```bash
NB_C_BIN=./golden_suite_generator/nanoBragg \
KMP_DUPLICATE_LIB_OK=TRUE \
pytest -v tests/test_at_parallel_026.py::TestAT_PARALLEL_026_TriclinicAbsolutePosition::test_triclinic_absolute_peak_position_vs_c
```
- Guardrails: ensure the instrumented binary is present (`make -C golden_suite_generator`). If using alternative binary, update env + document in artifact.

## Downstream Plan Alignment
- Primary owner: `[TEST-GOLDEN-001]` — Golden data regeneration and C runner upkeep.
- Supporting docs: `docs/development/testing_strategy.md §2.5`, `docs/development/c_to_pytorch_config_map.md` (parity CLI guardrails).
- Related findings: Pending infrastructure note (no formal finding yet); capture decision if binary path contract changes.

## Recommended Next Actions
1. Maintain `./golden_suite_generator/nanoBragg` by rebuilding when the C sources change (`make -C golden_suite_generator`).
2. Document the precedence order in `docs/development/testing_strategy.md §2.5` (if not already captured) and ensure `scripts/c_reference_runner.py` help text mirrors the utility behavior.
3. Capture a passing reproduction log and attach it under this cluster directory for traceability the next time the suite reruns.
4. Update `[TEST-GOLDEN-001]` attempt ledger when maintenance tasks (rebuild, documentation sync) are performed.

## Exit Criteria
- Passing `pytest` invocation captured under this cluster directory with commands.txt + pytest.log verifying parity harness launches.
- `docs/fix_plan.md` reflects ongoing maintenance tasks referencing this brief and recorded Attempt #.
