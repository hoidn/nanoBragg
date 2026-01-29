# Hi-Res B Diagnostics Summary

**Scenario:** hi_res_b (30Å cell, 0.5Å wavelength, 60mm distance, 0.05mm pixels, 128×128)
**Spread:** 0.5°  |  **Device:** cpu  |  **dtype:** float32

## Key Findings

| Metric | Mean | Min | Max |
|--------|------|-----|-----|
| `delta_q_norm` | 1.26e-2 | 1.18e-3 | 2.29e-2 |
| `sigma_q` | 7.12e+6 | 1.03e+5 | 1.32e+7 |
| `delta_q_over_sigma` | **2.32e-9** | 2.75e-10 | 1.15e-8 |
| `gaussian_envelope` | **1.0** | 1.0 | 1.0 |

## Gradient Probe

- FD gradient (±0.05°): **0.0**
- loss_plus = loss_minus = 720.71

## Root Cause

`sigma = |q| * tan(spread)` produces sigma in **m⁻¹** units (~10⁶–10⁷) while `delta_q_norm` (= `|dQ|` in reciprocal Å⁻¹ space) is ~10⁻²Å⁻¹. The ratio `|dQ|/σ` is ~10⁻⁹, making `exp(-ratio²/2) ≈ 1.0` for all pixels. The Gaussian envelope is completely flat → no gradient signal.

**Fix (Task 3):** Use angular deviation `Δθ = |dQ|/|G|` with `σ_θ = mosaic_spread_rad`, where `G = h₀a* + k₀b* + l₀c*`. This normalizes to a dimensionless ratio of order ~1.
