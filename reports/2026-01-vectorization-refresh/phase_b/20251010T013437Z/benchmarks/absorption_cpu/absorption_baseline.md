# Detector Absorption Baseline Results

**Date:** 2025-10-09T18:41:11.851994

**Device:** cpu

**Dtype:** torch.float32

## Environment

- Python: 3.13.5
- PyTorch: 2.7.1+cu126
- CUDA Available: True
- GPU: NVIDIA GeForce RTX 3090

## Configuration

- Attenuation Depth: 500 μm
- Detector Thickness: 100 μm
- Oversample Thick: True (accumulation mode)

## Results

| Size | Layers | Pixels | Cold (s) | Warm Mean (s) | Warm Std (s) | Throughput (px/s) | Mean Intensity |
|------|--------|--------|----------|---------------|--------------|-------------------|----------------|
| 256x256 | 5 | 65536 | 2.645062 | 0.004718 | 0.000195 | 13891193.7 | 5.98e-01 |
| 512x512 | 5 | 262144 | 0.637735 | 0.022901 | 0.000729 | 11446619.5 | 1.73e-01 |

## Command

```bash
PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/absorption_baseline.py --sizes 256 512 --repeats 200 --device cpu --outdir reports/2026-01-vectorization-refresh/phase_b/20251010T013437Z/benchmarks/absorption_cpu
```

## Notes

- Absorption parameters: attenuation depth = 500.0 μm, thickness = 100.0 μm
- Layer semantics: oversample_thick=True (accumulation mode exercises all layers)
- Performance bottleneck: Python loop over `thicksteps` in current implementation
