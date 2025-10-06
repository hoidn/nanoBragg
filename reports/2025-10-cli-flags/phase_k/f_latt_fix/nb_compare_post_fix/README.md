# Phase K3g3 MOSFLM Scaling Parity Evidence

**Date:** 2025-10-06
**Commit:** 192429d
**Plan Task:** CLI-FLAGS-003 Phase K3g3

## Executive Summary

Post-MOSFLM rescale fix (commit 46ba36b), the scaling parity test **FAILED** with poor correlation (0.174) and significant intensity ratio mismatch (1.45×).

## Test Command

```bash
env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg \
  pytest tests/test_cli_scaling.py::TestFlattSquareMatchesC::test_f_latt_square_matches_c -v
```

## Results

### Parity Metrics

| Metric | C Value | PyTorch Value | Ratio/Correlation |
|--------|---------|---------------|-------------------|
| Sum | 1,627,779 | 2,360,700 | 1.45× |
| Max | 27,170 | 57,948 | 2.13× |
| Correlation | - | - | **0.174** |
| Mean Peak Distance | - | - | 122.4 px |
| Max Peak Distance | - | - | 272.4 px |

### Pass/Fail Status

- ✗ **FAILED**: Correlation 0.174 < 0.999 (exit criterion)
- ✗ **FAILED**: Sum ratio 1.45 outside [0.99, 1.01]
- ✗ **FAILED**: Max ratio 2.13 outside tolerance
- ✗ **FAILED**: Peak positions misaligned by >1 pixel

## Artifacts

- `pytest_post_fix.log` — Full pytest output
- `test_metrics_failure.json` — Detailed failure metrics
- `c_image.npy` / `py_image.npy` — Raw float images for inspection
- `nb_compare_post_fix/summary.json` — nb-compare metrics
- `nb_compare_post_fix/*.png` — Visual comparison (C, Py, diff)
- `nb_compare_post_fix/*.bin` — Float image binaries

## Configuration

```
-cell 100 100 100 90 90 90
-default_F 300
-N 10
-lambda 1.0
-distance 100
-detpixels 512
-pixel 0.1
-oversample 1
-phisteps 1
-mosaic_dom 1
```

## Observations

1. **Low correlation (0.174)** indicates images are nearly uncorrelated, suggesting fundamental physics divergence
2. **Intensity excess (1.45×)** shows PyTorch produces significantly brighter images
3. **Peak displacement (122-272 px)** means Bragg peaks appear in different locations
4. **Max ratio (2.13×)** shows hot pixels are over 2× brighter in PyTorch

## Hypothesis

Despite the MOSFLM real-vector rescale fix in commit 46ba36b:
- Base lattice vectors may still diverge (need K3f trace validation)
- Fractional Miller indices may be misaligned
- F_latt calculation may still have errors
- Additional normalization factors may be missing

## Next Actions (per input.md)

1. ✅ Run parity pytest — **COMPLETE** (captured evidence)
2. ✅ Run nb-compare — **COMPLETE** (visual artifacts archived)
3. ⬜ Regenerate traces & scaling analysis (analyze_scaling.py)
4. ⬜ Update markdown summaries (scaling_chain.md)
5. ⬜ Log fix_plan attempt with metrics
6. ⬜ Only request supervisor review after completing checklist

## References

- Plan: `plans/active/cli-noise-pix0/plan.md` Phase K3g3
- Test: `tests/test_cli_scaling.py::TestFlattSquareMatchesC::test_f_latt_square_matches_c`
- Prior attempt: Attempt #43 (commit 46ba36b MOSFLM rescale implementation)
- Exit criteria: correlation ≥0.999, sum_ratio 0.99–1.01, peak distance ≤1 px
