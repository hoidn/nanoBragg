# Fix Plan Ledger

**Last Updated:** 2026-01-29 (Probabilistic Strategy realignment)

**Active Focus:**
- STRAT-PROB-001 — Implement ProbabilisticSimulator kernel per `docs/strategy/mainstrategy.md` §3A and `docs/plans/2026-01-29-probabilistic-simulator-implementation.md`
- STRAT-PROB-002 — Produce benchmark evidence per `docs/strategy/mainstrategy.md` §4 and `docs/plans/2026-01-29-probabilistic-simulator-implementation.md`

## Index
| ID | Title | Priority | Status |
| --- | --- | --- | --- |
| [STRAT-PROB-001](#strat-prob-001-probabilistic-simulator-kernel) | ProbabilisticSimulator kernel | Critical | in_planning |
| [STRAT-PROB-002](#strat-prob-002-probabilistic-benchmark-artifacts) | Probabilistic benchmark artifacts | Critical | in_planning |

## [STRAT-PROB-001] ProbabilisticSimulator kernel
- Strategy Reference: `docs/strategy/mainstrategy.md` §§2–3 (drop-in API, angular broadening, stash-and-patch requirement)
- Plan Reference: `docs/plans/2026-01-29-probabilistic-simulator-implementation.md` Tasks 1–2
- Goal: Land a differentiable analytic mosaic kernel plus regression/gradcheck coverage on CPU+CUDA.
- Dependencies: None (reuses existing Simulator + configs)
- Artifacts Root: `plans/active/strat-prob-001/` (TODO: populate on first engineering attempt)
- Next Actions:
  1. Author targeted pytest module (`tests/test_probabilistic_simulator.py`) capturing Monte Carlo parity + gradcheck (Plan Task 1).
  2. Implement `ProbabilisticSimulator` subclass + analytic kernel + stash/patch run override (Plan Task 2 Steps 1–5).
  3. Run `pytest -v tests/test_probabilistic_simulator.py` on CPU and CUDA (Plan Task 2 Step 6) and capture logs under artifacts root.
  4. Record findings + gradient verification into `docs/findings.md` if new observations appear (Plan Task 2 Step 7 commit message should cite artifacts).
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
  1. Implement `scripts/benchmark_probabilistic.py` CLI and seed deterministic configs mirroring `scripts/refinement_demo_diffuse.py` (Plan Task 3 Step 1).
  2. Generate PNG + JSON under `demo_outputs/` plus CLI options for alternate `--outdir` (Plan Task 3 Step 2).
  3. Document instructions + references in `README_PYTORCH.md` and update `docs/strategy/mainstrategy.md` §4 to call out the concrete script (Plan Task 3 Step 3).
  4. Run benchmark (Plan Task 3 Step 4) and stash logs/plots in artifacts root for PI review.
- Exit Criteria:
  - Script runs end-to-end on CPU with analytic curve faster + smoother than Monte Carlo baseline.
  - `demo_outputs/probabilistic_vs_mc_loss.png` + `probabilistic_vs_mc_summary.json` committed.
  - Strategy doc + README updated with reproducible command referencing outputs.

<!-- Supervisor state updated at end of current loop -->

Supervisor state: focus=STRAT-PROB-001 state=planning dwell=1 artifacts=plans/active/strat-prob-001/reports/2026-01-29T060113Z/ next_action=author_probabilistic_tests
