Summary: Fix weighted source normalization so PyTorch matches C when source weights differ.
Mode: Parity
Focus: SOURCE-WEIGHT-001 – Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests:
- tests/test_cli_scaling.py::TestSourceWeights::test_weighted_source_matches_c
- tests/test_cli_scaling.py::TestSourceWeights::test_uniform_weights_backward_compatible
- tests/test_cli_scaling.py::TestSourceWeights::test_edge_case_zero_sum_raises_error
- tests/test_cli_scaling.py::TestSourceWeights::test_edge_case_negative_weights_raises_error
- tests/test_cli_scaling.py::TestSourceWeights::test_single_source_fallback
Artifacts: reports/2025-11-source-weights/phase_c/<STAMP>/{implementation_notes.md,commands.txt,env.json,pytest.log}, reports/2025-11-source-weights/phase_d/<STAMP>/{pytest.log,metrics.json,env.json}
Do Now: SOURCE-WEIGHT-001 – Correct weighted source normalization; NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeights -v
If Blocked: Capture the failing command output plus `git diff` under reports/2025-11-source-weights/phase_c/<STAMP>/attempts/ and stop—do not workaround by editing tests.
Priorities & Rationale:
- plans/active/source-weight-normalization.md:35 — Phase C tasks demand a tensor-based normalization update plus regression coverage.
- docs/fix_plan.md:3965 — Next Actions call for completing C1–C3 with artifacts before dependent perf/vectorization work resumes.
- specs/spec-a-core.md:630 — AT-SRC-001 requires parity for weighted sourcefiles (Σwᵢ scaling).
- docs/development/c_to_pytorch_config_map.md:33 — Beam parameter mappings enforce weight semantics shared with the C CLI.
- tests/test_cli_scaling.py:252 — TC-A through TC-D scaffolding already expects the corrected normalization.
How-To Map:
- Keep `source_norm` as a tensor on the active device/dtype: introduce a tensor sum path without `.item()` and thread it through the scaling branch (update commentary quoting nanoBragg.c lines 2480-2595 as required by CLAUDE Rule 11).
- Revisit `_accumulate_source_contribution` only if normalization changes create double-scaling; document findings in implementation_notes.md.
- After code edits, run `pytest --collect-only -q` once, then execute `NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeights -v` (CPU). If CUDA is available, re-run with `--device cuda` via `pytest -k "TestSourceWeights and cuda"` and log outcomes.
- Write commands, env snapshot (`python -c "import json,platform,sys,torch; print(json.dumps({'python': sys.version, 'torch': torch.__version__, 'platform': platform.platform()}))"`), and metrics to the phase_c and phase_d artifact bundles (include correlation/sum_ratio numbers from TC-A failures/passes).
- Update `plans/active/source-weight-normalization.md` Phase C rows and docs/fix_plan.md Attempt history when the tests pass; reference the new artifact stamp.
Pitfalls To Avoid:
- Do not call `.item()` or `.detach()` on tensors that might need gradients later.
- Keep tensors on caller-provided device/dtype; never instantiate CPU-only scalars mid-run.
- Respect Protected Assets (no edits to docs/index.md-listed files beyond plan updates already staged).
- Leave CLI fixtures/tests intact; do not hack tolerances to mask scaling bugs.
- Ensure NB_C_BIN resolves before running TC-A; abort if the C binary is missing instead of substituting data.
- Re-run weighted-source parity only after reinstalling in editable mode if dependencies changed; avoid ad-hoc PYTHONPATH hacks.
- Capture stderr/stdout for both C and PyTorch invocations if TC-A fails; store under the same report stamp.
- Keep git worktree clean: stage only intentional changes (simulator.py, config.py if touched, tests, docs) and document in Attempts History.
- Follow docs/development/testing_strategy.md: targeted tests first, full suite only if needed after code changes.
- Preserve differentiability in any helper adjustments—no scalar branching that breaks vectorization.
Pointers:
- plans/active/source-weight-normalization.md:1 — Context and Phase breakdown for this initiative.
- docs/fix_plan.md:3953 — Ledger entry tracking SOURCE-WEIGHT-001 expectations.
- specs/spec-a-core.md:630 — Acceptance test AT-SRC-001 framing for source weighting.
- tests/test_cli_scaling.py:252 — Existing parity tests awaiting the fix.
- reports/2025-11-source-weights/phase_b/20251009T072937Z/strategy.md — Historical rationale for dividing by Σwᵢ (note our tensor-based update).
Next Up: 1) When normalization passes, re-run `scripts/validation/compare_scaling_traces.py` for the weighted fixture to refresh Phase D. 2) With SOURCE-WEIGHT-001 closed, resume VECTOR-GAPS-002 Phase B profiler capture.
