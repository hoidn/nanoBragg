# Cluster CLUSTER-CLI-001 — Missing CLI Golden Assets

## Summary
- Tests: `tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot[cpu]` and `tests/test_cli_flags.py::TestHKLFdumpParity::test_scaled_hkl_roundtrip`
- Classification: Infrastructure gap (missing golden artifacts)
- Failure mode: Tests expect `tests/golden_data/pix0_expected.json` and `tests/golden_data/scaled.hkl`; assets are absent so fixtures error before assertions.
- Evidence: `reports/2026-01-test-suite-refresh/phase_b/20251015T113531Z/pytest.log` (FileNotFoundError entries around lines 2135-2230).

## Reproduction Command
```bash
KMP_DUPLICATE_LIB_OK=TRUE \
pytest -v tests/test_cli_flags.py -k "pix0_vector_mm_beam_pivot or scaled_hkl_roundtrip"
```

## Downstream Plan Alignment
- Primary owner: `[CLI-FLAGS-003]` — Handle `-nonoise` and `-pix0_vector_mm` CLI parity.
- Supporting docs: `docs/development/testing_strategy.md §2.3` (Golden data regeneration), `docs/development/c_to_pytorch_config_map.md` (beam center & pix0 semantics).
- Related findings: `API-001`, `API-002` (pix0 unit/override bugs) — ensure fixes reference these findings before closure.

## Recommended Next Actions
1. Regenerate missing golden assets using commands in `tests/golden_data/README.md` (ensure `NB_C_BIN` set). Document outputs under `tests/golden_data/` and capture sha256 in this cluster directory.
2. Update `tests/test_cli_flags.py` fixtures if path expectations change; keep Protected Assets rule in mind (`docs/index.md`).
3. Once assets restored, rerun the reproduction command and store passing `pytest.log` under cluster directory.
4. Update `[CLI-FLAGS-003]` entry in `docs/fix_plan.md` with regeneration steps + asset verification.

## Exit Criteria
- Golden assets committed with provenance documented (commands.txt + sha256sum in cluster directory).
- Tests above pass on CPU; results archived under this cluster directory.
- Findings `API-001/002` annotated with remediation status (if resolved) or updated rationale.
