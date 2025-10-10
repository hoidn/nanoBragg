# Tricubic Interpolation Baseline Results

**Date:** 2025-10-09T18:36:04.899569

**Device:** cpu

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
| 256 | 100 | 0.147750 | 0.144783 | 0.000658 | 1447.83 | 690.7 |
| 512 | 100 | 0.143965 | 0.145470 | 0.000394 | 1454.70 | 687.4 |

## Command

```bash
PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/tricubic_baseline.py --sizes 256 512 --repeats 200 --device cpu --outdir reports/2026-01-vectorization-refresh/phase_b/20251010T013437Z/benchmarks/tricubic_cpu
```
