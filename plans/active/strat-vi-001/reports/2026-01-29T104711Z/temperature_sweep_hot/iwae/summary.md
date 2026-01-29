# IWAE + Temperature Sweep Summary (T={1,2,4,8}, k=8)

**Timestamp:** 2026-01-29T104711Z
**Plan:** `docs/plans/2026-01-29-vi-temperature-iwae-followup.md` Task 2

## Configuration
- Iterations: 25, k-samples: 8, detector: 32x32
- Observation: mean=25.0, normalization=mean, seed=321
- Objective: IWAE
- Temperatures: 1.0, 2.0, 4.0, 8.0

## Results

| T | σ_mean (°) | |∇μ| | |∇ρ| | ll/kl grad ratio |
|---|-----------|------|------|-----------------|
| 1.0 | 0.813 | 28.4 | 13.3 | 99.7 |
| 2.0 | 0.814 | 57.0 | 25.9 | 199.9 |
| 4.0 | 0.814 | 114.3 | 51.1 | 400.3 |
| 8.0 | 0.814 | 228.9 | 101.3 | 801.6 |

## Key Findings
- IWAE yields marginally higher σ (~0.814° vs 0.808° standard) — negligible difference.
- IWAE produces much higher |∇ρ| (e.g., 101 at T=8 vs 15 for standard), but this does not translate to better σ recovery.
- No configuration reached σ ≥ 1.2°; the 150-iter canonical benchmark was **NOT triggered**.

## Conclusion
Neither IWAE nor hotter temperatures resolve the structural posterior collapse. The σ plateau at ~0.81° is a landscape geometry issue. The benchmark skip is justified.
