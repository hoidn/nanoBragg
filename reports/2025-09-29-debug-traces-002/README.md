# AT-PARALLEL-002 Debug Traces - Pixel (64, 79) Analysis

## Overview

This directory contains debug traces and analysis for AT-PARALLEL-002 pixel-size failures, focusing on pixel (64,79) in the 0.4mm pixel size case.

## Contents

1. **`c_trace_pixel_64_79.log`** - C code trace output for pixel (64, 79)
2. **`py_trace_pixel_64_79.log`** - Initial PyTorch trace (before bugfix)
3. **`py_trace_detailed_pixel_64_79.log`** - Detailed PyTorch trace (with buggy Miller calculation)
4. **`py_trace_FIXED_pixel_64_79.log`** - Final PyTorch trace (after bugfix)
5. **`comparison_pixel_64_79.md`** - Initial comparison showing unit mismatch hypothesis
6. **`comparison_pixel_64_79_DETAILED.md`** - Detailed comparison with unit analysis
7. **`FINAL_ANALYSIS.md`** - Complete analysis with root cause and fix
8. **`README.md`** - This file

## Key Findings

### Bug Discovered and Fixed

**Location:** `src/nanobrag_torch/simulator.py`, method `_apply_debug_output`

**Issue:** The trace code was using reciprocal-space vectors (`rot_a_star`) instead of real-space vectors (`rot_a`) for Miller index calculation.

**Fix:**
1. Added `rot_a, rot_b, rot_c` parameters to `_apply_debug_output()`
2. Updated trace calculation to use real-space vectors: `h = dot(scattering, rot_a)`
3. Added detailed comments explaining the nanoBragg.c convention

**Result:** After the fix, all intermediate values match perfectly between C and PyTorch:
- Miller indices: ✓
- F_latt components: ✓
- I_before_scaling: ✓

### Remaining Mystery

Despite perfect single-pixel agreement, the test still reports:
- **pixel-0.4mm**: sum_ratio=1.1, corr=0.9970<0.9999 (FAIL)

This indicates:
1. The trace comparison validates individual pixel calculations
2. The test failure is due to a different issue affecting aggregate statistics
3. Likely causes: coordinate system shift, edge effects, or accumulation differences

## Test Configuration

- **Pixel**: (slow=64, fast=79) - 15 pixels off-center
- **Pixel size**: 0.4mm
- **Detector**: 256×256 pixels
- **Beam center**: (25.6mm, 25.6mm)
- **Distance**: 100mm
- **Crystal**: 100Å cubic, N=5
- **Wavelength**: 6.2Å
- **Convention**: MOSFLM

## Trace Values (Corrected)

### Geometry
- Position: (100mm, 0mm, 6mm) in lab frame
- Airpath: 100.18mm
- Omega (solid angle): 1.5914e-05 sr

### Miller Indices (Both C and PyTorch)
- h_frac = -0.0290, k_frac = 0, l_frac = 0.9660
- h0 = 0, k0 = 0, l0 = 1

### Lattice Factors
- F_latt_a = 4.836
- F_latt_b = 5.000
- F_latt_c = 4.775
- F_latt = 115.456

### Intensity
- I_before_scaling = 1.333e8
- Final intensity: C = 2117.56, PyTorch = 2121.36
- Ratio: 1.00179 (0.179% difference)

## Next Steps

1. Generate traces for multiple pixels to identify spatial patterns
2. Compare omega calculations across the detector
3. Investigate coordinate/indexing conventions
4. Check for off-by-one errors in pixel addressing
5. Examine edge/boundary handling

## How to Reproduce

### C Trace
```bash
./golden_suite_generator/nanoBragg -default_F 100 -cell 100 100 100 90 90 90 \
  -lambda 6.2 -N 5 -distance 100 -seed 1 -detpixels 256 -pixel 0.4 \
  -Xbeam 25.6 -Ybeam 25.6 -mosflm -trace_pixel 64 79 \
  -floatfile /tmp/c_trace.bin 2>&1 | tee c_trace.log
```

### PyTorch Trace
```bash
export KMP_DUPLICATE_LIB_OK=TRUE
python -m nanobrag_torch -default_F 100 -cell 100 100 100 90 90 90 \
  -lambda 6.2 -N 5 -distance 100 -seed 1 -detpixels 256 -pixel 0.4 \
  -Xbeam 25.6 -Ybeam 25.6 -mosflm -trace_pixel 64 79 \
  -floatfile /tmp/py_trace.bin 2>&1 | tee py_trace.log
```

## Commits

- **Fix applied**: Enhanced trace output with corrected Miller index calculation
- **File**: `src/nanobrag_torch/simulator.py`
- **Lines modified**: ~785-890 (method `_apply_debug_output`)

## Contact

For questions about this analysis, see:
- Test specification: `tests/test_at_parallel_002_pixel_size.py`
- Configuration map: `docs/development/c_to_pytorch_config_map.md`
- Debugging guide: `docs/debugging/debugging.md`