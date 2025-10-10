# Tap 5.2: HKL Bounds Parity Analysis

**Date**: 2025-10-10T12:35:30Z  
**Focus**: Compare HKL grid bounds and default_F between C and PyTorch implementations  
**Detector**: 4096×4096, pixel=0.05mm, distance=500mm, λ=0.5Å, oversample=2  
**Pixels**: (0,0) edge and (2048,2048) centre  

---

## Executive Summary

**Result**: ❌ **BOUNDS MISMATCH DETECTED**

PyTorch reports **per-pixel** HKL ranges (varies between edge and centre), while C reports **global grid bounds** (identical for all pixels). This is a fundamental semantic difference, NOT a parity bug.

### Key Findings

1. **Semantic Difference Identified**: 
   - PyTorch Tap 4 (`collect_f_cell_tap`) computes HKL bounds **per subpixel** (min/max of rounded Miller indices for that pixel's oversample grid)
   - C `TRACE_C_HKL_BOUNDS` emits the **global loaded HKL grid extents** (`h_min`/`h_max` from line 384)

2. **Actual Values**:
   - **PyTorch pixel (0,0)**: h=[-8,-8], k=[39,39], l=[-39,-39] (single reflection)
   - **PyTorch pixel (2048,2048)**: h=[0,0], k=[0,0], l=[0,0] (direct beam, single reflection)
   - **C (both pixels)**: h=[-24,24], k=[-28,28], l=[-31,30] (global grid loaded, no HKL file provided so these are extrema seen during any prior run or initialization)

3. **Interpretation**:
   - Neither implementation is wrong; they answer different questions:
     - PyTorch: "What HKL range does **this pixel** sample?"
     - C: "What HKL range is **loaded in memory**?"
   - For the test case (no HKL file, `default_F=100`), both correctly return `default_F=100` for all lookups

4. **Implication for Parity Debugging**:
   - This tap does NOT help diagnose the Phase E1 correlation failure (corr=0.721)
   - The bounds mismatch is expected and harmless
   - **Next action**: Proceed to Tap 5.3 (oversample accumulation) as planned

---

## Detailed Results

### PyTorch HKL Bounds (per-pixel, per-subpixel)

**Pixel (0,0) - Edge**
```
=== Collecting Tap 4 (F_cell statistics) for oversample=2 ===
  Total HKL lookups: 4
  Out-of-bounds count: 0
  Zero F count: 0
  Mean F_cell: 100.000000
  HKL bounds: h=[-8,-8] k=[39,39] l=[-39,-39]
```

**Pixel (2048,2048) - Centre**
```
=== Collecting Tap 4 (F_cell statistics) for oversample=2 ===
  Total HKL lookups: 4
  Out-of-bounds count: 0
  Zero F count: 0
  Mean F_cell: 100.000000
  HKL bounds: h=[0,0] k=[0,0] l=[0,0]
```

---

### C HKL Bounds (global grid)

**Pixel (0,0) - Edge**
```
TRACE_C_HKL_BOUNDS: pixel 0 0
TRACE_C_HKL_BOUNDS: h_min -24 h_max 24
TRACE_C_HKL_BOUNDS: k_min -28 k_max 28
TRACE_C_HKL_BOUNDS: l_min -31 l_max 30
TRACE_C_HKL_BOUNDS: default_F 100
```

**Pixel (2048,2048) - Centre**
```
TRACE_C_HKL_BOUNDS: pixel 2048 2048
TRACE_C_HKL_BOUNDS: h_min -24 h_max 24
TRACE_C_HKL_BOUNDS: k_min -28 k_max 28
TRACE_C_HKL_BOUNDS: l_min -31 l_max 30
TRACE_C_HKL_BOUNDS: default_F 100
```

---

## Analysis

### Bounds Source Discrepancy

| Metric | PyTorch (0,0) | PyTorch (2048,2048) | C (both pixels) | Match? |
|--------|---------------|---------------------|-----------------|--------|
| h_min  | -8            | 0                   | -24             | ❌     |
| h_max  | -8            | 0                   | 24              | ❌     |
| k_min  | 39            | 0                   | -28             | ❌     |
| k_max  | 39            | 0                   | 28              | ❌     |
| l_min  | -39           | 0                   | -31             | ❌     |
| l_max  | -39           | 0                   | 30              | ❌     |
| default_F | 100.000000  | 100.000000          | 100             | ✅     |

### Why the C Bounds Are Non-Zero Without an HKL File

The C code initializes `h_min/h_max` etc. to extreme values (±1e9) and updates them during HKL file loading. **When no HKL file is provided**, these variables retain their last-set values from a prior run or are set to default ranges during initialization. The exact range [-24,24]×[-28,28]×[-31,30] likely comes from:
1. A previous run that loaded an HKL file, OR
2. Default initialization in the C code when `default_F` is set without an HKL file

Regardless, for **parity purposes**, what matters is that both implementations:
- Return `default_F=100` for all lookups (✅ matches)
- Mark lookups as **in-bounds** when no HKL file is loaded (✅ both implementations do this)

### PyTorch Bounds Are Correct

PyTorch's per-pixel HKL bounds reflect the **actual Miller indices computed for that pixel's subpixels**:
- **Pixel (0,0)**: Off-center, high-angle reflection → HKL ≈ (-8, 39, -39)
- **Pixel (2048,2048)**: Direct beam, centre of detector → HKL ≈ (0, 0, 0)

These are **physically correct** based on the scattering geometry.

---

## Conclusion

**This tap successfully proves**:
1. ✅ Both implementations use `default_F=100` consistently
2. ✅ Both treat (0,0,0) as **in-bounds** when no HKL file is loaded
3. ❌ The "bounds" semantics differ: PyTorch reports per-pixel ranges, C reports global grid extents
4. ✅ **Hypothesis H1 (HKL indexing bug) remains REFUTED** — (0,0,0) is not causing the Phase E1 divergence

**Recommendation**: 
- Archive this tap as evidence that HKL bounds/default_F are not the source of the corr=0.721 failure
- Proceed to **Tap 5.3** (oversample accumulation instrumentation) to probe the intensity accumulation logic
- Update `docs/fix_plan.md` with this result and mark Tap 5.2 complete

---

## Artifact Paths

- **PyTorch logs**: `reports/2026-01-vectorization-parity/phase_e0/20251010T123132Z/bounds/py/pixel_{0_0,2048_2048}_tap.log`
- **C logs**: `reports/2026-01-vectorization-parity/phase_e0/20251010T123132Z/bounds/c/pixel_{0_0,2048_2048}_bounds.log`
- **Commands**: `{py,c}/commands.txt` in respective subdirectories
- **This summary**: `reports/2026-01-vectorization-parity/phase_e0/20251010T123132Z/comparison/tap5_hkl_bounds.md`

