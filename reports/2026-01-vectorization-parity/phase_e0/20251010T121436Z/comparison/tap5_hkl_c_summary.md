# Phase E13: C Tap 5.1 HKL Audit Summary

**Timestamp:** 2025-10-10T12:14:36Z
**Purpose:** Mirror PyTorch Tap 5.1 per-subpixel HKL audit for pixels (0,0) and (2048,2048)
**Git SHA:** 1a2203d553ea339ba23ba0b89f582b0033be2972
**Binary:** ./nanoBragg (instrumented with TRACE_C_TAP5_HKL guard at lines 3337-3345)

## Captured Pixels

### Edge Pixel (0,0) - oversample=2

**HKL Subpixel Data:**
- **Subpixel (0,0):** h=-7.90066, k=39.3564, l=-39.3564 → h0=-8, k0=39, l0=-39, F_cell=100, out_of_bounds=0
- **Subpixel (0,1):** h=-7.89885, k=39.3567, l=-39.3471 → h0=-8, k0=39, l0=-39, F_cell=100, out_of_bounds=0
- **Subpixel (1,0):** h=-7.89885, k=39.3471, l=-39.3567 → h0=-8, k0=39, l0=-39, F_cell=100, out_of_bounds=0
- **Subpixel (1,1):** h=-7.89703, k=39.3475, l=-39.3475 → h0=-8, k0=39, l0=-39, F_cell=100, out_of_bounds=0

**Key Observations:**
- All 4 subpixels round to the same Miller indices: (-8, 39, -39)
- All subpixels report `out_of_bounds=0` (in-bounds)
- All subpixels use `F_cell=default_F=100` (no HKL file loaded)
- Fractional HKL values vary slightly across subpixels due to position variation

### Centre Pixel (2048,2048) - oversample=2

**HKL Subpixel Data:**
- **Subpixel (0,0):** h=-1.125e-06, k=0.0150, l=-0.0150 → h0=0, k0=0, l0=0, F_cell=100, out_of_bounds=0
- **Subpixel (0,1):** h=-6.250e-07, k=0.0150, l=-0.0050 → h0=0, k0=0, l0=0, F_cell=100, out_of_bounds=0
- **Subpixel (1,0):** h=-6.250e-07, k=0.0050, l=-0.0150 → h0=0, k0=0, l0=0, F_cell=100, out_of_bounds=0
- **Subpixel (1,1):** h=-1.250e-07, k=0.0050, l=-0.0050 → h0=0, k0=0, l0=0, F_cell=100, out_of_bounds=0

**Key Observations:**
- All 4 subpixels round to Miller indices: (0, 0, 0)
- All subpixels report `out_of_bounds=0` (in-bounds)
- All subpixels use `F_cell=default_F=100` (no HKL file loaded)
- Fractional HKL values are close to zero (direct beam region)

## Critical Findings

### 1. HKL Indexing Behavior
Both C and PyTorch report `out_of_bounds=0` for all subpixels at both test pixels. This confirms that the HKL indexing logic correctly treats (0,0,0) as **in-bounds** when no HKL file is loaded.

### 2. Default_F Application
When no HKL file is present, both implementations correctly apply `default_F=100` to all Miller indices, regardless of whether they round to (0,0,0) or other values. The C code shows this at line 3328:
```c
F_cell = default_F;  // usually zero
```

### 3. Comparison with PyTorch Tap 5.1
**PyTorch Results** (from Attempts #32/#33):
- Edge pixel (0,0): All subpixels → h0=-8, k0=39, l0=-39, F_cell=100, out_of_bounds=False
- Centre pixel (2048,2048): All subpixels → h0=0, k0=0, l0=0, F_cell=100, out_of_bounds=False

**C Results** (this capture):
- Edge pixel (0,0): All subpixels → h0=-8, k0=39, l0=-39, F_cell=100, out_of_bounds=0
- Centre pixel (2048,2048): All subpixels → h0=0, k0=0, l0=0, F_cell=100, out_of_bounds=0

**Parity Status:** ✅ **PERFECT MATCH** - HKL indexing, bounds checking, and F_cell application are identical between C and PyTorch.

## Hypothesis Validation

### H1: HKL Indexing Bug - **REFUTED**
The hypothesis that PyTorch incorrectly treats (0,0,0) as out-of-bounds is **refuted**. Both implementations:
- Correctly round fractional Miller indices to (0,0,0) for the centre pixel
- Report `out_of_bounds=0` (False)
- Apply `default_F=100` uniformly when no HKL file is loaded

### Implication for Phase E
The 4× intensity discrepancy identified in Tap 5 (Attempt #30: C edge pixel `I_before_scaling=1.415e5` vs PyTorch `I_before_scaling=3.54e4`) is **NOT** caused by HKL indexing or bounds checking. The divergence must originate from:
- **H2:** Subpixel accumulation order/method
- **H3:** Background scaling (unlikely given water_size=0)
- **H4:** Undiscovered normalization or loop-order difference

## Next Steps

Per vectorization-parity-regression.md Task E14:
1. Execute Tap 5.2 to capture HKL grid bounds (`[h_min,h_max]`, `[k_min,k_max]`, `[l_min,l_max]`) and confirm (0,0,0) is within the loaded range
2. If Tap 5.2 confirms parity, pivot to **H2 investigation**: instrument the C oversample accumulation loop to log per-subpixel `F_cell²·F_latt²` contributions and compare against PyTorch's batched accumulation

## Artifacts

- **C traces:** `reports/2026-01-vectorization-parity/phase_e0/20251010T121436Z/c_taps/{pixel_0_0_hkl.log, pixel_2048_2048_hkl.log}`
- **Commands:** `reports/2026-01-vectorization-parity/phase_e0/20251010T121436Z/c_taps/commands.txt`
- **Environment:** `reports/2026-01-vectorization-parity/phase_e0/20251010T121436Z/env/{git_sha.txt, trace_env.json}`
- **Pytest collection:** `reports/2026-01-vectorization-parity/phase_e0/20251010T121436Z/comparison/pytest_collect.log` (692 tests)

## References

- **Spec:** `specs/spec-a-core.md` §§232-240 (HKL lookup semantics), §§471-476 (default_F fallback)
- **Plan:** `plans/active/vectorization-parity-regression.md` Task E13
- **Ledger:** `docs/fix_plan.md` [VECTOR-PARITY-001] Attempts #32/#33 (PyTorch Tap 5.1), Attempt #34 (this C mirror)
