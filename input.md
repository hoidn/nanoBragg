Summary: Capture SOURCE-WEIGHT Phase E parity evidence after converting TC-D2 to pytest.warns.
Mode: Parity
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests:
- pytest --collect-only -q
- NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v
Artifacts:
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/commands.txt
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/summary.md
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/metrics.json
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/warning.log
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/pytest_collect.log
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/pytest.log
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/env.json
Do Now: [SOURCE-WEIGHT-001] Phase E — switch TC-D2 to in-process pytest.warns, then run NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v and archive the TC-D1/D3 parity metrics under reports/2025-11-source-weights/phase_e/<UTCSTAMP>/
If Blocked: If the instrumented C binary is missing or fails to build, capture the `make -C golden_suite_generator` output under `reports/2025-11-source-weights/phase_e/<UTCSTAMP>/build.log`, switch NB_C_BIN=./nanoBragg, rerun the parity CLI bundle, and document the fallback in docs/fix_plan.md Attempts.
Priorities & Rationale:
- specs/spec-a-core.md:144-162 — normative statement that source weights are read but ignored; warning text must cite this block verbatim.
- plans/active/source-weight-normalization.md:1-220 — Phase E checklist now marks E1 done; E2/E3 require pytest.warns plus fresh parity metrics before VECTOR-GAPS unlocks.
- docs/fix_plan.md:4015-4045 — Next Actions call for TC-D2 pytest.warns + correlation evidence ≥0.999 with |sum_ratio−1| ≤1e-3.
- reports/2025-11-source-weights/phase_d/20251009T104310Z/commands.txt — Authoritative CLI bundle for TC-D1/D2/D3/D4 reproduction.
- reports/2025-11-source-weights/phase_e/20251009T114620Z/summary.md — Prior guard implementation evidence; new run must supersede these metrics.
- src/nanobrag_torch/__main__.py:720-755 — Warning guard implemented in commit 3140629; tests must assert this warning in-process.
How-To Map:
1. Build the instrumented C binary if absent: `make -C golden_suite_generator | tee reports/2025-11-source-weights/phase_e/$STAMP/build.log`; export `NB_C_BIN=./golden_suite_generator/nanoBragg` (fallback `./nanoBragg` if build unavailable).
2. Convert `tests/test_cli_scaling.py::TestSourceWeightsDivergence.test_sourcefile_divergence_warning` to call `nanobrag_torch.__main__.main()` inside `with pytest.warns(UserWarning) as record:`; use `monkeypatch`/`pytest` fixtures to set `sys.argv` and a temporary output path so no subprocess is needed.
3. Stamp `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; create `reports/2025-11-source-weights/phase_e/$STAMP/` and tee every command into `reports/2025-11-source-weights/phase_e/$STAMP/commands.txt` while saving pytest logs to the listed files.
4. Run `pytest --collect-only -q | tee reports/2025-11-source-weights/phase_e/$STAMP/pytest_collect.log` to prove selectors load after the test update.
5. Execute `NB_RUN_PARALLEL=1 NB_C_BIN=$NB_C_BIN KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v | tee reports/2025-11-source-weights/phase_e/$STAMP/pytest.log`; ensure TC-D1/D3/D4 hit the correlation/sum_ratio gates, and TC-D2 asserts the exact warning text (check `record[0].message.args[0]`).
6. Reproduce the Phase D3 CLI bundle (TC-D1/TC-D3 at minimum) with explicit `-oversample 1`; dump stderr to `reports/2025-11-source-weights/phase_e/$STAMP/warning.log`, store float images, and compute correlation/sum_ratio using the python snippet from commands.txt. Write metrics (including pass/fail booleans) to `reports/2025-11-source-weights/phase_e/$STAMP/metrics.json` plus a narrative `reports/2025-11-source-weights/phase_e/$STAMP/summary.md`.
7. Capture `env.json` with Python, PyTorch, NB_C_BIN, NB_RUN_PARALLEL, and git SHA; update docs/fix_plan.md Attempts and the plan Phase E rows referencing the new timestamp.
Pitfalls To Avoid:
- Do not regress the warning message or remove the spec citation; TC-D2 asserts exact fragments.
- `pytest.warns` only works in-process—avoid falling back to subprocess stderr parsing.
- Ensure the C binary really matches the CLI harness; stale builds will corrupt parity metrics.
- Keep metrics recording even on pass (write JSON + summary regardless) so downstream plans have evidence.
- Maintain ASCII-only artifact files; avoid Unicode punctuation in summary.md.
- Preserve device/dtype neutrality; no `.item()` or device-specific casts in test updates.
- Respect Protected Assets (docs/index.md); do not move fixtures out of reports/.
- Set `KMP_DUPLICATE_LIB_OK=TRUE` and `NB_RUN_PARALLEL=1` for every parity command; missing env vars will skip the suite.
- Clean temporary files in pytest tests using `tmp_path`; prevent writes into repo root.
- Do not run the full pytest suite this loop—stick to mapped selectors.
Pointers:
- specs/spec-a-core.md:144-162
- plans/active/source-weight-normalization.md: Status snapshot & Phase E table
- docs/fix_plan.md:4015-4045
- src/nanobrag_torch/__main__.py:720-755
- tests/test_cli_scaling.py:472-704
- reports/2025-11-source-weights/phase_d/20251009T104310Z/commands.txt
Next Up: After metrics land, patch docs/architecture/pytorch_design.md Sources section and notify `[VECTOR-GAPS-002]` to resume profiling.
