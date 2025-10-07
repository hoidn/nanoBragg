# Detector Absorption Baseline Results

**Date:** 2025-10-07T00:09:35.768044

**Device:** cuda

**Dtype:** torch.float32

## Environment

- Python: 3.13.7
- PyTorch: 2.8.0+cu128
- CUDA Available: True
- GPU: NVIDIA GeForce RTX 3090

## Configuration

- Attenuation Depth: 500 μm
- Detector Thickness: 100 μm
- Oversample Thick: True (accumulation mode)

## Results

| Size | Layers | Pixels | Cold (s) | Warm Mean (s) | Warm Std (s) | Throughput (px/s) | Mean Intensity |
|------|--------|--------|----------|---------------|--------------|-------------------|----------------|
| 256x256 | 5 | 65536 | 0.005815 | 0.005787 | 0.000057 | 11324656.0 | 5.98e-01 |
| 512x512 | 5 | 262144 | 0.005953 | 0.005851 | 0.000039 | 44804998.9 | 1.73e-01 |

## Command

```bash
PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/absorption_baseline.py --sizes 256 512 --repeats 5 --device cuda
```

## Notes

- Absorption parameters: attenuation depth = 500.0 μm, thickness = 100.0 μm
- Layer semantics: oversample_thick=True (accumulation mode exercises all layers)
- Performance bottleneck: Python loop over `thicksteps` in current implementation
