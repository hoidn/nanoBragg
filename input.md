Summary: Fix divergence auto-selection so sourcefile parity matches C and capture fresh Phase E evidence.
Mode: Parity
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling.py::TestSourceWeightsDivergence
Artifacts: reports/2025-11-source-weights/phase_e/<STAMP>/{commands.txt,pytest.log,metrics.json,warning.log,summary.md,env.json}
Do Now: docs/fix_plan.md [SOURCE-WEIGHT-001] — run `NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v`
If Blocked: Capture failing TC-D1/TC-D3 CLI outputs and update docs/fix_plan.md Attempts with hypotheses before pausing.

Priorities & Rationale
- specs/spec-a-core.md:151 — weight column ignored; CLI guard must enforce equal weighting even with divergence params.
- docs/fix_plan.md:4015 — Next Actions now require the `sourcefile` gate fix plus parity metrics.
- plans/active/source-weight-normalization.md — Phase E2/E3 flagged BLOCKED by extra divergence sources; resolving this unblocks VECTOR-GAPS-002 profiler work.
- reports/2025-11-source-weights/phase_e/20251009T115838Z/summary.md — latest evidence shows 140–300× sum_ratio after TC-D2 conversion; need new bundle post-fix.
- tests/test_cli_scaling.py:586 — TC-D2 already exercising pytest.warns; parity failures isolate the physics bug to __main__.py guard.

How-To Map
- Ensure `./golden_suite_generator/nanoBragg` is current (`make -C golden_suite_generator` if timestamps stale) so NB_C_BIN points to the instrumented binary.
- Patch `src/nanobrag_torch/__main__.py:1005` to gate divergence auto-selection on `'sourcefile' not in config`. Keep warning guard unchanged.
- Re-run `NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v` from repo root; confirm TC-D1/TC-D3 meet corr ≥0.999 and |sum_ratio−1| ≤1e-3.
- On success, archive artifacts under a fresh `reports/2025-11-source-weights/phase_e/<STAMP>/` folder (include commands.txt, pytest.log, metrics.json with CPU stats, warning.log capturing pytest.warns output, summary.md, env.json).
- Update docs/fix_plan.md Attempt history with metrics + artifact path, then advance Phase E rows in plans/active/source-weight-normalization.md.

Pitfalls To Avoid
- Do not regress TC-D2 warning behaviour; test must still detect `UserWarning` with spec citation.
- No `.cpu()` shims or `.item()` calls in physics path; keep vectorization intact.
- Respect Protected Assets (docs/index.md list) and avoid moving fixtures referenced there.
- Keep worktree focused—no full `pytest` suite; run only the mapped selector.
- Preserve device/dtype neutrality; avoid hard-coding CPU tensors or numpy conversions.
- Ensure env vars (`NB_RUN_PARALLEL`, `NB_C_BIN`, `KMP_DUPLICATE_LIB_OK`) are set when running commands.
- Maintain ASCII edits; do not touch unrelated plan items or archives.
- Record metrics immediately on failure to avoid losing evidence.
- Do not delete prior `reports/2025-11-source-weights` directories; append new timestamp only.
- Avoid rerunning divergence auto-selection with stale config caches—call `nanoBragg` via CLI per acceptance harness.

Pointers
- specs/spec-a-core.md:151
- docs/fix_plan.md:4015
- plans/active/source-weight-normalization.md:1
- src/nanobrag_torch/__main__.py:1005
- tests/test_cli_scaling.py:586
- reports/2025-11-source-weights/phase_e/20251009T115838Z/summary.md:1

Next Up
- Draft doc updates for `docs/architecture/pytorch_design.md` Sources subsection once parity bundle passes.
