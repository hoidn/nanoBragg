# Probabilistic Simulator Design (Analytic Mosaic)

Date: 2026-01-29
Owner: Codex (with user direction)
Status: Approved design

## Summary
This design adds a drop-in `ProbabilisticSimulator` that analytically marginalizes
mosaicity using a Gaussian orientation distribution, replacing Monte Carlo
mosaic-domain sampling. The goal is a high-impact, low-grunt-work demo that
shows faster, smoother refinement on the diffuse-spot benchmark while keeping
existing `Simulator` behavior untouched.

## Goals
- Provide a drop-in simulator: `Simulator` -> `ProbabilisticSimulator`.
- Preserve existing APIs and configs (`mosaic_spread_deg` kept, `mosaic_domains`
  ignored as a numerical nuisance parameter).
- Use full metric geometry via reciprocal vectors (works for triclinic).
- Implement angular broadening: sigma scales with |q| to match rotational
  mosaicity physics.
- Produce a "killer plot": loss vs wall-clock time with clear analytic win.

## Non-Goals
- No VI optimizer or ELBO/KL in this pass.
- No modifications to `Simulator` codepath or golden test behavior.
- No multi-image structure-factor refinement in this iteration.

## Architecture
- New module: `src/nanobrag_torch/simulators/probabilistic.py`.
- New class: `ProbabilisticSimulator(Simulator)`.
- New pure kernel: `compute_probabilistic_physics_for_position(...)`.
- Override `_compute_physics_for_position(...)` to call the new kernel and pass
  analytic mosaic spread.
- Override `run(...)` to "stash-and-patch" config (disable mosaic rotations)
  while retaining the true spread for analytic width.

## Probabilistic Physics Kernel
Inputs mirror the existing kernel and add `mosaic_spread_rad` (tensor).

Physics steps:
1) Scattering vector `s` as in the baseline (diffracted - incident) / lambda.
2) Fractional Miller indices: `h = s·a`, `k = s·b`, `l = s·c`.
3) Nearest integer `h0, k0, l0` for structure factor lookup.
4) Lattice factor uses existing SQUARE/ROUND/GAUSS/TOPHAT logic.
5) Mosaic envelope (analytic):
   - `dh = h - h0`, `dk = k - k0`, `dl = l - l0`
   - `dQ = dh*a* + dk*b* + dl*c*`
   - `dr2 = dot(dQ, dQ)`
   - `sigma = |q| * tan(mosaic_spread_rad) + eps`
   - `G = exp(-dr2 / (2*sigma^2))`
6) Intensity: `I = |F_cell * F_latt|^2 * G`.
7) Sum over phi (no mosaic dimension), apply polarization like baseline.

Notes:
- `eps` prevents division by zero near q=0 or spread=0.
- All ops remain differentiable and vectorized across sources.

## Stash-and-Patch run() Strategy
To avoid touching `Simulator` and prevent double-counting mosaicity:
- Stash `true_spread` and `true_domains`.
- Save `true_spread` on `self._analytic_mosaic_spread_deg`.
- Temporarily set `mosaic_spread_deg=0` and `mosaic_domains=1`.
- Call `super().run(...)` to build vectors without mosaic rotations.
- Restore original config in `finally`.

This guarantees the analytic kernel sees the true spread while the geometry
uses a single orientation per phi step.

## Benchmark Workflow
New script: `scripts/benchmark_probabilistic.py` (diffuse demo baseline).

1) Generate ground truth via Monte Carlo with `mosaic_domains=50`.
2) Baseline refinement with `Simulator` and `mosaic_domains=5`.
3) Probabilistic refinement with `ProbabilisticSimulator` (analytic).
4) Time per iteration measured as forward + backward + optimizer step only
   (exclude setup). Use `time.perf_counter()`.
5) Save outputs:
   - `demo_outputs/probabilistic_vs_mc_loss.png`
   - `demo_outputs/probabilistic_vs_mc_summary.json`

Expected outcome: analytic curve reaches lower loss faster and with smoother
monotonic convergence.

## Validation
- Run the benchmark script to generate the PI-facing plot.
- Spot-check with non-cubic parameters (`refinement_demo.py`) to verify
  full-metric geometry.
- Confirm no regressions by keeping baseline simulator untouched.

## Risks and Mitigations
- Sigma scaling could under/over-broaden at extremes: use epsilon and clamp
  mosaic spread to non-negative values.
- Double counting mosaicity: prevented by stash-and-patch in `run()`.
- Device/dtype mismatches: keep tensors on caller device/dtype; avoid
  `.item()` usage in analytic paths.

## Future Extensions
- Structured distributions (mixture of Gaussians) for sparse grains.
- Variational inference on pose distributions.
- Multi-image structure-factor refinement once analytic core is stable.
