Summary: Capture fresh SOURCE-WEIGHT-001 parity evidence and isolate the C segfault before rewriting the divergence test.
Mode: Docs
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling.py::TestSourceWeights::test_source_weights_ignored_per_spec, tests/test_cli_scaling.py::TestSourceWeights::test_cli_lambda_overrides_sourcefile, tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_c_divergence_reference
Artifacts: reports/2025-11-source-weights/phase_g/<STAMP>/*, reports/2025-11-source-weights/phase_h/<STAMP>/parity_reassessment.md
Do Now: Rebuild ./golden_suite_generator/nanoBragg with debug symbols, then rerun the Phase G evidence bundle (collect-only selector, targeted pytest, TC-D1 PyTorch CLI, TC-D3 C CLI) capturing full metrics; if the C command segfaults again, grab a gdb backtrace and archive it under the same STAMP before proceeding.
If Blocked: Run `NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence` and log the stderr/stdout in attempts history with the observed failure.
Priorities & Rationale:
- plans/active/source-weight-normalization.md:47-69 — Phase G refresh + new Phase H tasks demand parity metrics ≥0.999 and |sum_ratio−1| ≤3e-3 before any test rewrite.
- docs/fix_plan.md:4035-4058 — Ledger now blocks vectorization work until we log a clean Phase G attempt and parity reassessment memo.
- tests/test_cli_scaling.py:252-340 & 582-666 — Current tests still assume spec-first behaviour with an xfail marker; we need hard data before flipping it to pass.
- reports/2025-11-source-weights/phase_g/20251009T214016Z/notes.md — Last attempt documented XPASS + segfault; reproduce and extend those notes with fresh evidence.
How-To Map:
- Build: `make -C golden_suite_generator clean && make -C golden_suite_generator CFLAGS="-g -O0"`
- Pytest: `STAMP=$(date -u +%Y%m%dT%H%M%SZ); mkdir -p reports/2025-11-source-weights/phase_g/$STAMP; NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence | tee reports/2025-11-source-weights/phase_g/$STAMP/pytest.log`
- Collect log: `NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence > reports/2025-11-source-weights/phase_g/$STAMP/collect.log`
- PyTorch CLI: `KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch -sourcefile reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt -lambda 0.9768 -default_F 100 -cell 100 100 100 90 90 90 -distance 100 -detpixels 256 -pixel 0.1 -oversample 1 -phisteps 1 -mosaic_dom 1 -floatfile reports/2025-11-source-weights/phase_g/$STAMP/py_tc_d1.bin > reports/2025-11-source-weights/phase_g/$STAMP/py_stdout.txt`
- C CLI: `./golden_suite_generator/nanoBragg -sourcefile reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt -lambda 0.9768 -default_F 100 -cell 100 100 100 90 90 90 -distance 100 -detpixels_x 256 -detpixels_y 256 -pixel 0.1 -oversample 1 -phisteps 1 -mosaic_dom 1 -floatfile reports/2025-11-source-weights/phase_g/$STAMP/c_tc_d3.bin > reports/2025-11-source-weights/phase_g/$STAMP/c_stdout.txt 2>&1`
- If segfault: `gdb --batch --ex run --ex bt --args ./golden_suite_generator/nanoBragg ... | tee reports/2025-11-source-weights/phase_g/$STAMP/c_segfault/backtrace.txt`
- Metrics: use `python scripts/validation/compare_float_images.py --py reports/2025-11-source-weights/phase_g/$STAMP/py_tc_d1.bin --c reports/2025-11-source-weights/phase_g/$STAMP/c_tc_d3.bin --out reports/2025-11-source-weights/phase_g/$STAMP/correlation.txt`
Pitfalls To Avoid:
- Do not delete or overwrite prior `reports/2025-11-source-weights/phase_g/` directories; add a new STAMP per run.
- Ensure `NB_RUN_PARALLEL=1` and `KMP_DUPLICATE_LIB_OK=TRUE` are set for all pytest/CLI invocations.
- Keep the debug-built binary on the same commit; no edits to `golden_suite_generator/nanoBragg.c` unless explicitly instructed later.
- Treat `test_c_divergence_reference` as a hard failure if it still XPASSes; capture metrics before modifying tests.
- Leave generated `.bin` files out of git; only reference them from fix_plan attempts.
- Record gdb output verbatim; do not summarise without logs.
- Do not adjust tolerance thresholds until the parity memo is written.
- Avoid rerunning with stale `$STAMP`; create a new one if you need multiple passes the same loop.
- Skip doc edits until Phase H memo is drafted.
Pointers:
- plans/active/source-weight-normalization.md:47-69
- docs/fix_plan.md:4035-4058
- tests/test_cli_scaling.py:252-340
- tests/test_cli_scaling.py:582-666
- reports/2025-11-source-weights/phase_g/20251009T214016Z/notes.md
Next Up: Draft the Phase H parity reassessment memo once parity metrics and segfault triage land.
