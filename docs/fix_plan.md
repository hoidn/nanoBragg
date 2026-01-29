# Fix Plan Ledger

**Last Updated:** 2026-01-29 (Probabilistic Strategy realignment)

**Active Focus:**
- STRAT-PROB-003 — Execute `docs/plans/2026-01-29-probabilistic-gradient-recovery.md` to resolve FND-PROB-2026-01
- STRAT-PROB-002 — Benchmark artifacts frozen pending STRAT-PROB-003 fix
- STRAT-PROB-001 — Kernel + tests landed; in review while STRAT-PROB-002 benchmarks ramp

## Index
| ID | Title | Priority | Status |
| --- | --- | --- | --- |
| [STRAT-PROB-001](#strat-prob-001-probabilistic-simulator-kernel) | ProbabilisticSimulator kernel | Critical | in_review |
| [STRAT-PROB-002](#strat-prob-002-probabilistic-benchmark-artifacts) | Probabilistic benchmark artifacts | Critical | done_with_findings |
| [STRAT-PROB-003](#strat-prob-003-probabilistic-gradient-recovery) | Probabilistic gradient recovery | Critical | in_progress |

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

<!-- Supervisor state updated at end of current loop -->
Supervisor state: focus=STRAT-PROB-003 state=ready_for_implementation dwell=0 artifacts=plans/active/strat-prob-003/reports/2026-01-29T070535Z/ next_action=implement_task3_sigma_fix
