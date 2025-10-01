# Phase B Task B6: Warm-Run Reproducibility Study

**Configuration:** 4096×4096, CPU, float32, 5-iteration averages
**Runs:** 10
**Target:** speedup_warm ≥ 1.0 (PyTorch ≤ C)

## Summary Statistics

| Metric | Mean | Median | StdDev | Min | Max |
|--------|------|--------|--------|-----|-----|
| PyTorch warm (s) | 0.6170 | 0.6095 | 0.0183 | 0.5990 | 0.6570 |
| C warm (s) | 0.5092 | 0.5070 | 0.0097 | 0.4950 | 0.5250 |
| Speedup warm | 0.8280 | 0.8400 | 0.0326 | 0.7800 | 0.8800 |
| Correlation | 1.0000000000 | - | - | 1.0000000000 | - |

## Analysis

- **Mean slowdown:** PyTorch is 1.21× slower than C
- **Speedup:** 0.8280 (target: ≥1.0)
- **Variability:** CV = 3.9%
- **Numerical accuracy:** correlation = 1.0000000000

❌ **TARGET NOT MET:** Mean speedup < 1.0
PyTorch is consistently ~1.21× slower than C.

✅ **High reproducibility:** CV < 5% indicates stable measurements

## Individual Runs

| Run | PyTorch (s) | C (s) | Speedup | Correlation |
|-----|-------------|-------|---------|-------------|
| 1 | 0.5990 | 0.5250 | 0.8800 | 1.0000000000 |
| 2 | 0.6110 | 0.5250 | 0.8600 | 1.0000000000 |
| 3 | 0.6020 | 0.5040 | 0.8400 | 1.0000000000 |
| 4 | 0.6200 | 0.5070 | 0.8200 | 1.0000000000 |
| 5 | 0.6060 | 0.5070 | 0.8400 | 1.0000000000 |
| 6 | 0.6270 | 0.4950 | 0.7900 | 1.0000000000 |
| 7 | 0.6570 | 0.5120 | 0.7800 | 1.0000000000 |
| 8 | 0.6040 | 0.5040 | 0.8400 | 1.0000000000 |
| 9 | 0.6080 | 0.5120 | 0.8400 | 1.0000000000 |
| 10 | 0.6360 | 0.5010 | 0.7900 | 1.0000000000 |

## Conclusion

Phase B target NOT achieved. PyTorch is 1.21× slower than C.
Proceed to Phase C (diagnostic experiments) to identify and address remaining bottlenecks.
