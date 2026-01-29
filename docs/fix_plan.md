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
10. ~~**Execute VI ELBO Rebalancing plan:** follow Tasks 1–4 in `docs/plans/2026-01-29-vi-elbo-balancing.md` (KL weighting hook → schedule helper → CLI wiring → refreshed evidence) so the canonical benchmark demonstrates σ recovery (≥1.5° by 150 iterations) and the new CLI knobs + docs cover the workflow.~~ ✅ Implementation landed but benchmark evidence still shows collapse; see Task 11 failure note below.
11. ~~**Task 5** — Run the long-horizon KL annealing benchmark (extended diagnostics + canonical 150-iter run with β ramp) and update docs/findings/strategy with the new evidence.~~ ✅ Completed 2026-01-29. Result: σ did **not** reach 1.5° — 80-iter diagnostics (32×32) peaked at 1.25°, canonical 150-iter benchmark (64×64) collapsed to 0.148°. KL annealing alone is insufficient. Evidence: `plans/active/strat-vi-001/reports/2026-01-29T083412Z/`.
12. ~~**New Plan — Poisson Likelihood Rescaling:** Execute `docs/plans/2026-01-29-vi-poisson-likelihood-rescaling.md` Tasks 1–4 to (a) add Poisson observation helper utilities, (b) wire realistic fluence + Poisson-sampled counts through `vi_poisson_diagnostics.py` and `benchmark_vi_mosaic.py`, (c) refresh CLI/tests/artifacts, and (d) update findings/strategy with the new evidence bundle demonstrating restored likelihood curvature.~~ ✅ Tasks 1–4 landed 2026-01-29: `observation_utils.py` + tests, benchmark + diagnostics wired with `--fluence`/`--observation-seed`, docs updated. **Tasks 5–6 completed (2026-01-29):** Ran canonical `--iterations 150 --fluence 1e13 --observation-seed 321` benchmark. Result: fluence_scale=7.9e-16 zeroed all Poisson observations (mean_counts=0), VI diverged to σ=7.49°. The fluence normalization formula (1e13 / BeamConfig().fluence) is incorrect because raw intensities are not in photon-count space. Evidence: `plans/active/strat-vi-001/reports/2026-01-29T085512Z/`. **New follow-up (Tasks 7–9):** Implement adaptive observation scaling (auto-normalize intensities, metadata-rich summaries), thread the knobs through diagnostics/benchmark CLIs, rerun the canonical benchmark, and refresh docs/findings once σ recovery evidence exists.
- Exit Criteria:
  - New VI modules ship with deterministic seed control (`torch.Generator`) and gradcheck-proven differentiability.
  - Benchmark artifacts (PNG/JSON/logs) demonstrate Poisson ELBO convergence and non-zero gradients compared to MC/analytic, or STRAT-VI-001 documents a mitigation plan that resolves FND-VI-2026-01.
  - `docs/strategy/mainstrategy.md`, README_PYTORCH, and plan docs are updated to state VI is default; analytic path clearly flagged as legacy.
- Analytic simulator emits DeprecationWarning gated on VI success; `docs/findings.md` references the VI resolution/supersession of FND-PROB-2026-01.

<!-- Supervisor state updated at end of current loop -->
13. **Tasks 7–8 (Adaptive Poisson Scaling) — COMPLETED 2026-01-29:** Extended `poisson_sample_observations()` with adaptive auto-scaling (`target_mean_counts`, `normalization` params). Replaced legacy `--fluence` CLI with `--observation-mean` / `--observation-normalization` in both `benchmark_vi_mosaic.py` and `vi_poisson_diagnostics.py`. Tests updated and passing: `test_poisson_observation_helper_auto_scale_hits_target_mean`, `test_benchmark_script_smoke`, `test_vi_diagnostics_snapshot`, `test_vi_diagnostics_beta_schedule`. Plan ref: `docs/plans/2026-01-29-vi-poisson-likelihood-rescaling.md` Tasks 7–8.
14. ~~**Task 9 (Re-run canonical benchmark):**~~ ✅ Completed 2026-01-29. Ran with adaptive scaling. Command: `python scripts/benchmark_vi_mosaic.py --iterations 150 --observation-mean 25.0 --observation-normalization mean --observation-seed 321 --kl-weight-start 0.2 --kl-weight-end 1.0 --kl-warmup-steps 120`. Result: VI σ=0.103° (collapsed; **FAILED ≥1.5° criterion**). Adaptive scaling produced mean_counts=24.97 but did not resolve likelihood–KL imbalance. Evidence: `plans/active/strat-vi-001/reports/2026-01-29T104900Z/`.
15. ~~**Execution plan:**~~ ✅ `docs/plans/2026-01-29-vi-canonical-benchmark-refresh.md` captures the step-by-step workflow for Task 9 (artifact directory setup, observation-stat logging, rerun, doc updates, pytest smoke). Use this plan for the next engineer turn; start with Task 1 (benchmark run + artifact capture).

16. **Task 16 — ELBO decomposition & IWAE experiments:** Execute `docs/plans/2026-01-29-vi-elbo-decomposition.md` (component gradient logging, high-count sweeps, non-centered posterior option, IWAE objective) so we can (a) quantify log-likelihood vs KL gradient magnitudes per iteration, (b) test observation means 25→1000, (c) evaluate whether a non-centered posterior stabilizes σ, and (d) determine if IWAE-style objectives restore σ≥1.5°. Artifact roots belong under `plans/active/strat-vi-001/reports/<ts>/` (subfolders: `observation_sweep/`, `noncentered/`, `iwae/`). Exit once the canonical benchmark passes or the findings document a new mitigation path.

17. **Task 16A (ACTIVE 2026-01-29 15:52Z) — Execute Tasks 3 & 4 from the ELBO decomposition plan:**
    - Implement the `MosaicPosterior` parameterization switch (log-normal vs non-centered softplus), propagate the option through `VariationalMosaicSimulator`, diagnostics, and benchmark CLIs, and refresh the variational family note in `docs/plans/2026-01-29-vi-mosaic-design.md`.
    - Add IWAE objective support to `poisson_elbo` using the new `log_prob_sigma`/`log_prior_sigma` helpers plus per-sample log-likelihood capture; expose `--elbo-objective` CLI knobs and serialize metadata/diagnostics.
    - Capture fresh evidence: `plans/active/strat-vi-001/reports/2026-01-29T155200Z/noncentered/` (log_normal vs noncentered runs, observation_mean=25, k=4) and `.../iwae/` (≥8-sample IWAE sweep). Update `docs/findings.md` FND-VI-2026-01 and `docs/strategy/mainstrategy.md §9` with the outcomes.

Supervisor state: focus=STRAT-VI-001 state=planning dwell=1 artifacts=plans/active/strat-vi-001/reports/2026-01-29T104900Z/ next_action=delegate_task1_vi_elbo_decomposition
Supervisor state: focus=STRAT-VI-001 state=planning dwell=2 artifacts=plans/active/strat-vi-001/reports/2026-01-29T093224Z/ next_action=delegate_task2_vi_observation_sweep

Supervisor state: focus=STRAT-VI-001 state=ready_for_implementation dwell=0 artifacts=plans/active/strat-vi-001/reports/2026-01-29T155200Z/ next_action=delegate_tasks3_4_vi_noncentered_iwae

18. **Task 17 (NEW 2026-01-29 18:05Z) — Observation scale parity:** Execute `docs/plans/2026-01-29-vi-observation-scale-parity.md` to (a) teach `poisson_elbo` about `observation_scale`, (b) plumb the scale metadata through `scripts/analysis/vi_poisson_diagnostics.py`, `scripts/benchmark_vi_mosaic.py`, and MC/analytic baselines, and (c) re-run the canonical VI benchmark so the ≥1.5° criterion is evaluated with the scaled ELBO. Archive artifacts under `plans/active/strat-vi-001/reports/<ts>/scale_parity/`.

Supervisor state: focus=STRAT-VI-001 state=ready_for_implementation dwell=0 artifacts=plans/active/strat-vi-001/reports/2026-01-29T180500Z/ next_action=delegate_task17_vi_observation_scale_parity
19. ~~**Task 17 benchmark rerun (2026-01-29 19:30Z):**~~ ✅ Completed. Ran canonical 150-iter benchmark with observation-scale parity. MC σ=1.517° (meets ≥1.5°), VI σ=0.086° (collapsed). Scale parity is necessary but not sufficient — VI posterior collapse is structural. Evidence: `plans/active/strat-vi-001/reports/2026-01-29T193000Z/scale_parity/`. Demo artifacts refreshed in `demo_outputs/`. Docs (findings, strategy §9, fix_plan) updated with scaled results.

Supervisor state: focus=STRAT-VI-001 state=evidence_captured dwell=0 artifacts=plans/active/strat-vi-001/reports/2026-01-29T193000Z/scale_parity/ next_action=evaluate_alternative_posteriors_or_temperature_scaling

20. **Task 18 — Likelihood-temperature sweep (NEW 2026-01-29 10:22Z):** Execute `docs/plans/2026-01-29-vi-likelihood-temperature.md` to add a `likelihood_temperature` knob to `poisson_elbo`, surface it through diagnostics/benchmark CLIs, and run temperature sweeps (e.g., T∈{1,2,4}) that quantify how hotter likelihoods change σ recovery and gradient ratios. Archive artifacts under `plans/active/strat-vi-001/reports/<ts>/temperature_sweep/`, update `docs/findings.md` (FND-VI-2026-01) and `docs/strategy/mainstrategy.md §9` with conclusions, and refresh `input.md` plus `docs/fix_plan.md` once evidence lands.

Supervisor state: focus=STRAT-VI-001 state=planning dwell=1 artifacts=plans/active/strat-vi-001/reports/2026-01-29T102251Z/ next_action=delegate_task18_likelihood_temperature_sweep
Supervisor state: focus=STRAT-VI-001 state=planning dwell=1 artifacts=plans/active/strat-vi-001/reports/2026-01-29T102251Z/ next_action=delegate_task18_likelihood_temperature_sweep

21. **Task 18 evidence (COMPLETED 2026-01-29 10:22Z):** Likelihood-temperature plumbing plus the baseline sweep (T∈{1,2,4}) shipped and artifacts live under `plans/active/strat-vi-001/reports/2026-01-29T102251Z/temperature_sweep/`. σ plateaued at ≈0.81° for all temperatures, so the next step is to explore hotter temperatures and combine with the IWAE objective before escalating to longer benchmarks.

22. **Task 21 (NEW 2026-01-29 21:30Z) — Temperature × IWAE follow-up:** Execute `docs/plans/2026-01-29-vi-temperature-iwae-followup.md` to (a) run an extended T∈{1,2,4,8} sweep, (b) repeat the sweep with `objective="iwae"` and k=8, (c) trigger a canonical benchmark only if σ≥1.2° shows up in diagnostics, and (d) update docs/findings/fix-plan with the new evidence bundle. Artifacts should live under `plans/active/strat-vi-001/reports/<ts>/temperature_sweep_hot/` (and `/iwae`).

Supervisor state: focus=STRAT-VI-001 state=planning dwell=1 artifacts=plans/active/strat-vi-001/reports/2026-01-29T102251Z/temperature_sweep/ next_action=delegate_task21_temperature_iwae_followup

23. **Task 21 evidence (COMPLETED 2026-01-29 10:34Z):** Extended temperature sweep (T∈{1,2,4,8}) and IWAE+temperature combo both yield σ≈0.81° — no improvement. No configuration reached σ≥1.2° so the 150-iter benchmark was not triggered. The VI posterior collapse is confirmed structural across all tested mitigations (temperature, IWAE, non-centered, observation scaling). Evidence: `plans/active/strat-vi-001/reports/2026-01-29T103412Z/temperature_sweep_hot/`.

Supervisor state: focus=STRAT-VI-001 state=evidence_captured dwell=0 artifacts=plans/active/strat-vi-001/reports/2026-01-29T103412Z/temperature_sweep_hot/ next_action=evaluate_prior_schedule_or_multi_scale_geometry

24. **Task 24 (NEW 2026-01-29 22:15Z) — Prior schedule & multi-geometry diagnostics:** Execute `docs/plans/2026-01-29-vi-prior-geometry.md` to (a) add a configurable prior schedule helper + posterior setter, (b) surface prior knobs through diagnostics and benchmark CLIs, (c) capture 32×32 / 64×64 / 128×128 short-run diagnostics with informative priors, and (d) rerun the canonical 150-iter benchmark using the best prior+geometry combo. Archive artifacts under `plans/active/strat-vi-001/reports/<ts>/prior_schedule/` and `/prior_benchmark/`. Exit once we either achieve σ≥1.5° or document why informative priors + higher resolution still collapse.

Supervisor state: focus=STRAT-VI-001 state=planning dwell=1 artifacts=docs/plans/2026-01-29-vi-prior-geometry.md next_action=delegate_task24_prior_schedule_geometry

Supervisor state: focus=STRAT-VI-001 state=ready_for_implementation dwell=0 artifacts=plans/active/strat-vi-001/reports/2026-01-29T105208Z/prior_schedule_dev/ next_action=delegate_task24_prior_schedule_tasks1_2

Supervisor state: focus=STRAT-VI-001 state=ready_for_implementation dwell=0 artifacts=plans/active/strat-vi-001/reports/2026-01-29T113030Z/ next_action=delegate_task24_prior_schedule_tasks3_4
