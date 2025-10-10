# Phase E6 Summary — C Tap 4 (F_cell default usage)

**Date:** 2025-10-10T10:38:11Z
**Loop:** ralph Attempt #26 (VECTOR-PARITY-001 Phase E6)
**Status:** ✅ SUCCESS

## Objective
Capture C-side F_cell lookup statistics for pixels (0,0) and (2048,2048) with oversample=2 to compare against PyTorch Tap 4 metrics (Attempt #25).

## Execution Summary

### Instrumentation
- **File Modified:** `golden_suite_generator/nanoBragg.c:3337-3354`
- **Tap Logic:** Added `#pragma omp critical` block after F_cell assignment (line 3330) to emit TRACE_C_TAP4 lines for debug pixels
- **Captured Fields:** pixel coords, subpixel coords, source/mos/phi indices, h/k/l (float + rounded), F_cell value, out-of-bounds flag, default_F usage flag, zero_F flag
- **Build:** Instrumented binary compiled with `-O2 -fno-fast-math -ffp-contract=off -DTRACING=1 -fopenmp`

### Command Executed
```bash
./golden_suite_generator/nanoBragg \
  -default_F 100 \
  -cell 100 100 100 90 90 90 \
  -lambda 0.5 \
  -distance 500 \
  -detpixels 4096 \
  -pixel 0.05 \
  -N 5 \
  -oversample 2 \
  -floatfile /tmp/tap4.bin
```

**Runtime:** ~1 minute (oversample=2, 4096² detector)
**Output:** 287 lines total, 8 TRACE_C_TAP4 lines (4 subpixels × 2 pixels)

### Metrics (from tap4_metrics.json)

#### Edge Pixel (0,0)
```json
{
  "total_lookups": 4,
  "out_of_bounds_count": 4,
  "zero_f_count": 0,
  "default_f_count": 4,
  "hkl_min": [-7.900663, 39.347118, -39.356724],
  "hkl_max": [-7.897033, 39.356724, -39.347118],
  "mean_f_cell": 100.0
}
```

#### Centre Pixel (2048,2048)
```json
{
  "total_lookups": 4,
  "out_of_bounds_count": 0,
  "zero_f_count": 4,
  "default_f_count": 0,
  "hkl_min": [-1e-06, 0.005, -0.015],
  "hkl_max": [-0.0, 0.015, -0.005],
  "mean_f_cell": 0.0
}
```

## Key Findings

1. **Edge Pixel (0,0) Behaviour:**
   - All 4 subpixel lookups are **out of bounds** (h≈-8, k≈39, l≈-39)
   - All 4 use `default_F=100` (matches PyTorch Attempt #25)
   - No zero F_cell values

2. **Centre Pixel (2048,2048) Behaviour:**
   - All 4 subpixel lookups are **in bounds** (h≈0, k≈0.005-0.015, l≈-0.005--0.015)
   - All 4 F_cell values are **zero** (HKL file not provided, so Fhkl array contains zeros)
   - No default_F usage (lookups succeeded but returned stored zero)

3. **C ↔ PyTorch Parity:**
   - **CONFIRMED:** Edge pixel out-of-bounds behaviour matches (PyTorch `out_of_bounds_count=0` was measuring interpolation failures, NOT HKL array bounds)
   - **CONFIRMED:** default_F=100 applied uniformly at edges in both implementations
   - **DIFFERENCE IDENTIFIED:** Centre pixel F_cell=0 in C vs F_cell=100 in PyTorch (Attempt #25)
     - **Root Cause:** PyTorch trace script may be using `default_F` fallback for ALL lookups when no HKL file provided, while C correctly initializes Fhkl array to zeros and returns those stored values

## Artifacts
- `tap4_raw.log` — Full C stdout (287 lines)
- `tap4_metrics.json` — Processed summary statistics
- `commands.txt` — Exact reproduction command
- `env/trace_env.txt` — Git SHA, date, user

## Cleanup
- ✅ Instrumentation removed from `golden_suite_generator/nanoBragg.c`
- ✅ Clean binary rebuilt (133KB, no tap code)
- ✅ Pytest collection verified (692 tests collected)

## Next Actions (Phase E7)
1. Compare this C tap data vs PyTorch Attempt #25 (`f_cell_summary.md`)
2. Draft `f_cell_comparison.md` documenting the centre-pixel zero vs default_F discrepancy
3. Decide whether to escalate to Tap 5 (pre-normalisation intensity) or investigate the F_cell=0 centre pixel puzzle
4. Update `docs/fix_plan.md` with E7 Next Actions based on comparison findings

## Exit Criteria Met
- [x] C Tap 4 metrics captured for pixels (0,0) and (2048,2048) with oversample=2
- [x] JSON output matches PyTorch tap schema (total_lookups, out_of_bounds_count, zero_f_count, mean_f_cell, HKL bounds)
- [x] Commands and environment metadata archived
- [x] Instrumentation removed and clean build verified
- [x] Pytest collection clean (692 tests)
