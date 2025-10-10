# PyTorch Tap 5.1 — Per-Subpixel HKL Audit Summary

**Date:** 2025-10-10
**Ralph Attempt:** #33
**Phase:** E12 (PyTorch Tap 5.1 HKL Audit)
**Timestamp:** 20251010T120355Z

## Executive Summary

**Key Finding:** PyTorch correctly treats HKL index `(0,0,0)` as **in-bounds** for all 4 subpixels at the centre pixel (2048,2048) with oversample=2. This refutes Hypothesis H1 from `tap5_hypotheses.md` (that PyTorch incorrectly treats (0,0,0) as out-of-bounds).

**Implication:** The 4× intensity discrepancy between C and PyTorch at centre pixel (Attempt #30) is NOT caused by HKL indexing or bounds checking. The hypothesis must pivot to H2 (oversample accumulation) or H3 (background inclusion).

## Pixel Data Analysis

### Centre Pixel (2048, 2048)

**Configuration:**
- Oversample: 2 (2×2 subpixel grid)
- Total subpixels: 4
- All subpixels round to HKL `(0,0,0)`
- All report `out_of_bounds=false`
- All return `F_cell=100.0` (default_F)

**Subpixel Breakdown:**

| Subpixel | HKL Fractional | HKL Rounded | F_cell | Out of Bounds |
|----------|----------------|-------------|--------|---------------|
| [0,0] | (-1.999999965641e-06, 0.01999999980000, -0.01999999980000) | (0,0,0) | 100.0 | false |
| [0,1] | (-9.999999939213e-07, 0.01999999990000, -4.449294643091e-15) | (0,0,0) | 100.0 | false |
| [1,0] | (-9.999999939238e-07, 4.448069996298e-15, -0.01999999990000) | (0,0,0) | 100.0 | false |
| [1,1] | (-4.379057701015e-47, 4.449294665337e-15, -4.449294665337e-15) | (0,0,0) | 100.0 | false |

**Observation:**
- All 4 subpixels have fractional HKL components very close to zero (h ≈ 0, k ≈ 0.02, l ≈ -0.02 or near-zero)
- All round to integer HKL `(0,0,0)`
- PyTorch reports `out_of_bounds=false` for all 4 subpixels → **(0,0,0) is treated as in-bounds**
- All subpixels return `F_cell=100.0` (default_F)

**Critical Result:** PyTorch does NOT treat (0,0,0) as out-of-bounds.

### Edge Pixel (0, 0)

**Configuration:**
- Oversample: 2 (2×2 subpixel grid)
- Total subpixels: 4
- All subpixels round to HKL `(-8, 39, -39)`
- All report `out_of_bounds=false`
- All return `F_cell=100.0` (default_F)

**Subpixel Breakdown:**

| Subpixel | HKL Fractional | HKL Rounded | F_cell | Out of Bounds |
|----------|----------------|-------------|--------|---------------|
| [0,0] | (-7.902478764626, 39.360782101128, -39.360782101128) | (-8,39,-39) | 100.0 | false |
| [0,1] | (-7.898848372213, 39.361525968534, -39.342315853371) | (-8,39,-39) | 100.0 | false |
| [1,0] | (-7.898848372213, 39.342315853371, -39.361525968534) | (-8,39,-39) | 100.0 | false |
| [1,1] | (-7.895217773963, 39.343059399892, -39.343059399892) | (-8,39,-39) | 100.0 | false |

**Observation:**
- All 4 subpixels have fractional HKL ≈ (-7.9, 39.35, -39.35)
- All round to integer HKL `(-8, 39, -39)`
- All report `out_of_bounds=false`
- All return `F_cell=100.0` (default_F)

**Consistency:** Edge pixel behaviour matches centre pixel — all lookups return default_F with no out-of-bounds flags.

## Hypothesis Evaluation

### H1 — HKL Indexing Bug (Refuted)

**Hypothesis:** PyTorch incorrectly treats Miller index `(0,0,0)` as out-of-bounds, falling back to default_F=100 instead of retrieving the stored HKL value of 0.0.

**Evidence Against H1:**
1. All 4 subpixels at centre pixel (2048,2048) round to `(0,0,0)`
2. All 4 report `out_of_bounds=false` (not true!)
3. PyTorch's HKL lookup code treats (0,0,0) as a valid, in-bounds index

**Conclusion:** H1 is refuted. PyTorch's HKL indexing is correct for (0,0,0).

**But:** All subpixels still return `F_cell=100.0` (default_F), not the stored HKL grid value. This suggests:
- **Either:** The test case has no HKL file loaded (only default_F), OR
- **Or:** There is a *different* issue with HKL grid lookup that is unrelated to bounds checking

### Next Steps

**Action Required:** Compare against C Tap 5.1 (E13) to determine:
1. Does C also treat (0,0,0) as in-bounds?
2. What F_cell values does C retrieve for the same 4 subpixels?
3. Is there a difference in the stored HKL grid between C and PyTorch?

**Hypothesis Pivot:** If C retrieves `F_cell=0.0` for (0,0,0) while PyTorch retrieves `F_cell=100.0`, the issue is NOT bounds checking but rather:
- **H2a:** HKL grid not loaded in PyTorch (missing HKL file)
- **H2b:** HKL grid loaded but lookup returns default_F incorrectly
- **H3:** Oversample accumulation differs between C and PyTorch

## Reference Contract

From `specs/spec-a-core.md:232-240` (Nearest-Neighbour Fallback):

> If interpolation is off:
>   - Nearest-neighbor lookup of F_cell at (h0, k0, l0) if in-range; else F_cell = default_F.

**Interpretation:** The spec requires:
1. Round fractional HKL to nearest integer `(h0, k0, l0)`
2. Check if `(h0, k0, l0)` is within HKL grid bounds `[h_min, h_max] × [k_min, k_max] × [l_min, l_max]`
3. If in-bounds: retrieve F_cell from HKL grid
4. If out-of-bounds: use default_F

**PyTorch Behaviour:** Steps 1-2 are correct. Step 3 requires validation against C Tap 5.1.

## Artifacts

- **Centre pixel JSON:** `reports/2026-01-vectorization-parity/phase_e0/20251010T120355Z/py_taps/pixel_2048_2048_hkl_subpixel.json`
- **Edge pixel JSON:** `reports/2026-01-vectorization-parity/phase_e0/20251010T120355Z/py_taps/pixel_0_0_hkl_subpixel.json`
- **Commands:** `reports/2026-01-vectorization-parity/phase_e0/20251010T120355Z/commands.txt`

## Ledger Update

**Task:** E12 — PyTorch Tap 5.1 HKL Audit
**Status:** [D] (Done)
**Outcome:** H1 refuted; (0,0,0) treated as in-bounds by PyTorch
**Next:** E13 — C Tap 5.1 HKL Audit (mirror this tap on C side)
