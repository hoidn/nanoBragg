# Fix Plan Ledger

**Last Updated:** 2026-01-29 (Variational mosaic pivot)

**Active Focus:**
- STRAT-VI-001 — Execute `docs/plans/2026-01-29-vi-mosaic-implementation-plan.md` to land the VariationalMosaicSimulator stack and retire the analytic kernel once VI passes
- STRAT-PROB-001/002/003 — Paused as legacy reference while VI replaces the analytic mosaic flow

## Index
| ID | Title | Priority | Status |
| --- | --- | --- | --- |
| [STRAT-PROB-001](#strat-prob-001-probabilistic-simulator-kernel) | ProbabilisticSimulator kernel | Critical | paused_legacy |
| [STRAT-PROB-002](#strat-prob-002-probabilistic-benchmark-artifacts) | Probabilistic benchmark artifacts | Critical | paused_legacy |
| [STRAT-PROB-003](#strat-prob-003-probabilistic-gradient-recovery) | Probabilistic gradient recovery | Critical | paused_legacy |
| [STRAT-VI-001](#strat-vi-001-variational-mosaic-simulator) | Variational mosaic simulator | Critical | in_progress |

## [STRAT-PROB-001] ProbabilisticSimulator kernel
- Strategy Reference: `docs/strategy/mainstrategy.md` §§2–3 (drop-in API, angular broadening, stash-and-patch requirement)
- Plan Reference: `docs/plans/2026-01-29-probabilistic-simulator-implementation.md` Tasks 1–2
- Goal: Land a differentiable analytic mosaic kernel plus regression/gradcheck coverage on CPU+CUDA.
- Dependencies: None (reuses existing Simulator + configs)
- Artifacts Root: `plans/active/strat-prob-001/` (reports/2026-01-29T060113Z contains supervisor summary + pytest logs)
- Next Actions:
  1. Review engineer evidence bundle (tests + gradcheck output) and confirm CUDA logs are archived under `plans/active/strat-prob-001/`.
  2. Spot-check `tests/test_probabilistic_simulator.py` on CUDA once GPU node is available (Plan Task 2 Step 6) and drop log in the artifacts root if not already present.
  3. File a finding only if additional gradient or parity observations emerge during review; otherwise no new doc updates are required.
- Exit Criteria:
  - Tests from Task 1 all pass on CPU and CUDA.
  - Kernel satisfies §3B angular broadening equation and §3C full-metric requirement (documented in code docstrings).
  - Plan Tasks 1–2 marked complete with evidence bundle referenced from artifacts root.

## [STRAT-PROB-002] Probabilistic benchmark artifacts
- Strategy Reference: `docs/strategy/mainstrategy.md` §4 (benchmark + killer plot) & §5 risk table (speed + convergence proof)
- Plan Reference: `docs/plans/2026-01-29-probabilistic-simulator-implementation.md` Task 3 + `docs/plans/2026-01-29-probabilistic-benchmark-realignment.md`
- Goal: Provide reproducible benchmark script + PNG/JSON outputs demonstrating analytic speed/convergence win.
- Dependencies: STRAT-PROB-001 (ProbabilisticSimulator must exist)
- Artifacts Root: `plans/active/strat-prob-002/`
- Next Actions:
  1. ~~Task 1: Refactor benchmark with BenchmarkScenario, CLI overrides, gradient diagnostics, tests.~~ ✅ Done.
  2. ~~Task 2: Preset catalog + sweep helper + dry-run.~~ ✅ Done.
  3. ~~Task 3: Run hi-res scenarios with diagnostics, capture artifacts, update docs.~~ ✅ Done — gradient zero-out confirmed in hi-res (FND-PROB-2026-01).
  4. ~~Task 4: Refresh handoff docs.~~ ✅ Done.
  5. **NEW:** Investigate why probabilistic kernel produces zero gradients across all presets. The σ ≫ |ΔQ| regime makes the Gaussian envelope ≈ 1.0 everywhere. Potential fixes: (a) change broadening formula so σ is comparable to ΔQ, (b) add structured off-Bragg sampling, (c) validate kernel math separately before running full refinement loop.
- Exit Criteria:
  - Benchmark script exposes documented scenario presets + gradient diagnostics with pytest coverage.
  - Hi-res benchmark artifacts (PNG/JSON/sweep) show ≥4× speedup and non-zero gradients and are archived under `plans/active/strat-prob-002/reports/`.
  - Strategy doc + README reference the hi-res scenario, CLI knobs, and new evidence bundle.
  - Supervisor handoff (`input.md`) maps to the enhanced workflow with updated mapped tests.
  - STRAT-PROB-003 delivers the gradient fix so this entry can move to **complete**.

## [STRAT-PROB-003] Probabilistic gradient recovery
- Strategy Reference: `docs/strategy/mainstrategy.md` §§3–4, speedup + gradient requirements
- Plan Reference: `docs/plans/2026-01-29-probabilistic-gradient-recovery.md`
- Goal: Instrument the analytic kernel, adjust the Gaussian breadth using reciprocal metric data, and refresh benchmark evidence so probabilistic gradients are >1e-4 (hi_res_b/c) and ≥4× speedup is documented.
- Dependencies: STRAT-PROB-002 artifacts (baseline CLI + presets)
- Artifacts Root: `plans/active/strat-prob-003/` (current loop report: `2026-01-29T065513Z`)
- Next Actions:
  1. ~~Task 1 (plan §Task 1): add kernel diagnostics callback + new `scripts/analysis/probabilistic_gaussian_diagnostics.py` harness with pytest coverage.~~ ✅ Completed 2026-01-29 (artifacts: `plans/active/strat-prob-003/reports/2026-01-29T065513Z/task1_pytest.log`).
  2. ~~Task 2: capture hi_res_b diagnostics, update `docs/findings.md` entry FND-PROB-2026-01 with quantified evidence.~~ ✅ Completed 2026-01-29 (artifacts: `plans/active/strat-prob-003/reports/2026-01-29T065513Z/hi_res_b_diag.*`).
  3. **Task 3 (ACTIVE):** update the design doc with the Δθ-based Gaussian width, refactor `compute_probabilistic_physics` to use `g_norm`/`delta_theta`, extend the diagnostics script + pytest coverage, and add the hi_res_b spread regression plus `tests/test_probabilistic_gradients.py` (≥1e-4 gradient magnitude).
  4. Task 4: refresh benchmark presets/artifacts (add `hi_res_c`), rerun CLI, and roll the evidence into `docs/strategy/mainstrategy.md` + README once Task 3 proves non-zero gradients and ≥4× speedup.
- Exit Criteria:
  - Diagnostics JSON/markdown exist under the artifacts root showing |ΔQ|/σ ratios and non-zero FD gradients for hi_res_b.
- Updated kernel & tests land with grad magnitudes ≥1e-4 for hi_res_b (unit test) and gradcheck continues to pass on CPU.
- `scripts/benchmark_probabilistic.py --scenario hi_res_c` yields probabilistic mean |grad| ≥1e-4 and speedup ≥4× (artifacts logged + docs updated).
- STRAT-PROB-002 can move to **complete** (docs referencing artifacts, README updated).

> **Status:** Paused as of 2026-01-29. The analytic Gaussian fix is no longer on the critical path because VI mosaic modeling supersedes it. Preserve artifacts for documentation but do not resume until STRAT-VI-001 completes.

## [STRAT-VI-001] Variational mosaic simulator
- Strategy Reference: `docs/strategy/mainstrategy.md` §8 (VI replacement for mosaicity)
- Plan Reference: `docs/plans/2026-01-29-vi-mosaic-implementation-plan.md`, `docs/plans/2026-01-29-vi-elbo-balancing.md`
- Goal: Implement the VariationalMosaicSimulator stack (posterior module, VariationalMosaicSimulator class, Poisson ELBO helper, benchmarks, and analytic deprecation) so mosaicity gradients are recovered via VI instead of the analytic Gaussian.
- Dependencies: STRAT-PROB-003 findings FND-PROB-2026-01 (zero gradients) plus existing Simulator API contracts.
- Artifacts Root: `plans/active/strat-vi-001/` (current loop report: `2026-01-29T080653Z`)
- Next Actions:
  1. ~~**Task 1** — Stand up `src/nanobrag_torch/vi/mosaic_posterior.py` with a reparameterized log-normal sampler, KL helper, and `tests/test_vi_mosaic.py::test_mosaic_posterior_*` coverage (write test first).~~ ✅ (2026-01-29 engineer loop)
  2. ~~**Task 2** — Implement `VariationalMosaicSimulator` in `src/nanobrag_torch/simulators/variational_mosaic.py` plus smoke tests that show `k_samples=1` matches deterministic rotations and averages across seeds; update `__init__.py`.~~ ✅ (2026-01-29 engineer loop; tests recorded in `engineer_summary.md`)
  3. ~~**Task 3** — Add `src/nanobrag_torch/vi/poisson_elbo.py` and gradcheck/regression coverage tying simulator + posterior together.~~ ✅ (2026-01-29 engineer loop — verified via `pytest tests/test_vi_mosaic.py::TestPoissonELBO::*` on CPU with gradcheck.)
  4. ~~**Task 4** — Build `scripts/benchmark_vi_mosaic.py` with a reusable `run_benchmark()` helper, add `tests/test_vi_mosaic.py::test_benchmark_script_smoke`, and refresh `docs/strategy/mainstrategy.md` + `docs/development/testing_strategy.md` so the VI benchmark workflow (PNG/JSON artifacts + CLI commands) is documented.~~ ✅ Completed 2026-01-29 (artifact: `plans/active/strat-vi-001/reports/2026-01-29T075217Z/collect_test_benchmark_script_smoke.log`).
5. ~~**Task 5** — After VI passes, emit `DeprecationWarning` in the analytic simulator and mark docs accordingly.~~ ✅ Completed January 29 2026 (warning added, README_PYTORCH + analytic design doc flagged as legacy, new pytest guard).
6. ~~Capture a CPU test log for `tests/test_vi_mosaic.py::test_probabilistic_simulator_deprecated_warning` under `plans/active/strat-vi-001/reports/2026-01-29T075930Z/` and confirm the warning appears exactly once (evidence for fix_plan exit criteria).~~ ✅ 2026-01-29 (`test_deprecation_warning.log`).
7. ~~**Evidence gap:** run the canonical VI benchmark command (`KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 python scripts/benchmark_vi_mosaic.py --iterations 150 --outdir demo_outputs`) and archive the console log plus the resulting `vi_vs_mc_loss.png` / `vi_vs_mc_summary.json` under `plans/active/strat-vi-001/reports/2026-01-29T080653Z/`. Reference the artifact paths in `demo_outputs/` and summarize the convergence metrics in that report.~~ ✅ Logged in `benchmark_summary.md` / `vi_vs_mc_summary.json` (2026-01-29 supervisor loop).
8. ~~**Task 7** — Diagnose VI spread collapse (FND-VI-2026-01) via enriched `poisson_elbo` diagnostics + benchmark logging, then archive the JSON/markdown bundle under `plans/active/strat-vi-001/reports/2026-01-29T081427Z/`.~~ ✅ Evidence wired + findings/strategy updated 2026-01-29.
9. ~~**Plan update** — Draft focused mitigation design (ELBO rescaling / observation normalization) now that instrumentation is done.~~ ✅ `docs/plans/2026-01-29-vi-elbo-balancing.md` captures the KL annealing rollout.
10. **Execute VI ELBO Rebalancing plan:** follow Tasks 1–4 in `docs/plans/2026-01-29-vi-elbo-balancing.md` (KL weighting hook → schedule helper → CLI wiring → refreshed evidence) so the canonical benchmark demonstrates σ recovery (≥1.5° by 150 iterations) and the new CLI knobs + docs cover the workflow.
- Exit Criteria:
  - New VI modules ship with deterministic seed control (`torch.Generator`) and gradcheck-proven differentiability.
  - Benchmark artifacts (PNG/JSON/logs) demonstrate Poisson ELBO convergence and non-zero gradients compared to MC/analytic, or STRAT-VI-001 documents a mitigation plan that resolves FND-VI-2026-01.
  - `docs/strategy/mainstrategy.md`, README_PYTORCH, and plan docs are updated to state VI is default; analytic path clearly flagged as legacy.
- Analytic simulator emits DeprecationWarning gated on VI success; `docs/findings.md` references the VI resolution/supersession of FND-PROB-2026-01.

<!-- Supervisor state updated at end of current loop -->
Supervisor state: focus=STRAT-VI-001 state=planning dwell=1 artifacts=plans/active/strat-vi-001/reports/2026-01-29T081427Z/ next_action=delegate_kl_annealing_plan
