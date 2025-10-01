# AT-PARALLEL-012 Phase A3: Plateau Fragmentation Analysis

**Date:** 2025-09-30
**Test Case:** simple_cubic (1024×1024, λ=6.2Å, cubic cell)
**ROI:** 20×20 pixels at beam center (512, 512)

## Findings

| Implementation | Dtype | Unique Values | Fragmentation Ratio |
|----------------|-------|---------------|---------------------|
| C golden | float32 | 66 | 1.00 (baseline) |
| PyTorch | float32 | 324 | **4.91×** |
| PyTorch | float64 | 301 | 4.56× |

## Analysis

PyTorch float32 produces **4.91× more unique intensity values** than C float32 in the beam-center plateau region. This fragmentation breaks scipy.ndimage.maximum_filter's plateau tie-breaking, causing peak detection to miss ~7 peaks (43/50 vs spec requirement of ≥48/50).

## Artifacts

- CSV data: `phase_a3_plateau_fragmentation.csv`
- Histogram: `phase_a3_plateau_histogram.png`
- Value distribution: `phase_a3_value_distribution.png`

## Next Actions

Per plan Phase B3: Evaluate mitigation strategies (single-stage reduction, compensated summation, peak clustering) to reduce fragmentation ratio to <2×.
