# Scaling Chain Analysis: C vs PyTorch

**Last Updated:** 2025-10-06 (Phase K3g3 Evidence Collection)
**Commit:** 192429d (post-MOSFLM rescale fix 46ba36b)
**Pixel:** (slow=133, fast=134) — changed from (1039, 685) for on-peak verification

## Phase K3g3 Parity Status: **FAILED**

The parity test after the MOSFLM real-vector rescale fix still shows poor correlation:

| Metric | Value | Status |
|--------|-------|--------|
| Correlation | 0.174 | ❌ < 0.999 |
| Sum ratio (Py/C) | 1.45 | ❌ (expect ~1.0) |
| Max ratio (Py/C) | 2.13 | ❌ (expect ~1.0) |
| Peak distance | 122-272 px | ❌ (expect ≤1 px) |

## Dtype Analysis Results

Float32 vs Float64 comparison (pixel 133,134):
- **F_latt_b error:** 93.98% in BOTH dtypes
- **Conclusion:** Precision is NOT the root cause

Reference: `dtype_sweep/dtype_sensitivity.json`

## Legacy Scaling Chain (Attempt #42, pixel 1039,685)

### Key Findings

**First Divergence:** `I_before_scaling` (after SAMPLE pivot fix)
- C value: 1.480792010454e+15
- PyTorch value: 1.806530429487e+14
- Ratio (Py/C): 0.122 (8.2× undercount)

**Final Intensity Ratio (Py/C):** 1.114

### Post-SAMPLE-Pivot Factor Comparison

| Factor | C Value | PyTorch Value | Ratio (Py/C) | Match? | Notes |
|--------|---------|---------------|--------------|--------|-------|
| I_before_scaling | 1.481e+15 | 1.807e+14 | 0.122 | ❌ | 8.2× error |
| F_latt_b | 38.63 | 46.98 | 1.216 | ❌ | 21.6% excess |
| steps | 1.00e+01 | 1.00e+01 | 1.000 | ✅ | |
| r_e_sqr | 7.941e-30 | 7.941e-30 | 1.000 | ✅ | |
| fluence | 1.00e+24 | 1.00e+24 | 1.000 | ✅ | |
| polar | 0.9126 | 1.000 | 1.096 | ❌ | 9.6% error |
| omega_pixel | 4.159e-07 | 4.159e-07 | 0.9998 | ✅ | |
| I_pixel_final | 446.25 | 497.18 | 1.114 | ❌ | |

### Updated Findings (Attempt #42)

1. **F_latt_b divergence (21.6%):** Despite MOSFLM rescale fix, lattice factor still mismatches
2. **Polarization mismatch:** PyTorch polar=1.0 vs C polar≈0.913 (9.6% error)
3. **Root causes remain:**
   - Fractional Miller indices may still be off (Δk≈6.0 from K3e per-φ traces)
   - Base lattice vectors unverified post-rescale (K3f needed)
   - Polarization defaults need realignment (K3b pending)

## Artifacts

- **Phase K3g3 parity run:** `pytest_post_fix.log`, `nb_compare_post_fix/summary.json`
- **Dtype analysis:** `analyze_output_post_fix_fp32.txt`, `analyze_output_post_fix_fp64.txt`
- **Visual comparison:** `nb_compare_post_fix/diff.png`, `c.png`, `py.png`
- **Legacy traces (Attempt #42):** `trace_c_scaling.log`, `trace_py_after.log`
- **Analysis script:** `analyze_scaling.py`

## Next Actions (per Plan K3f)

1. ⬜ Capture C baseline for base lattice + scattering (K3f1)
2. ⬜ Extend PyTorch trace harness with matching fields (K3f2)
3. ⬜ Diff base traces & isolate first divergence (K3f3)
4. ⬜ Record root cause & fix outline (K3f4)

**Blocker:** The MOSFLM rescale fix (commit 46ba36b) is insufficient. Phase K3f base-lattice traces are required to diagnose the Δh≈6.0 / F_latt_b error before resuming parity work.
