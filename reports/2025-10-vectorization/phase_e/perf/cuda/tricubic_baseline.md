# Tricubic Interpolation Baseline Results

**Date:** 2025-10-08T20:45:41.601015

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
| 256 | 100 | 0.568271 | 0.557436 | 0.001673 | 5574.36 | 179.4 |
| 512 | 100 | 0.557162 | 0.559759 | 0.001660 | 5597.59 | 178.6 |

## Command

```bash
PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/tricubic_baseline.py --sizes 256 512 --repeats 200 --device cuda --outdir reports/2025-10-vectorization/phase_e/perf//cuda
```
