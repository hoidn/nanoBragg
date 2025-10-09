# Tricubic Interpolation Baseline Results

**Date:** 2025-10-08T20:44:26.165185

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
| 256 | 100 | 0.146268 | 0.144778 | 0.000703 | 1447.78 | 690.7 |
| 512 | 100 | 0.144051 | 0.145056 | 0.000449 | 1450.56 | 689.4 |

## Command

```bash
PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/tricubic_baseline.py --sizes 256 512 --repeats 200 --device cpu --outdir reports/2025-10-vectorization/phase_e/perf//cpu
```
