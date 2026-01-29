# Report: 2026-01-29T085512Z — Poisson Observation Benchmark

Ran canonical VI benchmark with Poisson-sampled observations (`--iterations 150 --fluence 1e13 --observation-seed 321 --kl-weight-start 0.2 --kl-weight-end 1.0 --kl-warmup-steps 120`). The fluence_scale (~7.9e-16) zeroed all observations, causing VI to diverge to σ=7.49° instead of converging to the 2.0° target. MC baseline reached 1.35°. The fluence normalization formula needs correction. See [benchmark_fluence_summary.md](./benchmark_fluence_summary.md) and [vi_observation_stats.json](./vi_observation_stats.json).

**Acceptance criterion (σ ≥ 1.5° by 150 iters): NOT MET.** Blocker is the fluence scaling formula, not the VI algorithm itself.
