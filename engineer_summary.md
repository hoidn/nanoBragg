# Engineer Summary — STRAT-PROB-002 (Benchmark Realignment)

## What I Did

Executed all 4 tasks from `docs/plans/2026-01-29-probabilistic-benchmark-realignment.md`:

1. **Task 1:** Added `BenchmarkScenario` dataclass, `resolve_scenario()` with CLI precedence, `--diagnose-gradients` flag, and CLI test coverage (4 tests).
2. **Task 2:** Created `scripts/benchmark_probabilistic_presets.py` with 3 presets (default, hi_res_a, hi_res_b), wired `--scenario`, `--sweep-json`, `--dry-run` into CLI.
3. **Task 3:** Ran hi_res_b benchmark (128×128, 30Å cell, 0.5Å λ), captured artifacts, updated strategy doc §4 and fix_plan.md, logged finding FND-PROB-2026-01.
4. **Task 4:** Updated `plans/active/strat-prob-002/README.md` with preset table and report index, wrote report summary.

## Files Changed

| File | Action |
|------|--------|
| `scripts/benchmark_probabilistic.py` | Modified — scenario resolution, CLI overrides, gradient diagnostics, sweep, dry-run |
| `scripts/benchmark_probabilistic_presets.py` | Created — BenchmarkScenario dataclass + PRESETS dict |
| `scripts/presets/hi_res_probe.json` | Created — sweep config for hi-res probe |
| `tests/scripts/__init__.py` | Created |
| `tests/scripts/test_benchmark_probabilistic_cli.py` | Created — 4 CLI tests |
| `docs/strategy/mainstrategy.md` | Modified — added hi_res_b measured results |
| `docs/fix_plan.md` | Modified — marked tasks done, added new action for gradient investigation, updated status |
| `docs/findings.md` | Modified — added FND-PROB-2026-01 |
| `plans/active/strat-prob-002/README.md` | Modified — added preset table and report index |
| `plans/active/strat-prob-002/reports/2026-01-29T062136Z/summary.md` | Updated with full results |
| `plans/active/strat-prob-002/reports/2026-01-29T062136Z/*.{json,png}` | Copied from demo_outputs |
| `demo_outputs/probabilistic_vs_mc_{summary.json,loss.png}` | Regenerated with hi_res_b data |

## Tests Run

- `pytest tests/scripts/test_benchmark_probabilistic_cli.py -v` — **4/4 passed**
- `pytest tests/test_probabilistic_simulator.py -v` — **5/5 passed**
- `scripts/benchmark_probabilistic.py --iterations 100 --device cpu --scenario hi_res_b --diagnose-gradients` — completed, artifacts captured

## Key Finding: FND-PROB-2026-01

The probabilistic kernel produces effectively **zero gradients** (mean |grad| = 9.05e-22) for `mosaic_spread_deg` across all tested presets including hi-res. The analytic Gaussian envelope width σ ≫ |ΔQ| for all sampled pixels, making envelope ≈ 1.0 everywhere. Speedup was 2.1× (below 4× target).

## Blockers / Open Questions

1. **Gradient vanishing** remains the critical blocker — needs kernel-level investigation (broadening formula, sampling strategy, or parameterization change).
2. **Speedup below target** — 2.1× vs 4× goal. MC baseline with 5 domains at 128×128 is already fast; advantage may require larger detectors or higher domain counts.
