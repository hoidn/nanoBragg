Summary: Capture a fresh Phase G evidence bundle with the correct C CLI flags, document the XPASS metrics, and prep the parity reassessment gate.
Mode: Docs+Parity
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling.py::TestSourceWeights::test_source_weights_ignored_per_spec, tests/test_cli_scaling.py::TestSourceWeights::test_cli_lambda_overrides_sourcefile, tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_c_divergence_reference
Artifacts: reports/2025-11-source-weights/phase_g/<STAMP>/*, reports/2025-11-source-weights/phase_h/<STAMP>/parity_reassessment.md
Do Now: [SOURCE-WEIGHT-001] Phase G2 evidence bundle — NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence
If Blocked: Capture `pytest --collect-only -q` output for the two classes, log the failure mode (XPASS, segfault, or CLI error) in attempts history with pointers to the partial artifacts, and halt before modifying tests.
Priorities & Rationale:
- plans/active/source-weight-normalization.md:47 — Phase G2 expects a new evidence bundle before Phase H unblocks; we must gather production-ready artifacts.
- docs/fix_plan.md:4051 — The fix plan now demands correlation ≥0.999 or a documented anomaly plus the corrected `-mosaic_domains` flag usage.
- reports/2025-11-source-weights/phase_g/20251009T214016Z/notes.md:1 — Last bundle recorded XPASS + segfault; replicate with correct commands and extend the notes.
- reports/2025-11-source-weights/phase_f/20251009T203823Z/commands.txt:75 — Authoritative CLI command set for TC-Spec and TC-C runs; reuse with corrected flag spelling and STAMP-scoped working dir.
- specs/spec-a-core.md:151 — Spec still mandates weights are ignored; parity evidence must confirm this before we rewrite the test expectation.
How-To Map:
- `repo_root=$(git rev-parse --show-toplevel)`; `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `BASE=$repo_root/reports/2025-11-source-weights/phase_g/$STAMP`; `mkdir -p "$BASE"/logs "$BASE"/cli`.
- Collect-only proof: `NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence > "$BASE"/logs/collect.log`.
- Targeted pytest: `NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence | tee "$BASE"/logs/pytest.log`; expect `test_c_divergence_reference` to XPASS — keep the full output.
- PyTorch CLI runs from the evidence dir: `pushd "$BASE"/cli; KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch -sourcefile "$repo_root/reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt" -lambda 0.9768 -default_F 100 -cell 100 100 100 90 90 90 -distance 100 -detpixels 256 -pixel 0.1 -oversample 1 -phisteps 1 -mosaic_dom 1 -floatfile py_tc_weighted.bin > py_tc_weighted_stdout.txt 2>&1; popd`.
- Equal-weight comparison (spec check): create `equal_sources.txt` inside `$BASE/cli`, rerun the PyTorch CLI with that file, then run a short python snippet (store as `spec_metrics.py`) to compute sum ratio, correlation, and NaN counts; write JSON to `$BASE/cli/metrics_spec.json`.
- C vs PyTorch reference: `pushd "$BASE"/cli; "$repo_root/golden_suite_generator/nanoBragg" -sourcefile "$repo_root/reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt" -lambda 0.9768 -default_F 100 -cell 100 100 100 90 90 90 -distance 100 -detpixels_x 256 -detpixels_y 256 -pixel 0.1 -oversample 1 -phisteps 1 -mosaic_domains 1 -floatfile c_tc_weighted.bin > c_tc_weighted_stdout.txt 2>&1; popd` followed by a matching PyTorch run (same args, output `py_tc_weighted_for_c.bin`).
- Metrics + NaN audit: within `$BASE/cli`, run `python - <<'PY'` to load both `.bin` files, compute sums, correlation, and `np.isnan` counts; save to `metrics_c_compare.json` and dump a human-readable summary to `notes.md`.
- Archive commands and environment: append each executed CLI string to `$BASE/commands.txt`; copy `env` output to `$BASE/env.txt`.
- If the C floatfile contains NaNs or the command segfaults, gather a `gdb --batch --ex run --ex bt --args ...` trace into `$BASE/cli/c_segfault/backtrace.txt` and mention it in `notes.md`.
Pitfalls To Avoid:
- Do not run the CLI commands from repo root; stay in `$BASE/cli` so auxiliary SMV/PGM outputs remain scoped.
- Use `-mosaic_domains` for the C binary; the PyTorch-only `-mosaic_dom` alias triggered the prior segfault/NaN metrics.
- Keep every `.bin`, stdout/stderr, and JSON out of git; leave them on disk and reference paths in fix_plan attempts.
- Always export `KMP_DUPLICATE_LIB_OK=TRUE` and keep `NB_RUN_PARALLEL=1` for the divergence test.
- Do not edit tests or docs until Phase H; this loop is evidence-only.
- If pytest XPASSes again, do not remove the xfail marker; simply log metrics and halt.
- Ensure the python metrics snippet guards against division by zero and reports NaN counts explicitly.
- Rebuild the C binary first if the executable is missing or stale (`make -C golden_suite_generator clean && make -C golden_suite_generator CFLAGS="-g -O0"`).
- Avoid deleting prior `phase_g` directories; each run needs a fresh STAMP.
- Skip full-suite pytest; targeted selectors only.
Pointers:
- plans/active/source-weight-normalization.md:47
- docs/fix_plan.md:4051
- reports/2025-11-source-weights/phase_g/20251009T214016Z/notes.md:1
- reports/2025-11-source-weights/phase_f/20251009T203823Z/commands.txt:75
- specs/spec-a-core.md:151
Next Up: Draft the Phase H parity reassessment memo once the new bundle confirms the true C vs PyTorch behaviour.
