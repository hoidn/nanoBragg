# Fix Plan Ledger

**Last Updated:** 2026-01-29 (Variational mosaic pivot)

**Active Focus:**
- STRAT-M2-001 — Execute `docs/plans/2026-01-29-m2-amortized-multi-image.md` to deliver the Duck amortized multi-image demo (Strategy §7 Milestone M1)
- STRAT-PROB-001/002/003 — Paused as legacy reference while VI replaces the analytic mosaic flow

## Index
| ID | Title | Priority | Status |
| --- | --- | --- | --- |
| [STRAT-PROB-001](#strat-prob-001-probabilistic-simulator-kernel) | ProbabilisticSimulator kernel | Critical | paused_legacy |
| [STRAT-PROB-002](#strat-prob-002-probabilistic-benchmark-artifacts) | Probabilistic benchmark artifacts | Critical | paused_legacy |
| [STRAT-PROB-003](#strat-prob-003-probabilistic-gradient-recovery) | Probabilistic gradient recovery | Critical | paused_legacy |
| [STRAT-VI-001](#strat-vi-001-variational-mosaic-simulator) | Variational mosaic simulator | Critical | failed |
| [STRAT-VI-002](#strat-vi-002-gaussian-likelihood-vi-path) | Gaussian likelihood VI path | Critical | failed |
| [STRAT-M2-001](#strat-m2-001-duck-multi-image-demo) | Duck multi-image demo | Critical | in_progress |

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
- Exit Criteria: **FAILED** — see FND-VI-2026-01h. All 9 mitigations are exhausted and σ never reached 1.5° on the canonical benchmark. Future work moves to STRAT-VI-002.

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

25. **Task 25 (NEW 2026-01-29 23:45Z) — Multiscale geometry sweep:** Execute `docs/plans/2026-01-29-vi-multiscale-geometry.md` to (a) add the VI geometry preset module + CLI wiring, (b) build a `run_geometry_sweep` helper inside `scripts/analysis/vi_poisson_diagnostics.py`, and (c) run the new sweep + canonical benchmark on multi-scale crystal configurations (smaller cell + shorter wavelength per `docs/strategy/mainstrategy.md §9`). Artifact roots will live under `plans/active/strat-vi-001/reports/<ts>/geometry_sweep/` and `/geometry_benchmark/`. Exit once the sweep either recovers σ ≥ 1.5° or documents why richer geometries still collapse and recommends the next mitigation (e.g., flow posterior or hybrid MC-VI).

Supervisor state: focus=STRAT-VI-001 state=planning dwell=1 artifacts=docs/plans/2026-01-29-vi-multiscale-geometry.md next_action=delegate_task25_geometry_presets

26. **Task 26 (NEW 2026-01-29 23:59Z) — Flow posterior / hybrid pathfinding:** Execute `docs/plans/2026-01-29-vi-flow-posterior.md` to land a normalizing-flow parameterization for `MosaicPosterior`, expose the knobs via diagnostics + benchmark CLIs, and capture evidence showing whether the expressive posterior can break the σ≤0.8° ceiling logged in FND-VI-2026-01f. Scope:
    - Task 1–2: build affine-coupling flow layers + integrate them into `MosaicPosterior` with gradcheck coverage.
    - Task 3: wire CLI flags (`--posterior-parameterization flow`, `--posterior-flow-layers`, etc.) plus simulator plumbing and snapshot tests.
    - Task 4: run comparative diagnostics / canonical benchmark (`plans/active/strat-vi-001/reports/<ts>/flow_{diagnostics,benchmark}/`), update `docs/findings.md` + `docs/strategy/mainstrategy.md` with go/no-go results, and set the next mitigation (e.g., hybrid MC-VI) if σ is still <1.5°.
    - Exit criteria: flow posterior code + tests merged, artifacts demonstrating sigma trajectory ≥1.5° **or** documented structural failure plus recommendation for the hybrid path.
- **Status 2026-01-29 12:25Z:** Tasks 1–3 landed (`src/nanobrag_torch/vi/flows.py`, `mosaic_posterior.py`, CLI plumbing, tests). Observation diagnostics captured at `plans/active/strat-vi-001/reports/2026-01-29T122511Z/flow_diagnostics/vi_diagnostics.json` show the flow posterior blasting σ to 16° on iter 1 before collapsing to 0.064° by iter 24; gradient ratios balloon (>4e2) but the ELBO still collapses. The canonical flow benchmark run (`demo_outputs/vi_vs_mc_summary.json`, iterations=30, `posterior_parameterization="flow"`) diverged to NaNs after ≈22 iterations, and no artifacts were archived under `flow_benchmark/`. Plan Task 4 remains OPEN: log-normal baseline diagnostics + comparison summary are missing, the 150-iter flow benchmark artifacts are absent, and docs/findings/fix_plan/input still describe flow as "pending".
- **Next Actions:**
    1. Re-run the observation sweep for both flow and log-normal parameterizations (25 iters, 32×32 detector, `observation_mean=25`, `k=4`) via `scripts/analysis/vi_poisson_diagnostics.py`. Archive outputs under `plans/active/strat-vi-001/reports/2026-01-29T235959Z/flow_diagnostics/` as `{flow.json, baseline.json}` plus a `summary.md` comparing σ/gradient trajectories.
    2. Run the canonical 150-iteration benchmark with `--posterior-parameterization flow --posterior-flow-layers 4 --posterior-flow-hidden 32 --k-samples 4 --observation-mean 25 --observation-normalization mean --kl-weight-start 0.2 --kl-weight-end 1.0 --kl-warmup-steps 120 --prior-spread-start 2.0 --prior-spread-end 0.5 --prior-warmup-steps 120`. Archive PNG/JSON/logs under `plans/active/strat-vi-001/reports/2026-01-29T235959Z/flow_benchmark/` (copy the `vi_vs_mc_*` files there in addition to `demo_outputs/`).
    3. Update `docs/findings.md` (FND-VI-2026-01) and `docs/strategy/mainstrategy.md §9` with the new flow evidence + conclusion (still collapses), refresh this fix-plan entry and `input.md`, and articulate whether we escalate to the hybrid MC-VI plan.

- **Status 2026-01-29 (Task 26 COMPLETED — FAILED):** All three actions executed:
    1. ✅ Flow vs log-normal diagnostics archived: `plans/active/strat-vi-001/reports/2026-01-29T235959Z/flow_diagnostics/{flow/,baseline/,summary.md}`. Flow σ blew up to 37–56° (vs baseline 0.81°).
    2. ✅ 150-iter canonical benchmark: `plans/active/strat-vi-001/reports/2026-01-29T235959Z/flow_benchmark/`. Flow diverged to NaN by iteration 2. Demo artifacts copied to `demo_outputs/`.
    3. ✅ `docs/findings.md` (FND-VI-2026-01g), `docs/strategy/mainstrategy.md §9`, and this fix-plan updated.
    - **Result: FAILED ≥1.5° criterion.** Flow posterior introduces catastrophic σ blow-up / NaN divergence.
    - **All 8 VI mitigations exhausted.** Recommend escalation to hybrid MC-VI (`docs/plans/2026-01-29-vi-hybrid-mc-vi.md`).

Supervisor state: focus=STRAT-VI-001 state=task26_complete_failed dwell=0 artifacts=plans/active/strat-vi-001/reports/2026-01-29T235959Z/ next_action=escalate_hybrid_mc_vi_plan

27. **Task 27 (NEW 2026-01-29 23:59Z) — Hybrid MC-VI escalation plan:** Execute `docs/plans/2026-01-29-vi-hybrid-mc-vi.md` to build the MC warm-start + VI fine-tune pipeline documented in `docs/strategy/mainstrategy.md §9`. Scope:
    - ~~Task 1: land the `run_mc_warm_start()` helper + dataclasses under `src/nanobrag_torch/vi/hybrid.py` with pytest coverage (`tests/test_vi_hybrid.py`).~~ ✅ Completed 2026-01-29
    - ~~Task 2: add `MosaicPosterior.prime_from_sigma()` + tests so the VI stage can consume the MC σ.~~ ✅ Completed 2026-01-29
    - ~~Task 3: ship the `HybridMosaicTrainer` orchestration class (warm-start → VI) with dependency injection hooks for diagnostics, plus unit tests.~~ ✅ Completed 2026-01-29
    - ~~Task 4: add `scripts/analysis/vi_hybrid_refinement.py` (diagnostics CLI) + smoke tests.~~ ✅ Completed 2026-01-29
    - ~~Task 5: integrate hybrid mode into `scripts/benchmark_vi_mosaic.py`, refresh docs/findings, and archive diagnostics + canonical benchmark artifacts under `plans/active/strat-vi-001/reports/<ts>/hybrid_{diagnostics,benchmark}/`.~~ ✅ Completed 2026-01-29
    - **Execution reference:** `docs/plans/2026-01-29-hybrid-benchmark-evidence.md` (diagnostics + canonical benchmark workflow)
    - Exit criteria: canonical 150-iter benchmark demonstrates σ≥1.5° **or** the evidence bundle proves the hybrid path also collapses → **FAILED. Hybrid collapses σ to 0.04° (MC warm-start) / 0.02° (VI fine-tune). Evidence: `plans/active/strat-vi-001/reports/2026-01-29T235800Z/`.**
    - **Status: FAILED.** MC warm-start collapsed σ 0.45°→0.04° (MSE landscape biased toward σ→0). VI fine-tune (150 iters) could not recover. All 9 VI mitigations exhausted. **STRAT-VI-001 should be closed as failed.** Next: escalate to Gaussian likelihood or amortized multi-image inference.

Supervisor state: focus=STRAT-VI-001 state=task27_complete_failed dwell=0 artifacts=plans/active/strat-vi-001/reports/2026-01-29T235800Z/ next_action=close_strat_vi_001_escalate_gaussian_likelihood

- Strategy Reference: `docs/strategy/mainstrategy.md §9` (post-hybrid escalation) — Gaussian likelihood replaces the Poisson ELBO to inject curvature into the VI loss landscape.
- Plan Reference: `docs/plans/2026-01-29-vi-gaussian-likelihood.md`
- Goal: Implement a Gaussian observation helper + ELBO, update diagnostics/benchmark CLIs, and capture new benchmark evidence so we can judge whether Gaussian likelihood recovers σ≥1.5° or produces a new finding documenting failure.
- Dependencies: STRAT-VI-001 failure bundle (artifacts under `plans/active/strat-vi-001/`) and the existing VI simulator stack.
- Artifacts Root: `plans/active/strat-vi-002/` (current loop report: `2026-01-29T213000Z`).
- Next Actions:
  1. ~~**Task 1:** Author `docs/architecture/vi_gaussian_likelihood.md`, update `docs/index.md`, and add the §9.2 Gaussian escalation narrative in `docs/strategy/mainstrategy.md`.~~ ✅ Completed 2026-01-29 (spec + doc hooks merged; evidence logged in `plans/active/strat-vi-002/reports/2026-01-29T130500Z/`).
  2. ~~**Task 2:** Extend `src/nanobrag_torch/vi/observation_utils.py` with `gaussian_sample_observations()` plus new tests in `tests/test_vi_mosaic.py`.~~ ✅ Completed 2026-01-29 (observation helper + metadata tests landed).
  3. ~~**Task 3:** Create `src/nanobrag_torch/vi/gaussian_elbo.py`, expose it via `vi.__init__`, and add gradcheck/regression coverage.~~ ✅ Completed 2026-01-29 (Gaussian ELBO + gradcheck suite recorded in `tests/test_vi_mosaic.py`).
  4. ~~**Task 4:** Add `--likelihood {poisson,gaussian}` plumbing to `scripts/analysis/vi_poisson_diagnostics.py` and `scripts/benchmark_vi_mosaic.py`, including CLI smoke tests and demo artifact refresh.~~ ✅ Completed 2026-01-29 (diagnostics CLI accepts `--likelihood`; log archived under `plans/active/strat-vi-002/reports/2026-01-29T130500Z/`).
  5. ~~**Task 5:** Update `scripts/benchmark_vi_mosaic.py` regression tests and CLI wiring so Gaussian runs emit `vi_vs_mc_*` artifacts plus `likelihood_model` metadata.~~ ✅ Completed 2026-01-29 (see `tests/test_vi_mosaic.py::TestBenchmarkCLI::test_benchmark_cli_gaussian`).
  6. ~~**Task 6** — Run Gaussian diagnostics + canonical benchmark and refresh docs/artifacts.~~ ✅ Completed 2026-01-29 (artifacts under `plans/active/strat-vi-002/reports/2026-01-29T213000Z/`). Benchmark failed the ≥1.5° criterion (σ=0.078°), producing FND-VI-2026-02. STRAT-VI-002 is closed as **failed**; escalate to STRAT-M2-001.
- Exit Criteria (FAILED 2026-01-29): Gaussian helper + ELBO shipped but canonical benchmark still collapsed (FND-VI-2026-02). Initiative closed; follow-up is STRAT-M2-001 per strategy §7.

Supervisor state: focus=STRAT-VI-002 state=failed dwell=0 artifacts=plans/active/strat-vi-002/reports/2026-01-29T213000Z/ next_action=escalate_to_strat_m2_001

## [STRAT-M2-001] Duck multi-image demo
- Strategy Reference: `docs/strategy/mainstrategy.md` §7 (Milestones M1–M3)
- Plan References:
  - `docs/plans/2026-01-29-m2-amortized-multi-image.md` (M1: dataset + shared-posterior demo — ✅ code complete, docs pending)
  - `docs/plans/2026-01-29-m2-amortized-mosaicity.md` (M2: amortized encoder + diagnostics)
- Goal: Advance the multi-image refinement track from the fixed shared-posterior Duck demo (delivered 2026-01-29 engineer loop) to an amortized encoder that predicts per-image mosaic spread with measurable gradient amplification as dataset size grows.
- Dependencies: STRAT-VI-001/002 findings (posterior collapse), Duck dataset artifacts under `demo_inputs/duck_multi_image/`.
- Artifacts Root: `plans/active/strat-m2-001/`
- Next Actions (Task numbers per M2 plan):
  1. **Task 1 — Dataset spec + mosaic truth:** Finish the Duck dataset spec (`docs/specs/duck_multi_image_dataset.md`), teach the generator to emit per-image mosaic spreads + observation scaling metadata, refresh `demo_inputs/duck_multi_image/`, and extend `tests/test_duck_dataset.py` accordingly.
  2. **Task 2 — Amortized encoder:** Land `src/nanobrag_torch/vi/amortized_encoder.py` with pytest coverage for shape/grad flow and export it via `vi.__init__`.
  3. **Task 3 — Conditioned trainer plumbing:** Extend `MultiImageTrainer` + `mosaic_posterior` with an amortized mode that builds conditioned posteriors per image, logs per-image sigma + gradient norms, and adds regression tests in `tests/test_vi_mosaic.py`.
  4. **Task 4 — CLI + docs:** Add `--mode amortized` + diagnostics to `scripts/demo_recover_duck.py`, capture artifacts under `plans/active/strat-m2-001/reports/<ts>/amortized_demo/`, update `docs/strategy/mainstrategy.md` + `docs/development/testing_strategy.md`, and refresh this ledger once evidence lands.
- Exit Criteria:
  - Duck dataset spec published + referenced from `docs/index.md`; metadata includes per-image mosaic truth, observation scaling, and orientation stats.
  - `DuckMosaicEncoder` + amortized trainer pass targeted pytest selectors, with per-image sigma predictions differing across images and gradients remaining finite.
  - `scripts/demo_recover_duck.py --mode amortized` generates PNG/JSON artifacts that show loss decrease plus σ recovery ≥1.5° on the canonical 20-image set, and gradient norms increase when repeating the run with 10 vs 20 images.
  - Strategy/testing docs cite the new CLI workflow and artifact path; demo outputs synced under `demo_outputs/duck_amortized/`.

Supervisor state: focus=STRAT-M2-001 state=planning dwell=1 artifacts=plans/active/strat-m2-001/reports/TBD next_action=delegate_task1_dataset_spec

Supervisor state: focus=STRAT-M2-001 state=ready_for_implementation dwell=0 artifacts=plans/active/strat-m2-001/reports/2026-01-29T230500Z/ next_action=delegate_tasks3_4_amortized_trainer_cli
