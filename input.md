Summary: Land the SOURCE-WEIGHT Phase E warning guard and parity evidence so VECTOR-GAPS can unblock.
Mode: Parity
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests:
- pytest --collect-only -q
- NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v
Artifacts:
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/commands.txt
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/summary.md
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/metrics.json
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/pytest_collect.log
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/pytest.log
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/warning.log
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/env.json
Do Now: [SOURCE-WEIGHT-001] Phase E — replace the stderr print with a spec-citing `warnings.warn` guard in `src/nanobrag_torch/__main__.py`, re-enable TC-D2 with `pytest.warns`, then run `NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v`
If Blocked: Capture TC-D1/TC-D3 CLI outputs with the pre-guard binary, stash stdout/stderr under `reports/2025-11-source-weights/phase_e/<UTCSTAMP>/attempts/`, and log the blocker plus metrics in docs/fix_plan.md before pausing.
Priorities & Rationale:
- specs/spec-a-core.md:144-162 — normative rule that source weights are read but ignored; warning text must cite this block.
- plans/active/source-weight-normalization.md:1-200 — Phase E checklist describing guard placement, parity metrics, and documentation follow-through.
- docs/fix_plan.md:4015-4029 — Next Actions demand warning guard + TC-D2 activation before VECTOR-GAPS-002 resumes.
- reports/2025-11-source-weights/phase_d/20251009T103212Z/design_notes.md — Option B decision memo with acceptance thresholds and guard wording.
- src/nanobrag_torch/__main__.py:718-744 — Current CLI guard uses stderr print; must switch to `warnings.warn(..., stacklevel=2)` and keep divergence detection logic intact.
- tests/test_cli_scaling.py:472-704 — TC-D1…D4 scaffolding ready; TC-D2 needs `pytest.warns(UserWarning)` once guard emits correctly.
How-To Map:
1. Export `KMP_DUPLICATE_LIB_OK=TRUE` and `NB_RUN_PARALLEL=1`; set `NB_C_BIN=./golden_suite_generator/nanoBragg` so CLI parity uses the instrumented binary.
2. Edit `src/nanobrag_torch/__main__.py`: replace the stderr `print` with `warnings.warn("Divergence/dispersion parameters ignored when sourcefile is provided. Sources are loaded from file only (see specs/spec-a-core.md:151-162).", UserWarning, stacklevel=2)` and keep the divergence/dispersion detection list unchanged.
3. Update `tests/test_cli_scaling.py::TestSourceWeightsDivergence.test_sourcefile_divergence_warning` to drop the skip, wrap the subprocess invocation in `with pytest.warns(UserWarning) as record:` and assert the warning string fragments from the captured record; continue verifying exit code and output file.
4. Stamp a fresh reports folder (`STAMP=$(date -u +%Y%m%dT%H%M%SZ)`), tee all commands into the listed artifact files, and record the exact guard message in `warning.log`.
5. Run `pytest --collect-only -q | tee reports/2025-11-source-weights/phase_e/$STAMP/pytest_collect.log` to prove selectors still load.
6. Execute `NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v | tee reports/2025-11-source-weights/phase_e/$STAMP/pytest.log`, ensuring TC-D2 captures the warning via `pytest.warns` and other cases hit the parity checks.
7. Re-run the Phase D3 CLI bundle (commands.txt) with explicit `-oversample 1` for both C and PyTorch; pipe stderr to `warning.log`, keep stdout binaries, and compute correlation/sum-ratio via the existing Python snippet, saving values in `metrics.json` and the narrative `summary.md`.
8. Capture environment metadata (`python - <<'PY' ...`) into `env.json`, then update docs/fix_plan.md attempt history and mark plan Phase E1/E2/E3 progress referencing the new timestamp.
Pitfalls To Avoid:
- Do not touch simulator physics loops; guard lives in CLI parsing only.
- Warning string must retain the spec citation verbatim so TC-D2 assertions stay stable.
- Use `warnings.warn` with `stacklevel=2`; leaving the stderr print will keep TC-D2 skipped.
- Ensure `pytest.warns` inspects `record[0].message.args[0]` before asserting fragments; avoid brittle stderr parsing.
- Maintain ASCII artifacts; no Unicode in summary/metrics files.
- Keep NB_RUN_PARALLEL set, otherwise parity tests skip and metrics won't be captured.
- Preserve protected assets listed in docs/index.md; do not relocate fixtures under reports/.
- Record both commands and results; missing env.json or metrics.json will block closure.
- Avoid `.item()` or device shims when editing CLI glue; guard must be device/dtype neutral.
- No full pytest suite this loop; stick to the mapped selectors.
Pointers:
- specs/spec-a-core.md:144-162
- plans/active/source-weight-normalization.md:1-220
- docs/fix_plan.md:4015-4045
- src/nanobrag_torch/__main__.py:718-744
- tests/test_cli_scaling.py:472-704
- reports/2025-11-source-weights/phase_d/20251009T104310Z/commands.txt
Next Up: After parity evidence lands, update docs/architecture/pytorch_design.md Sources section and notify `[VECTOR-GAPS-002]` per plan Phase E4/F1.
