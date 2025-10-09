Summary: Capture SOURCE-WEIGHT-001 Phase D parity evidence so the 4096² profiler can trust multi-source metrics again.
Mode: Parity
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization — Phase D parity capture
Branch: feature/spec-based-2
Mapped tests: NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeights::test_weighted_source_matches_c -v; pytest --collect-only -q
Artifacts: reports/2025-11-source-weights/phase_d/<STAMP>/commands.txt; reports/2025-11-source-weights/phase_d/<STAMP>/pytest/pytest.log; reports/2025-11-source-weights/phase_d/<STAMP>/cli/c_stdout.log; reports/2025-11-source-weights/phase_d/<STAMP>/cli/py_stdout.log; reports/2025-11-source-weights/phase_d/<STAMP>/cli/c_weight.bin; reports/2025-11-source-weights/phase_d/<STAMP>/cli/py_weight.bin; reports/2025-11-source-weights/phase_d/<STAMP>/metrics.json; reports/2025-11-source-weights/phase_d/<STAMP>/summary.md; reports/2025-11-source-weights/phase_d/<STAMP>/env.json
Do Now: [SOURCE-WEIGHT-001] Phase D1 — run `pytest --collect-only -q`, export `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and `OUTDIR=reports/2025-11-source-weights/phase_d/$STAMP`, then execute `NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeights::test_weighted_source_matches_c -v | tee $OUTDIR/pytest/pytest.log`, followed by C & PyTorch CLI runs with `-oversample 1` (see How-To Map) to populate metrics.
If Blocked: Capture stdout/stderr and exit codes under `$OUTDIR/blocking.md`, append the failing command to `commands.txt`, and log the failure as a new Attempt in docs/fix_plan.md before stopping.
Priorities & Rationale:
- plans/active/source-weight-normalization.md:11-55 keeps Phase D open; without the parity bundle `[VECTOR-GAPS-002]` remains blocked.
- docs/fix_plan.md:4015-4099 now marks SOURCE-WEIGHT-001 in_progress and requires Phase D evidence before resuming 4096² profiling.
- specs/spec-a-core.md:151 mandates “weight column is read but ignored,” so the authoritative parity test must prove the equal-weight behaviour end-to-end.
- tests/test_cli_scaling.py:253-386 encodes the weighted-source regression; rerunning it with NB_RUN_PARALLEL=1 establishes a trustworthy baseline.
- docs/development/testing_strategy.md:1-70 insists on CPU parity proof with explicit env logging before any performance sampling.
How-To Map:
- Export `AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md` and append every command (timestamp + text) to `$OUTDIR/commands.txt` via `printf` so provenance survives audits.
- Run `pytest --collect-only -q | tee reports/2025-11-source-weights/phase_d/$STAMP/pytest_collect.log` immediately after defining `$STAMP`/`$OUTDIR`; confirm exit 0.
- Execute the parity selector with env vars: `NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeights::test_weighted_source_matches_c -v | tee $OUTDIR/pytest/pytest.log`; capture exit code in `commands.txt`.
- Reuse the fixture at `reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt`. For the C run:
  `"$NB_C_BIN" -mat A.mat -floatfile $OUTDIR/cli/c_weight.bin -sourcefile reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -oversample 1 -nonoise -nointerpolate > $OUTDIR/cli/c_stdout.log 2>&1`.
- For the PyTorch run:
  `KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch -mat A.mat -floatfile $OUTDIR/cli/py_weight.bin -sourcefile reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -oversample 1 -nonoise -nointerpolate > $OUTDIR/cli/py_stdout.log 2>&1`.
- Capture environment data: `python - <<'PY'` (dump python/torch versions, git SHA) into `$OUTDIR/env.json`, and `python -m torch.utils.collect_env > $OUTDIR/torch_env.txt`.
- Generate metrics: `python - <<'PY'` with `numpy.fromfile` to calculate totals, maxima, sum_ratio, and Pearson correlation; write the result to `$OUTDIR/metrics.json` and echo the correlation line for quick review.
- Summarise findings in `$OUTDIR/summary.md` (include command list, correlation, sum_ratio, and confirmation that `-oversample 1` was explicit) and update docs/fix_plan.md with Attempt #7 completion details referencing the new directory.
Pitfalls To Avoid:
- Do not reuse legacy 20251009 directories; every run must use a fresh UTC `$STAMP`.
- Keep `-oversample 1` on both CLI invocations; omitting it recreates the auto-selection mismatch that caused 52× divergence.
- Ensure NB_RUN_PARALLEL=1 and NB_C_BIN point to `./golden_suite_generator/nanoBragg`; otherwise pytest will skip the parity test and the evidence is invalid.
- Do not move or modify files listed in docs/index.md (especially fixtures and loop scripts).
- No edits to production code during this evidence loop; parity proof only.
- Store binary outputs under `$OUTDIR/cli/`; avoid leaving large temp files in /tmp — remove them or capture paths in commands.txt.
- Maintain device/dtype neutrality: run everything on CPU float32; don’t add `.cpu()` calls to scripts.
- Record exit codes after every command; mismatched return codes without documentation will invalidate the attempt.
- If correlation <0.99 or sum_ratio deviates >5e-3, stop and log the anomaly rather than proceeding to profiler work.
- Leave input.md untouched; only galph edits this file.
Pointers:
- plans/active/source-weight-normalization.md:11-56 — Phase D checklist and gating notes.
- docs/fix_plan.md:4015-4099 — Ledger context and updated Next Actions for SOURCE-WEIGHT-001.
- specs/spec-a-core.md:145-165 — Normative statement that weights are ignored.
- tests/test_cli_scaling.py:253-386 — Regression test exercising the weighted-source path.
- docs/development/testing_strategy.md:1-120 — Authoritative commands and parity expectations.
Next Up: Once Phase D artifacts land, resume `[VECTOR-GAPS-002]` Phase B1 profiler rerun with the refreshed parity metrics.
