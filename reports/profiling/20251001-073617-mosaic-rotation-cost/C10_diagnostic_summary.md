# Phase C10: Mosaic Rotation RNG Cost

**Date:** 2025-10-01 07:36:17

## Configuration
- Device: cpu
- Dtype: torch.float32
- mosaic_domains: 10
- mosaic_spread: 1.0°
- Crystal: 100Å cubic (standard benchmark params)

## Results
- **Mean time per call:** 0.283239 ms
- **Std deviation:** 0.004807 ms
- **Min/Max:** 0.276603 / 0.295694 ms
- **Iterations:** 100
- **Matrix shape:** (10, 3, 3)

## Cost Estimate for 4096² Simulation
- Mosaic rotations generated once per run
- **Estimated total cost:** 0.283 ms

## Analysis
For 4096² detector with 10 mosaic domains:
- Mosaic rotation RNG: ~0.3 ms (0.0% of 600ms target)

**Recommendation:** Mosaic rotation RNG is NOT a significant bottleneck (<5% of warm time). Caching (Plan D7) would provide minimal ROI (~0.3ms savings).
