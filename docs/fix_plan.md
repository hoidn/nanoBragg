# Fix Plan Ledger

**Last Updated:** 2026-01-29 (Probabilistic Strategy realignment)

**Active Focus:**
- STRAT-PROB-002 — Produce benchmark evidence per `docs/strategy/mainstrategy.md` §4 and `docs/plans/2026-01-29-probabilistic-simulator-implementation.md`
- STRAT-PROB-001 — Kernel + tests landed; in review while STRAT-PROB-002 benchmarks ramp

## Index
| ID | Title | Priority | Status |
| --- | --- | --- | --- |
| [STRAT-PROB-001](#strat-prob-001-probabilistic-simulator-kernel) | ProbabilisticSimulator kernel | Critical | in_review |
| [STRAT-PROB-002](#strat-prob-002-probabilistic-benchmark-artifacts) | Probabilistic benchmark artifacts | Critical | ready_for_implementation |

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
- Plan Reference: `docs/plans/2026-01-29-probabilistic-simulator-implementation.md` Task 3
- Goal: Provide reproducible benchmark script + PNG/JSON outputs demonstrating analytic speed/convergence win.
- Dependencies: STRAT-PROB-001 (ProbabilisticSimulator must exist)
- Artifacts Root: `plans/active/strat-prob-002/`
- Next Actions:
  1. Implement `scripts/benchmark_probabilistic.py` with deterministic configs pulled from `scripts/refinement_demo_diffuse.py`, helper builders, and CLI flags `--iterations`, `--device`, `--outdir`, `--plot-only` (Plan Task 3 Step 1).
  2. Produce JSON + PNG artifacts (Plan Task 3 Step 2) capturing loss curves, per-iteration timing, and annotate the plot with measured speedup; stash outputs under both `demo_outputs/` and `plans/active/strat-prob-002/reports/<timestamp>/`.
  3. Update `README_PYTORCH.md` (Performance) and `docs/strategy/mainstrategy.md` §4 with reproducible commands + observed speedup (Plan Task 3 Step 3).
  4. Run `KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmark_probabilistic.py --iterations 150 --device cpu` plus `pytest -v tests/test_probabilistic_simulator.py` to validate no regressions, capturing console logs alongside the PNG/JSON (Plan Task 3 Step 4).
- Exit Criteria:
  - Script runs end-to-end on CPU with analytic curve faster + smoother than Monte Carlo baseline.
  - `demo_outputs/probabilistic_vs_mc_loss.png` + `probabilistic_vs_mc_summary.json` committed.
  - Strategy doc + README updated with reproducible command referencing outputs.

<!-- Supervisor state updated at end of current loop -->

Supervisor state: focus=STRAT-PROB-002 state=planning dwell=1 artifacts=plans/active/strat-prob-002/reports/2026-01-29T061003Z/ next_action=implement_benchmark_cli
