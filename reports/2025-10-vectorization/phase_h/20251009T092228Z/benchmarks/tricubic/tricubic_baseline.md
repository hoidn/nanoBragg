# Tricubic Interpolation Baseline Results

**Date:** 2025-10-09T02:25:47.424036

**Device:** cuda

**Dtype:** torch.float32

## Environment

- Python: 3.13.5
- PyTorch: 2.7.1+cu126
- CUDA Available: True
- GPU: NVIDIA GeForce RTX 3090

## Results

**Note:** Current implementation only supports scalar interpolation calls. Benchmarks measure overhead of 100 scalar get_structure_factor() calls in a loop.

| Size Param | Scalar Calls | Cold (s) | Warm Mean (s) | Warm Std (s) | Time/Call (μs) | Calls/sec |
|------------|--------------|----------|---------------|--------------|----------------|----------|
| 256 | 100 | 0.570113 | 0.564765 | 0.001374 | 5647.65 | 177.1 |
| 512 | 100 | 0.562829 | 0.565298 | 0.001379 | 5652.98 | 176.9 |

## Command

```bash
PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/tricubic_baseline.py --device cuda --repeats 200 --sizes 256 512 --outdir reports/2025-10-vectorization/phase_h/20251009T092228Z/benchmarks/tricubic
```
