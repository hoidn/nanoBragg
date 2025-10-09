Summary: Finish SOURCE-WEIGHT Phase E by landing the CLI warning guard, reactivating TC-D2, and capturing parity metrics so VECTOR-GAPS-002 can resume.
Mode: Parity
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests:
- pytest --collect-only -q
- pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v
Artifacts:
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/commands.txt
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/summary.md
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/metrics.json
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/pytest.log
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/pytest_collect.log
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/warning.log
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/env.json
Do Now: [SOURCE-WEIGHT-001] Phase E — implement the Option B CLI warning guard, remove the TC-D2 skip, then run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v`
If Blocked: Capture TC-D1/TC-D3 CLI outputs with the current simulator, stash binaries+stdout under reports/2025-11-source-weights/phase_e/<UTCSTAMP>/attempts/, and log blocker context + metrics in docs/fix_plan.md before pausing.
Priorities & Rationale:
- specs/spec-a-core.md:144-162 — spec makes the “weight column is read but ignored” rule; warning message must cite this range.
- plans/active/source-weight-normalization.md:1-120 — Phase E checklist defines guard location, tests, and parity tolerances we must satisfy.
- docs/fix_plan.md:4015-4029 — Next Actions demand Phase E1–E3 guard + metrics and Phase E4 doc updates before unblocking profiling.
- reports/2025-11-source-weights/phase_d/20251009T103212Z/design_notes.md — Option B decision memo spells out warning wording and acceptance gates.
- tests/test_cli_scaling.py:472-648 — TC-D1…D4 scaffolding already exists; TC-D2 must swap string matching for `pytest.warns` once the guard emits correctly.
- docs/development/testing_strategy.md:1-120 — authoritative command sourcing; keep run cadence to targeted selectors before any broader smoke.
How-To Map:
1. `export KMP_DUPLICATE_LIB_OK=TRUE` and set `NB_C_BIN=./golden_suite_generator/nanoBragg`; record both in env.json.
2. In `src/nanobrag_torch/__main__.py`, hook the CLI parser: when `--sourcefile` appears with any of `-hdivrange/-vdivrange/-dispersion`, call `warnings.warn("Divergence/dispersion parameters ignored when sourcefile is provided. Sources are loaded from file only (see specs/spec-a-core.md:151-162).", UserWarning, stacklevel=2)` and keep simulator inputs untouched.
3. Update `tests/test_cli_scaling.py::TestSourceWeightsDivergence.test_sourcefile_divergence_warning` to remove the skip and assert the warning via `with pytest.warns(UserWarning) as record:` plus string containment checks; keep TC-D1/D3/D4 logic unchanged.
4. Stamp a reports directory (`STAMP=$(date -u +%Y%m%dT%H%M%SZ)`) and tee every command to files listed above (`commands.txt`, `pytest_collect.log`, `pytest.log`, `warning.log`).
5. Run `pytest --collect-only -q | tee reports/2025-11-source-weights/phase_e/$STAMP/pytest_collect.log` to prove selector discovery.
6. Execute `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v | tee reports/2025-11-source-weights/phase_e/$STAMP/pytest.log` and ensure TC-D2 reports the captured warning.
7. Re-run the CLI bundle from `reports/2025-11-source-weights/phase_d/20251009T104310Z/commands.txt`, redirecting outputs into the new reports folder (e.g. `... > reports/.../tc_d1_py.stdout`, capture the warning via `2>&1 | tee reports/.../warning.log`).
8. Compute correlation/sum-ratio for TC-D1 and TC-D3 with a short Python snippet, dump into `metrics.json`, and summarise results plus warning text in `summary.md` alongside any skipped CUDA rationale.
9. Capture environment metadata (`python - <<'PY' ...`) into env.json, then update docs/fix_plan.md attempts and the plan Phase E rows referencing the new timestamp before finishing.
Pitfalls To Avoid:
- Do not edit simulator physics loops—guard lives in CLI parsing only.
- Warning string must include the spec citation verbatim; losing it breaks TC-D2 expectations.
- Use `warnings.warn(..., stacklevel=2)` so tests see the guard; avoid printing manually.
- Keep NB_RUN_PARALLEL requirements satisfied (skip gracefully if the env var is missing, but document it in summary.md).
- No full pytest suite this loop; stick to the mapped selectors.
- Preserve fixtures under reports/2025-11-source-weights/; do not relocate or rename protected assets listed in docs/index.md.
- Log all commands/outputs in ASCII; avoid adding `.item()` or device-specific hacks when touching CLI glue.
- Remember to add the new attempt entry and plan updates—vectorization profiling stays blocked until you do.
Pointers:
- specs/spec-a-core.md:144-162
- plans/active/source-weight-normalization.md:1-200
- docs/fix_plan.md:4015-4029
- tests/test_cli_scaling.py:472-648
- reports/2025-11-source-weights/phase_d/20251009T104310Z/commands.txt
- docs/development/testing_strategy.md:1-120
Next Up (optional): After parity artifacts land, tackle Phase E4 documentation updates and notify `[VECTOR-GAPS-002]` so profiler work can restart.
