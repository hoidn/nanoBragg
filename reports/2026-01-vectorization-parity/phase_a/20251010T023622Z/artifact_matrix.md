# Artifact Matrix

| run | correlation_warm | sum_ratio | speedup_warm | git_sha | notes |
| --- | --- | --- | --- | --- | --- |
| good-20251009-161714 | 0.9999984741695391 | n/a | 0.7762269992649153 | missing | path=reports/benchmarks/20251009-161714/benchmark_results.json |
| 20251009T070458Z | 0.7211752710777161 | n/a | 0.780127049910952 | None | path=reports/2026-01-vectorization-gap/phase_b/20251009T070458Z/profile/benchmark_results.json |
| 20251009T094735Z | 0.7211752710777161 | n/a | 0.7948134279077356 | 8f1b96b76530259e5ce4a47618bec82982b525bb | path=reports/2026-01-vectorization-gap/phase_b/20251009T094735Z/profile/benchmark_results.json |
| 20251009T095913Z | 0.7211752710777161 | n/a | 0.7883255430454444 | None | path=reports/2026-01-vectorization-gap/phase_b/20251009T095913Z/profile/benchmark_results.json |
| 20251010T020149Z | 0.7211752710777161 | n/a | 1.2279878060187097 | None | path=reports/2026-01-vectorization-gap/phase_b/20251010T020149Z/failed/benchmark_results.json |
| 20251010T021229Z | 0.7211752710777161 | n/a | 1.1791907349115522 | 12cbad7f6a0912104701c8105e4d22ee3280f054 | path=reports/2026-01-vectorization-gap/phase_b/20251010T021229Z/failed/benchmark_results.json |
| 20251010T022314Z | 0.7211752710777161 | n/a | 1.1502583053632323 | 22ea5c188f6a7c9f38f18228dd1b0e27c14e5290 | path=reports/2026-01-vectorization-gap/phase_b/20251010T022314Z/failed/benchmark_results.json |

## Key Findings

1. **Deterministic Failure**: All 6 failing runs show **identical** correlation = 0.7211752710777161, suggesting a systematic bug rather than randomness.
2. **Good vs Bad Gap**: Known-good run achieved correlation 0.9999985 (>0.999 threshold), failing runs are 0.721 (~28% worse).
3. **Git Provenance**: 3 of 6 failing runs have git_sha recorded (8f1b96b, 12cbad7, 22ea5c1); good run lacks SHA.
4. **Sum Ratio**: All runs report `sum_ratio: n/a` — metric not captured in these benchmarks.
5. **Speedup Variability**: Warm speedups range from 0.776 (good) to 1.228 (failing 20251010T020149Z), but correlation is uncorrelated with speed.

## Open Questions
- [ ] Capture git SHA for reports/benchmarks/20251009-161714 (not recorded) — likely from 2025-12-24..2025-12-26 range per plan D1.
- [ ] Confirm whether any smaller ROI bundles exist for comparison (Phase B3 task).
- [ ] Why is sum_ratio missing? Should Phase B runs include `--compare` flag to compute it?
- [ ] Are the 3 failing commits (8f1b96b, 12cbad7, 22ea5c1) on the same branch? Check git history for regression window.
