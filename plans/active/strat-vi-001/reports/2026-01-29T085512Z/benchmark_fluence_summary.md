# Canonical VI benchmark with Poisson observations

- Command: `python scripts/benchmark_vi_mosaic.py --iterations 150 --fluence 1e13 --observation-seed 321 --kl-weight-start 0.2 --kl-weight-end 1.0 --kl-warmup-steps 120`
- Artifacts: `vi_vs_mc_loss.png`, `vi_vs_mc_summary.json`, `vi_observation_stats.json`
- Key metrics:
  - VI final sigma: 7.49 deg (target: 2.0 deg) -- **DIVERGED**
  - MC final sigma: 1.35 deg
  - VI loss trajectory: 277.4 -> 93.3
  - MC loss trajectory: 0.0188 -> 0.0175
  - Observation mean_counts: 0.0, max_counts: 0.0
  - Fluence scale: 7.94e-16
- **Finding:** The fluence_scale of ~8e-16 (= 1e13 / BeamConfig().fluence) is far too small. Multiplying raw simulator intensities by this factor produces expected counts < 1 everywhere, so `torch.poisson` returns all zeros. The VI optimizer receives a zero-observation target, causing sigma to diverge. The fluence scaling formula needs revisiting: either the default BeamConfig().fluence (~1.26e28) is not the correct normalization denominator, or the raw intensities need pre-normalization before applying the fluence scale.
