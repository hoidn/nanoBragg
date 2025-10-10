# Phase B1 Benchmark + Parity Summary

## Benchmark Metrics (from benchmark_detailed.py)
- Bundle: reports/benchmarks/20251009-195918
- Correlation (warm): 0.7211752710777161
- Speedup (warm): 1.1891088131889507x
- PyTorch time (warm): 0.6692593097686768s
- C time: 0.7958221435546875s

## nb-compare Metrics
- correlation: 0.05949746740145082
- rmse: 5.522035598754883
- c_sum: 24784.927734375
- py_sum: 5803630.0
- sum_ratio: 234.15965270996094

## Acceptance Thresholds (specs/spec-a-core.md:151)
- Correlation: ≥0.999 (normative)
- |sum_ratio−1|: ≤5e-3 (normative)

## Status
- Correlation: ❌ FAIL (0.059497)
- Sum ratio: ❌ FAIL (|234.159653 - 1.0| = 233.159653)

**BLOCKING**: Thresholds not met. Phase B2/B3 trace triage required.

## Notes
- Benchmark correlation (0.7211752710777161) disagrees with nb-compare correlation (0.059497) by 12.1x
- Sum ratio 234.16 indicates PyTorch generating ~234x total intensity vs C
- This suggests catastrophic normalization or scaling bug in PyTorch implementation
- Next: Phase B2 pytest selectors + Phase C trace debugging
