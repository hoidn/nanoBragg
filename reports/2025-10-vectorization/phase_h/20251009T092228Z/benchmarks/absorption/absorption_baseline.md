# Detector Absorption Baseline Results

**Date:** 2025-10-09T02:29:46.376629

**Device:** cuda

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
| 256x256 | 5 | 65536 | 0.005523 | 0.005478 | 0.000023 | 11964342.8 | 5.98e-01 |
| 512x512 | 5 | 262144 | 0.005764 | 0.005562 | 0.000018 | 47131718.9 | 1.73e-01 |

## Command

```bash
PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/absorption_baseline.py --device cuda --repeats 200 --sizes 256 512 --thicksteps 5 --outdir reports/2025-10-vectorization/phase_h/20251009T092228Z/benchmarks/absorption
```

## Notes

- Absorption parameters: attenuation depth = 500.0 μm, thickness = 100.0 μm
- Layer semantics: oversample_thick=True (accumulation mode exercises all layers)
- Performance bottleneck: Python loop over `thicksteps` in current implementation
