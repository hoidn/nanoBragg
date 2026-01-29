# STRAT-PROB-002 Report: Hi-Res Benchmark (2026-01-29T062136Z)

## Scenario
- Preset: `hi_res_b` (30Å cell, 0.5Å λ, 60mm distance, 0.05mm pixel, 128×128)
- Iterations: 100, Device: CPU, Gradient diagnostics: enabled

## Results
- **Speedup:** 2.1× (baseline 0.012s/iter, probabilistic 0.006s/iter)
- **Baseline:** spread 0.5° → 0.36°, final loss 7.98e-05, mean |grad| 2.71e-04
- **Probabilistic:** spread stuck at 0.5°, final loss 8.61e-05, mean |grad| 9.05e-22

## Finding: FND-PROB-2026-01
The probabilistic kernel produces effectively zero gradients for `mosaic_spread_deg` across all tested presets. The analytic Gaussian envelope width σ ≫ |ΔQ| for all sampled pixels, making envelope ≈ 1.0 and derivative ≈ 0.

## Implementation Delivered
- Tasks 1-4 of the realignment plan completed
- New CLI: `--scenario`, `--diagnose-gradients`, `--sweep-json`, `--dry-run`, geometry overrides
- New files: `scripts/benchmark_probabilistic_presets.py`, `tests/scripts/test_benchmark_probabilistic_cli.py`
- All 4 CLI tests pass, all 5 probabilistic simulator tests pass

## Artifacts
- `probabilistic_vs_mc_summary.json`, `probabilistic_vs_mc_loss.png`
