Summary: Stage the Phase D3 acceptance harness for weighted-source divergence so Phase E implementation can proceed.
Mode: Docs
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q; pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v
Artifacts: reports/2025-11-source-weights/phase_d/<STAMP>/{commands.txt,summary.md,pytest_collect.log,pytest_TestSourceWeightsDivergence.log,warning_capture.log}
Do Now: [SOURCE-WEIGHT-001] Phase D3 acceptance harness — KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v
If Blocked: Record the failure details in summary.md, stash stdout/stderr into the log files above, then run KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q and document the outcome in attempts history.
Priorities & Rationale:
- specs/spec-a-core.md:151 anchors the "weights ignored" rule we must cite in the harness summary.
- plans/active/source-weight-normalization.md:11 escalates Phase D3 now that Option B is locked.
- docs/fix_plan.md:4027 sets D3 deliverables (commands.txt, pytest logs, summary metrics) before Phase E may start.
- reports/2025-11-source-weights/phase_d/20251009T103212Z/design_notes.md:1 documents Option B requirements we must mirror in the harness.
- docs/development/testing_strategy.md:40 reminds us to capture authoritative selectors and device notes inside the artifact bundle.
-How-To Map:
- export STAMP=$(date -u +%Y%m%dT%H%M%SZ) and mkdir -p reports/2025-11-source-weights/phase_d/$STAMP/ before any commands.
- Tee every shell command into reports/2025-11-source-weights/phase_d/$STAMP/commands.txt for reproducibility.
- Run KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q | tee reports/2025-11-source-weights/phase_d/$STAMP/pytest_collect.log to prove selectors load; annotate skipped modules in summary.md.
- Execute the targeted test command from Do Now, even if it fails, and pipe output to reports/2025-11-source-weights/phase_d/$STAMP/pytest_TestSourceWeightsDivergence.log; note the result (missing test vs failure) in summary.md.
- Draft warning_capture.log in reports/2025-11-source-weights/phase_d/$STAMP/ by noting the expected UserWarning text from Option B and whether it exists today ("pending implementation" is acceptable); state acceptance metrics (corr ≥0.999, |sum_ratio-1| ≤1e-3, warning observed) in summary.md with checkboxes.
- Summarise next execution steps for Phase E (spec patch, BeamConfig guard, regression tests) and reference the design notes and plan rows explicitly.
Pitfalls To Avoid:
- Do not touch production code or specs yet; D3 is documentation-only.
- Keep all new files within the timestamped reports directory; no stray artifacts in repo root.
- Do not run C or PyTorch CLI simulations yet—those belong to Phase E metrics.
- Avoid renaming any assets listed in docs/index.md or moving existing fixtures.
- Capture full pytest output even on failure; do not trim logs.
- Respect device neutrality: never hard-code .cpu()/.cuda() in examples.
- Do not delete the prior D1/D2 report folders; link to them from summary.md instead.
- Ensure NB_C_BIN remains unset or pointing to a valid binary; do not modify environment defaults in scripts.
- Maintain Option B framing—no new divergence-handling ideas unless flagged as future work.
Pointers:
- specs/spec-a-core.md:151
- plans/active/source-weight-normalization.md:11
- docs/fix_plan.md:4027
- reports/2025-11-source-weights/phase_d/20251009T103212Z/design_notes.md:1
- docs/development/testing_strategy.md:40
Next Up: Phase E1–E4 implementation once the D3 harness bundle is committed.
