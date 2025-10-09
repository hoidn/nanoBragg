Summary: Capture CUDA parity + performance evidence for the vectorized tricubic/absorption path so Phase H can close cleanly.
Mode: Perf
Focus: [VECTOR-TRICUBIC-001] Vectorize tricubic interpolation and detector absorption
Branch: feature/spec-based-2
Mapped tests: pytest tests/test_tricubic_vectorized.py -v -k cuda | pytest tests/test_at_abs_001.py -v -k cuda
Artifacts: reports/2025-10-vectorization/phase_h/<STAMP>/{commands.txt,env.json,pytest_logs/,benchmarks/,summary.md}
Do Now: [VECTOR-TRICUBIC-001] Vectorize tricubic interpolation and detector absorption — run KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py -v -k cuda
If Blocked: Save failing command, traceback, and `torch.cuda.is_available()` output to reports/2025-10-vectorization/phase_h/<STAMP>/attempts/ with commands.txt + env.json, note the blocker in docs/fix_plan.md Attempts, then halt.
Priorities & Rationale:
- plans/active/vectorization.md:91 — Phase H2 requires fresh CUDA pytest + benchmark artifacts before plan archival.
- docs/fix_plan.md:3421 — Next Actions call for capturing CUDA parity + perf bundles under phase_h/<STAMP>/.
- docs/development/testing_strategy.md:18 — Device/dtype discipline mandates CPU+CUDA validation when tensor code changes.
- docs/development/pytorch_runtime_checklist.md:12 — Detector tensors must live on simulator device prior to compiled runs.
- reports/2025-10-vectorization/phase_a/tricubic_baseline.md:1 — Provides CPU baselines to compare against new CUDA timings.
How-To Map:
- Prologue: `git status --short`; ensure clean except expected files. Run `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_tricubic_vectorized.py::TestTricubicVectorized` and `...tests/test_at_abs_001.py::TestDetectorAbsorption` to document selector validity; stash logs under phase_h/<STAMP>/pytest_logs/collect.log.
- CUDA parity: Execute `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py -v -k cuda` then `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_abs_001.py -v -k cuda`; tee each log to phase_h/<STAMP>/pytest_logs/.
- Benchmarks: `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/tricubic_baseline.py --device cuda --repeats 200 --sizes 256 512 --outdir reports/2025-10-vectorization/phase_h/<STAMP>/benchmarks/tricubic` and similarly for `absorption_baseline.py --device cuda --repeats 200 --sizes 256 512 --thicksteps 5 --outdir .../benchmarks/absorption`.
- Metadata: Capture `python -m torch.utils.collect_env` (tee) and `nvidia-smi` (if available) into env.json/commands.txt alongside command list; summarise key metrics in summary.md referencing CPU baselines.
- Wrap-up: Update docs/fix_plan.md [VECTOR-TRICUBIC-001] Attempts with Attempt #18 (include correlations, CUDA timings vs CPU). If parity fails, attach diffs and stop before plan archival.
Pitfalls To Avoid:
- No ad-hoc `.cpu()`/`.cuda()` calls inside physics loops; rely on constructor-time placement.
- Do not skip collect-only proof; selectors must be documented before execution.
- Keep benchmark repeats identical to CPU baselines (200) for comparable stats.
- Avoid overwriting prior phase_h data—use fresh ISO8601 stamp per run.
- Record env + command logs before editing docs/fix_plan.md to keep provenance intact.
- If GPU unavailable, don’t fake success; document unavailability and stop.
- Preserve differentiability: don’t introduce `.item()` when handling metrics in simulator/tests.
- Respect protected assets (docs/index.md) while updating docs/fix_plan.md.
- Ensure pytest logs include both stdout and exit codes; no silent failures.
Pointers:
- plans/active/vectorization.md:91
- docs/fix_plan.md:3410
- docs/development/testing_strategy.md:18
- docs/development/pytorch_runtime_checklist.md:12
- reports/2025-10-vectorization/phase_a/tricubic_baseline.md:1
Next Up: 1) Compare new CUDA timings against CPU baselines and flag regressions >5%; 2) Advance plans/active/vectorization-gap-audit.md Phase B2 once parity holds.
