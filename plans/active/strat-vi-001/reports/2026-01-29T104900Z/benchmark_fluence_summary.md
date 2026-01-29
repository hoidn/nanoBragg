# Canonical VI benchmark with adaptive Poisson scaling

- Command: `python scripts/benchmark_vi_mosaic.py --iterations 150 --observation-mean 25.0 --observation-normalization mean --observation-seed 321 --kl-weight-start 0.2 --kl-weight-end 1.0 --kl-warmup-steps 120`
- Artifacts: `vi_vs_mc_loss.png`, `vi_vs_mc_summary.json`, `vi_observation_stats.json`, `benchmark/vi_diagnostics.json`
- Key metrics:
  - VI σ final (deg): 0.103 (target 2.0°) — **FAILED ≥1.5° criterion**
  - MC σ final (deg): 0.024
  - Analytic σ final (deg): 3.214 (overshoots)
  - VI loss first / last: -79386.4 / -79817.9 (ELBO improving)
  - MC loss first / last: 2278.1 / 2277.2
  - Observation stats: mean=24.97, max=234.0, scale_mode=mean, scale=30.88
- Notes: σ did NOT reach ≥1.5° by iter 150. The VI σ collapsed toward zero (0.103°), suggesting the KL divergence or likelihood gradient balance is incorrect — the model prefers a narrow posterior. The analytic baseline overshoots to 3.21°, confirming the underlying gradient signal exists but VI optimization dynamics differ. Next diagnostic: log per-iteration likelihood vs KL decomposition to identify whether the KL term is too weak or the likelihood gradient pushes σ down.
