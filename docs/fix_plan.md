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
- Plan Reference: `docs/plans/2026-01-29-probabilistic-simulator-implementation.md` Task 3 + `docs/plans/2026-01-29-probabilistic-benchmark-realignment.md`
- Goal: Provide reproducible benchmark script + PNG/JSON outputs demonstrating analytic speed/convergence win.
- Dependencies: STRAT-PROB-001 (ProbabilisticSimulator must exist)
- Artifacts Root: `plans/active/strat-prob-002/`
- Next Actions:
  1. Task 1 (Alignment Plan): Refactor `scripts/benchmark_probabilistic.py` to introduce `BenchmarkScenario`, CLI geometry overrides, `--scenario`, and `--diagnose-gradients`. Add `tests/scripts/test_benchmark_probabilistic_cli.py`.
  2. Task 2: Add preset catalog + sweep helper (`scripts/benchmark_probabilistic_presets.py`, `--sweep-json`, `--dry-run`), and refresh implementation plan references.
  3. Task 3: Run hi-res scenarios (≥4× speedup) with diagnostics, capture PNG/JSON/sweep artifacts, and update docs + findings.
  4. Task 4: Refresh `input.md`, plan README, and report summaries to hand off hi-res benchmark execution.
- Exit Criteria:
  - Benchmark script exposes documented scenario presets + gradient diagnostics with pytest coverage.
  - Hi-res benchmark artifacts (PNG/JSON/sweep) show ≥4× speedup and non-zero gradients and are archived under `plans/active/strat-prob-002/reports/`.
  - Strategy doc + README reference the hi-res scenario, CLI knobs, and new evidence bundle.
  - Supervisor handoff (`input.md`) maps to the enhanced workflow with updated mapped tests.

<!-- Supervisor state updated at end of current loop -->
Supervisor state: focus=STRAT-PROB-002 state=ready_for_implementation dwell=0 artifacts=plans/active/strat-prob-002/reports/2026-01-29T062136Z/ next_action=delegate_hi_res_benchmark_plan
