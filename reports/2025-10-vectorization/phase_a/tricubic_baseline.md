# Tricubic Interpolation Baseline Results

**Date:** 2025-10-07T00:09:17.633094

**Device:** cuda

**Dtype:** torch.float32

## Environment

- Python: 3.13.7
- PyTorch: 2.8.0+cu128
- CUDA Available: True
- GPU: NVIDIA GeForce RTX 3090

## Results

**Note:** Current implementation only supports scalar interpolation calls. Benchmarks measure overhead of 100 scalar get_structure_factor() calls in a loop.

| Size Param | Scalar Calls | Cold (s) | Warm Mean (s) | Warm Std (s) | Time/Call (μs) | Calls/sec |
|------------|--------------|----------|---------------|--------------|----------------|----------|
| 256 | 100 | 0.558660 | 0.554879 | 0.001995 | 5548.79 | 180.2 |
| 512 | 100 | 0.551459 | 0.552792 | 0.000441 | 5527.92 | 180.9 |

## Command

```bash
PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/tricubic_baseline.py --sizes 256 512 --repeats 5 --device cuda
```
