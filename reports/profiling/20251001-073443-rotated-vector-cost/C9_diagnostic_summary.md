# Phase C9: Rotated Vector Regeneration Cost

**Date:** 2025-10-01 07:34:43

## Configuration
- Device: cpu
- Dtype: torch.float32
- phi_steps: 1
- mosaic_domains: 1
- Crystal: 100Å cubic, N=(5,5,5)

## Results
- **Mean time per call:** 1.563500 ms
- **Std deviation:** 0.012065 ms
- **Min/Max:** 1.533539 / 1.614880 ms
- **Iterations:** 100
- **Vector shapes:** ['(tensor([[[ 1.0000e+02, -4.3711e-06, -4.3711e-06]]]), tensor([[[ 0.0000e+00,  1.0000e+02, -4.3711e-06]]]), tensor([[[  0.0000,   0.0000, 100.0000]]]))', '(tensor([[[0.0100, 0.0000, 0.0000]]]), tensor([[[4.3711e-10, 1.0000e-02, 0.0000e+00]]]), tensor([[[4.3711e-10, 4.3711e-10, 1.0000e-02]]]))']

## Cost Estimate for 4096² Simulation
- Total calls: 1 phi × 1 mosaic = 1
- **Estimated total cost:** 1.564 ms

## Analysis
For 4096² detector with baseline config (phi_steps=1, mosaic=1):
- Rotated vector regeneration: ~1.6 ms (0.3% of 600ms target)

**Recommendation:** Rotated vector regeneration is NOT a significant bottleneck (<5% of warm time). Caching (Plan D6) would provide minimal ROI (~1.6ms savings).
