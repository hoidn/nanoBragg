# Sprint 4 Bandwidth Baseline

STAMP: 20260129T051604Z

## Baseline context (isolated bandwidth test)
- ratio (2048 vs 512): ~0.67 (from rounded log values 0.3/0.2 GB/s)
  - 512×512: 0.020s, ~0.3 GB/s
  - 1024×1024: 0.083s, ~0.3 GB/s
  - 2048×2048: 0.565s, ~0.2 GB/s

## Stressed context (after full module run)
- ratio (2048 vs 512): ~0.67 (from rounded log values 0.3/0.2 GB/s)
  - 512×512: 0.023s, ~0.3 GB/s
  - 1024×1024: 0.085s, ~0.3 GB/s
  - 2048×2048: 0.566s, ~0.2 GB/s

## Additional standalone measurements (3 runs)
- Run 1: ratio=0.7051 (512=0.302, 2048=0.213 GB/s)
- Run 2: ratio=0.6299 (512=0.329, 2048=0.207 GB/s)
- Run 3: ratio=0.6334 (512=0.334, 2048=0.211 GB/s)

## Post-stress failure observation
- One run measured ratio=0.5553 (512=0.304, 2048=0.169 GB/s)

## Threshold derivation
- Observed minimum ratio: 0.5553
- Threshold: 0.45 (~80% of worst-case, replacing legacy 0.50)
- Constant: `BANDWIDTH_RATIO_THRESHOLD = 0.45` in `tests/test_at_perf_003.py`
