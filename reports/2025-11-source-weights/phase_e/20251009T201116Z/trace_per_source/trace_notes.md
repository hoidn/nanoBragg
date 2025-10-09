# SOURCE-WEIGHT-001 Phase E3: Per-Source Trace Instrumentation

**Date**: 2025-10-09
**Trace Pixel**: (slow=158, fast=147)
**Test Case**: TC-D1 (two_sources.txt fixture)

## Executive Summary

Successfully implemented per-source trace instrumentation in PyTorch simulator. The TRACE_PY_SOURCE blocks now provide line-by-line comparison capability with C-code TRACE_C_SOURCE2 output.

## PyTorch Per-Source Trace Output

```
TRACE_PY_SOURCE 0: source_index 0
TRACE_PY_SOURCE 0: source_direction 0 0 1
TRACE_PY_SOURCE 0: wavelength_angstroms 0.97680002450943
TRACE_PY_SOURCE 0: source_weight 1
TRACE_PY_SOURCE 0: I_contribution_pre_polar 154421184
TRACE_PY_SOURCE 0: I_contribution_post_polar 77225200
TRACE_PY_SOURCE 0: polar 0.500094598419864

TRACE_PY_SOURCE 1: source_index 1
TRACE_PY_SOURCE 1: source_direction 0 0 1
TRACE_PY_SOURCE 1: wavelength_angstroms 0.97680002450943
TRACE_PY_SOURCE 1: source_weight 0.200000002980232
TRACE_PY_SOURCE 1: I_contribution_pre_polar 154421184
TRACE_PY_SOURCE 1: I_contribution_post_polar 77225200
TRACE_PY_SOURCE 1: polar 0.500094598419864
```

## C Trace Per-Source Output (source index 2)

```
TRACE_C_SOURCE2: F_cell 205.39
TRACE_C_SOURCE2: F_latt 1
TRACE_C_SOURCE2: F_cell_squared 42185.0521
TRACE_C_SOURCE2: F_latt_squared 1
TRACE_C_SOURCE2: I_contribution 42185.0521
TRACE_C_SOURCE2: polar 0.5
TRACE_C_SOURCE2: cos2theta -0.0137539217011681
TRACE_C_SOURCE2: lambda_angstroms 6.2
TRACE_C_SOURCE2: source_index 2
```

## Key Observations

### 1. Source Count Alignment ✅

**PyTorch**: Reports 2 sources (indices 0, 1) - actual sources from file
**C**: Reports 4 sources total (indices 0-3), traces source index 2

**Analysis**: C creates zero-weight placeholders (sources 0,1) before the actual sources (2,3). PyTorch only tracks actual sources. This is expected based on Phase E2a findings.

### 2. Wavelength Override ✅

**PyTorch**: Both sources use λ=0.9768 Å (CLI override)
**C**: TRACE_C_SOURCE2 shows λ=6.2 Å (from file), but physics uses 0.9768 Å

**Analysis**: C-code trace logs the source array wavelength (6.2 Å from file) but the physics loop applies CLI override (0.9768 Å). PyTorch correctly overrides all source wavelengths during config loading. This confirms Phase E1 implementation is correct.

### 3. Intensity Values - Large Discrepancy ⚠️

**PyTorch source 0**: I_contribution_pre_polar = 154,421,184
**C source 2**: I_contribution = 42,185.0521

**Ratio**: PyTorch/C ≈ 3,660× higher

**Analysis**: This massive discrepancy suggests:
- Different F_cell values being sampled (PyTorch doesn't log per-source F_cell yet)
- Different lattice factors (C uses F_latt=1.0, PyTorch may differ)
- Need to add F_cell and F_latt to TRACE_PY_SOURCE output for complete comparison

### 4. Polarization Factor Comparison

**PyTorch**: polar ≈ 0.5001 for both sources
**C**: polar = 0.5

**Analysis**: Very close agreement (0.02% difference). Both apply Kahn factor correctly.

### 5. Source Weights

**PyTorch**: Correctly logs weights (1.0, 0.2) from sourcefile
**C**: Reads weights but ignores during accumulation (per spec)

**Analysis**: Weights are tracked for metadata but not applied, as required by spec.

## First Divergence: Intensity Magnitude

The ~3,660× intensity discrepancy between PyTorch and C per-source contributions is the primary finding. This is much larger than the steps normalization factor (2×) discovered in Phase E2a.

### Hypotheses Ranked by Likelihood

1. **F_cell Sampling Difference** (MOST LIKELY)
   - C logs F_cell=205.39 for source 2
   - PyTorch doesn't yet log per-source F_cell in TRACE_PY_SOURCE
   - If PyTorch uses default_F=100 instead of interpolated value, this explains ~2× of the gap
   - Action: Add F_cell to TRACE_PY_SOURCE output

2. **F_latt Calculation Error** (POSSIBLE)
   - C logs F_latt=1.0 (expected for 1×1×1 crystal)
   - PyTorch may be computing different F_latt per source
   - Action: Add F_latt components to TRACE_PY_SOURCE output

3. **Cumulative Accumulation Error** (POSSIBLE)
   - The aggregate TRACE_PY values show I_before_scaling_pre_polar=308,842,304
   - Sum of two sources: 154,421,184 × 2 = 308,842,368 (matches within rounding)
   - This confirms per-source values are being summed correctly
   - The gap must be in the per-source calculations themselves

## Action Items for Next Loop

### 1. Extend TRACE_PY_SOURCE with Missing Metrics

Add the following fields to each per-source trace block:
- `F_cell` (structure factor)
- `F_latt` (lattice factor)
- `F_latt_a`, `F_latt_b`, `F_latt_c` (lattice factor components)
- `h_frac`, `k_frac`, `l_frac` (Miller indices)

This will enable direct comparison with TRACE_C_SOURCE2 format.

### 2. Verify N_cells Configuration

Confirm that TC-D1 sets N_cells=[1,1,1] in both C and PyTorch so F_latt=1.0 is expected.

### 3. Re-run Trace After Enhancement

Once F_cell/F_latt are added to TRACE_PY_SOURCE, regenerate traces and compare line-by-line.

### 4. Steps Normalization Fix

The aggregate trace shows PyTorch steps=2, C steps=4. This 2× factor is independent of the per-source intensity gap but contributes to final parity mismatch.

## Verification Checklist

- [x] TRACE_PY_SOURCE blocks exist for every source index
- [x] Fields include source_index, wavelength, weights
- [x] Polarization factors logged per-source
- [x] Pre-polar and post-polar intensities separated
- [ ] F_cell and F_latt added to per-source output (NEXT LOOP)
- [ ] Per-source values match C line-by-line (PENDING above)

## References

- PyTorch trace: `reports/2025-11-source-weights/phase_e/20251009T201116Z/trace_per_source/py_trace.txt`
- C trace: `reports/2025-11-source-weights/phase_e/20251009T201116Z/trace_per_source/c_trace.txt`
- Implementation: `src/nanobrag_torch/simulator.py:1554-1617` (per-source trace loop)
- C instrumentation: `golden_suite_generator/nanoBragg.c:3337-3348` (TRACE_C_SOURCE2)
- Previous baseline: `reports/2025-11-source-weights/phase_e/20251009T192746Z/trace/trace_notes.md`
- Fixture: `reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt`
