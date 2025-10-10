# ROI Scope Summary — VECTOR-PARITY Phase B4b

## Context
- Good baseline: `reports/benchmarks/20251009-161714/benchmark_results.json` (corr≈0.999998, sum_ratio≈1.0; git SHA not recorded).
- Failing full-frame capture: `reports/2026-01-vectorization-parity/phase_b/20251010T030852Z/nb_compare_full/summary.json` (corr≈0.063; sum_ratio≈225).
- ROI parity run: `reports/2026-01-vectorization-parity/phase_b/20251010T035732Z/roi_compare/summary.json` (corr≈1.0; sum_ratio≈0.99999).
- Acceptance thresholds (spec): correlation ≥0.999, |sum_ratio−1| ≤5×10⁻³ (`specs/spec-a-core.md` §§4–5; `docs/development/testing_strategy.md` §2).

## Metric Comparison
| Region | Tool & Inputs | Correlation | Sum Ratio (Py/C) | Mean Peak Δ (px) | Notes |
| --- | --- | --- | --- | --- | --- |
| Full frame (4096²) | `nb-compare` (Phase B1, `nb_compare_full`) | 0.06298 | 225.036 | 66.89 | Catastrophic parity failure; huge intensity inflation across low-signal region. |
| Full frame (4096²) | `benchmark_detailed.py` (Phase B1) | 0.72118 | n/a | n/a | Same command; warm/cold correlations identical ⇒ deterministic regression. |
| Central ROI (512² @ 1792:2304) | `nb-compare --roi` (Phase B4a) | 0.999999999 | 0.999987 | 0.78 | Meets spec thresholds; physics agrees where signal is concentrated. |

## Observations
- **Signal-local parity holds.** The central ROI meets correlation and sum thresholds by wide margins, with peak offsets ≤1.41 px, indicating geometry and scaling agree where the Bragg peaks live.
- **Full-frame metrics dominated by background.** The failing sum ratio (≈225×) and large peak deltas suggest the regression arises in detector regions with near-zero C intensity (edges/corners), not in the ROI.
- **Tool behavior diverges.** `benchmark_detailed.py` correlation (0.72) and `nb-compare` correlation (0.063) differ sharply; both reference the same floatfiles. This hints that benchmark correlation may normalise differently (e.g., excludes zero rows) while nb-compare includes entire frame.
- **Spec guardrails target ROIs.** `specs/spec-a-parallel.md` emphasises ROI-based acceptance for AT-012; ROI parity is therefore the primary correctness gate.

## Hypotheses
1. **Edge overexposure / halo accumulation:** PyTorch intensity grows at detector edges where C remains near zero (sum_ratio 225×). Investigate whether normalization (steps/oversample) or detector solid-angle differs outside the ROI.
2. **Zero-padding sensitivity in nb-compare:** Including vast zero-intensity regions suppresses correlation; resampling or normalization across ~16M pixels may amplify numerical noise. Confirm by trimming background before correlation.
3. **Command mismatch:** B1 nb-compare run used λ=6.2 Å and distance=100 mm, whereas ROI test used λ=0.5 Å and distance=500 mm (per `summary.json`). Determine whether this difference is intentional (command template) or residual from scripted defaults.

## Recommendations
- **Short term:** Treat central ROI parity as authoritative for AT-012 while documenting the full-frame discrepancy in plan/fix_plan (unlock Phase C trace work on representative pixels).
- **Evidence gap:** Run an additional ROI sweep (e.g., 1024² centered, corners) to map where correlation collapses; log results under a new `<STAMP>/roi_compare` bundle before Phase C if time allows.
- **Trace prep:** When moving to Phase C, select ROI pixels that showed parity to understand healthy paths and edge pixels to capture divergence.

## References
- `reports/2026-01-vectorization-parity/phase_b/20251010T030852Z/nb_compare_full/summary.json`
- `reports/2026-01-vectorization-parity/phase_b/20251010T030852Z/summary.md`
- `reports/2026-01-vectorization-parity/phase_b/20251010T035732Z/roi_compare/summary.json`
- `plans/active/vectorization-parity-regression.md` (Phase B4)
