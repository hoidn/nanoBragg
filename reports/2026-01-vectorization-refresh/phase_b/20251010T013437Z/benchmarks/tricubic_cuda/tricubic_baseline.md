# Tricubic Interpolation Baseline Results

**Date:** 2025-10-09T18:37:13.631499

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
| 256 | 100 | 0.572392 | 0.568214 | 0.001635 | 5682.14 | 176.0 |
| 512 | 100 | 0.566002 | 0.569776 | 0.001613 | 5697.76 | 175.5 |

## Command

```bash
PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/tricubic_baseline.py --sizes 256 512 --repeats 200 --device cuda --outdir reports/2026-01-vectorization-refresh/phase_b/20251010T013437Z/benchmarks/tricubic_cuda
```
