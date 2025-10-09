Summary: Capture weighted-source parity evidence to unblock the vectorization relaunch.
Mode: Perf
Focus: VECTOR-TRICUBIC-002 / Vectorization relaunch backlog
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q; pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v
Artifacts: reports/2025-11-source-weights/phase_e/<STAMP>/ {commands.txt, summary.md, env.json, correlation.txt, sum_ratio.txt, pytest.log}
Do Now: SOURCE-WEIGHT-001 — Correct weighted source normalization; run NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v
If Blocked: If the pytest node passes but metrics still diverge, rerun the PyTorch-only CLI (`nanoBragg ... -sourcefile`) and capture stdout/stderr to reports/2025-11-source-weights/phase_e/<STAMP>/py_only.log before attempting the C parity step.
Priorities & Rationale:
- plans/active/vectorization.md — Phase A requires SOURCE-WEIGHT-001 parity before profiling resumes.
- docs/fix_plan.md — VECTOR-TRICUBIC-002 Next Actions hinge on corr ≥0.999, |sum_ratio−1| ≤1e-3 evidence.
- plans/active/source-weight-normalization.md — Phase E2/E3 outline the diagnostics and parity commands we must execute now.
- specs/spec-a-core.md — Sources §4 mandates that weights are read but ignored, so parity must reflect equal weighting.
How-To Map:
- Export env vars: `export KMP_DUPLICATE_LIB_OK=TRUE; export NB_RUN_PARALLEL=1; export NB_C_BIN=./golden_suite_generator/nanoBragg` (fallback ./nanoBragg).
- Preflight: `pytest --collect-only -q` (store log as collect.log under reports/<STAMP>/).
- Targeted test: `NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v | tee reports/2025-11-source-weights/phase_e/<STAMP>/pytest.log`.
- PyTorch CLI (TC-D1): run command from reports/2025-11-source-weights/phase_d/20251009T104310Z/commands.txt with `-oversample 1`, writing outputs to /tmp/py_tc_d1.bin; capture stdout→reports/<STAMP>/py_tc_d1.log.
- C CLI (TC-D1): run matching `$NB_C_BIN` command saving /tmp/c_tc_d1.bin; log stderr/stdout.
- Metrics: use provided Python snippet to compute correlation/sum_ratio; record outputs into `correlation.txt` and `sum_ratio.txt`.
- Repeat PyTorch-only TC-D2 to confirm `UserWarning`; append to summary.md.
- Archive commands/env: copy executed commands into `commands.txt`; run `python - <<'PY'` block to dump os.environ and git SHA into `env.json`.
Pitfalls To Avoid:
- Do not modify production code; this loop is evidence-only.
- Respect Protected Assets (do not move/delete files listed in docs/index.md).
- Keep tensors on caller device; no `.cpu()`/`.cuda()` in ad-hoc scripts.
- Use `-oversample 1` explicitly to match C baseline and avoid auto-selection drift.
- Ensure `/tmp/*.bin` cleanup only after metrics recorded; avoid git-adding binaries.
- Log every command executed; missing artifacts will block plan Phase A closure.
- Skip full test suite; only run mapped selectors.
- Do not rely on prior timestamps; create a new ISO8601 UTC directory under phase_e/.
- Verify `NB_C_BIN` points to a built binary before running commands.
- Capture warning output for TC-D2; failing to prove the guard fires will keep Phase E blocked.
Pointers:
- plans/active/vectorization.md
- plans/active/source-weight-normalization.md
- docs/fix_plan.md
- specs/spec-a-core.md
- reports/2025-11-source-weights/phase_d/20251009T104310Z/commands.txt
Next Up: Vectorization refresh benchmarks (plans/active/vectorization.md Phase B) once parity evidence lands.
