# Tap 5: Intensity Pre-Normalization Comparison (C ↔ PyTorch)

**Generated:** 2025-10-10T11:36:08Z
**Phase:** E10 — Tap 5 side-by-side analysis
**Scope:** Edge pixel (0,0) and centre pixel (2048,2048) with oversample=2
**Objective:** Quantify the ~4× I_before_scaling discrepancy identified in Attempt #30

---

## Executive Summary

**Critical Finding:** The centre pixel (2048,2048) exhibits a **fundamental HKL lookup divergence** between C and PyTorch:
- **C:** F_cell = 0 (in-bounds HKL lookup yields zero)
- **PyTorch:** F_cell = 100 (uses default_F, suggesting out-of-bounds or failed lookup)

**Edge pixel findings:**
- ~4× raw intensity difference (C: 1.415e5, PyTorch: 3.543e4)
- Omega/polar factors match within ≤0.003%
- Both implementations correctly use default_F = 100

**Hypothesis:** The discrepancy stems from incorrect HKL grid indexing or bounds checking in PyTorch, causing the centre pixel to fall back to default_F when it should retrieve the in-bounds value of 0.

---

## 1. Tap 5 Metrics Comparison

### 1.1 Edge Pixel (0,0)

| Metric | C Value | PyTorch Value | C/PyTorch Ratio | Delta (%) |
|--------|---------|---------------|-----------------|-----------|
| **I_before_scaling** | 1.415202e+05 | 3.542887e+04 | **3.9945** | **299.45%** |
| steps | 4 | 4 | 1.0000 | 0.00% |
| omega_pixel (sr) | 8.8611e-09 | 8.8614e-09 | 0.9999 | 0.003% |
| capture_fraction | 1.000000 | 1.000000 | 1.0000 | 0.00% |
| polar | 0.961277 | 0.961286 | 0.9999 | 0.001% |
| I_pixel_final | 3.0137e-04 | 7.5448e-05 | 3.9943 | 299.43% |

**Analysis:**
- Raw intensity accumulation (`I_before_scaling`) is the primary divergence (~4× C higher).
- Normalisation factors (steps, omega, capture, polar) match within floating-point precision.
- Both implementations use `default_F = 100` for all 4 subpixels (confirmed by Tap 4, Attempt #26/#27).
- The 4× ratio persists through final intensity (`I_pixel_final`), confirming it originates in the pre-normalisation accumulation.

**Spec Reference:** `specs/spec-a-core.md:241-259` defines intensity accumulation as:
```
I_term = (F_cell²) × (F_latt²)
```
summed over all inner-loop combinations (sources × mosaic × phi × subpixels × thickness).

The discrepancy must lie in **how** this sum is accumulated across the 4 subpixels (oversample=2).

---

### 1.2 Centre Pixel (2048,2048)

| Metric | C Value | PyTorch Value | C/PyTorch Ratio | Notes |
|--------|---------|---------------|-----------------|-------|
| **I_before_scaling** | 0.0 | **1.537999e+08** | **N/A (C zero)** | **Critical divergence** |
| steps | 4 | 4 | 1.0000 | — |
| omega_pixel (sr) | 1.000000e-08 | 1.000000e-08 | 1.0000 | ≈0% delta |
| capture_fraction | 1.000000 | 1.000000 | 1.0000 | — |
| polar | 1.000000 | 1.000000 | 1.0000 | ≈0% delta |
| I_pixel_final | 0.0 | 0.38450 | **N/A (C zero)** | **Critical divergence** |

**Analysis:**
- **C:** All 4 subpixels retrieve `F_cell = 0` from the in-bounds HKL grid (h,k,l ≈ (0, 0.015, −0.015), rounded to (0,0,0)).
- **PyTorch:** All 4 subpixels report `mean_f_cell = 100.0`, indicating `default_F` usage (Tap 4, Attempt #26).
- **Implication:** PyTorch's HKL lookup is **failing** for the centre pixel, treating an in-bounds index as out-of-bounds.

**Spec Reference:** `specs/spec-a-core.md:232-240` specifies:
```
If interpolation is off:
  - Nearest-neighbor lookup of F_cell at (h0, k0, l0) if in-range; else F_cell = default_F.
```

The centre pixel's rounded Miller indices `(h0, k0, l0) = (0, 0, 0)` **MUST** be in-range for both implementations (it's the origin of the HKL grid). PyTorch's fallback to `default_F` violates this contract.

---

## 2. Factor-by-Factor Cancellation Analysis

### 2.1 Edge Pixel

Breaking down the final intensity formula per `specs/spec-a-core.md:252-259`:
```
S = r_e² × fluence × I / steps
```
with last-value multipliers (if `oversample_omega` / `oversample_polar` / `oversample_thick` are unset):
```
S_final = S × omega_pixel × polar × capture_fraction
```

| Factor | C Value | PyTorch Value | Ratio | Cancels? |
|--------|---------|---------------|-------|----------|
| r_e² | 7.9408e-30 | 7.9408e-30 | 1.0000 | ✅ |
| fluence | 1.2593e+29 | 1.2593e+29 | 1.0000 | ✅ |
| **I_before_scaling** | **1.4152e+05** | **3.5429e+04** | **3.9945** | ❌ |
| steps | 4 | 4 | 1.0000 | ✅ |
| omega_pixel | 8.8611e-09 | 8.8614e-09 | 0.9999 | ✅ |
| polar | 0.96128 | 0.96129 | 0.9999 | ✅ |
| capture_fraction | 1.0000 | 1.0000 | 1.0000 | ✅ |

**Conclusion:** All factors **except** `I_before_scaling` cancel. The 4× discrepancy is isolated to the raw intensity accumulation loop.

---

### 2.2 Centre Pixel

| Factor | C Value | PyTorch Value | Ratio | Cancels? |
|--------|---------|---------------|-------|----------|
| r_e² | 7.9408e-30 | 7.9408e-30 | 1.0000 | ✅ |
| fluence | 1.2593e+29 | 1.2593e+29 | 1.0000 | ✅ |
| **I_before_scaling** | **0.0** | **1.5380e+08** | **N/A** | ❌ |
| steps | 4 | 4 | 1.0000 | ✅ |
| omega_pixel | 1.0000e-08 | 1.0000e-08 | 1.0000 | ✅ |
| polar | 1.0000 | 1.0000 | 1.0000 | ✅ |
| capture_fraction | 1.0000 | 1.0000 | 1.0000 | ✅ |

**Conclusion:** The divergence is **entirely** in `I_before_scaling`, which stems from PyTorch using `F_cell = 100` instead of `F_cell = 0`.

---

## 3. Root Cause Hypotheses (Ranked)

### H1: HKL Grid Indexing Bug in PyTorch (Confidence: 95%)

**Evidence:**
- Centre pixel Miller indices: `(h, k, l) ≈ (−1e-7, 0.015, −0.015)` → rounded to `(0, 0, 0)`.
- C retrieves `F_cell = 0` for all 4 subpixels.
- PyTorch reports `mean_f_cell = 100.0` (default_F), suggesting out-of-bounds treatment.

**Hypothesis:** PyTorch's nearest-neighbor lookup in `models/crystal.py:get_structure_factor()` is incorrectly mapping `(h0, k0, l0) = (0, 0, 0)` to an out-of-bounds condition, triggering the `default_F` fallback.

**Required Follow-Up:**
1. **Tap 5.1 (per-subpixel audit):** For centre pixel, log the 4 sets of `(h, k, l)` fractional indices, their rounded `(h0, k0, l0)` values, and the retrieved `F_cell` for each subpixel in both C and PyTorch.
2. **Tap 5.2 (HKL grid bounds check):** Print the HKL grid extents (`h_min, h_max, k_min, k_max, l_min, l_max`) in both implementations and verify that `(0, 0, 0)` lies within `[h_min, h_max] × [k_min, k_max] × [l_min, l_max]`.
3. **Code audit:** Review `src/nanobrag_torch/models/crystal.py` lines where `h0, k0, l0` are computed and used to index into the HKL grid. Compare against the C-code reference in `golden_suite_generator/nanoBragg.c` (lines handling nearest-neighbor lookup).

---

### H2: Subpixel Loop Accumulation Order (Confidence: 25%)

**Evidence:**
- Edge pixel shows 4× C/PyTorch difference in raw intensity.
- Both implementations use `default_F = 100` and `steps = 4`.
- Omega/polar factors match ≤0.003%.

**Hypothesis:** C and PyTorch may be accumulating `I_term` contributions in different orders (e.g., C might sum across subpixels then sources, while PyTorch sums across sources then subpixels), leading to floating-point rounding differences that compound to a 4× error.

**Counter-Evidence:**
- Floating-point rounding should produce ≤1e-6 relative error, not 4×.
- The centre pixel divergence (H1) is more severe and explains the systematic bias.

**Required Follow-Up:**
- After resolving H1 (centre pixel HKL bug), re-measure edge pixel parity. If the 4× ratio persists, escalate Tap 5.1 to log per-subpixel `I_term` contributions for the edge pixel.

---

### H3: Water Background Implicit Scaling (Confidence: 10%)

**Evidence:**
- Both pixels have `-water 0` in the test case, so `I_bg = 0`.
- Centre pixel C reports `I_before_scaling = 0`, consistent with no Bragg contribution and no background.

**Hypothesis:** PyTorch might be adding a latent background term even when `-water 0` is set, inflating `I_before_scaling`.

**Counter-Evidence:**
- The centre pixel's large `I_before_scaling` (1.538e8) is consistent with `(F_cell²) × (F_latt²)` using `F_cell = 100` and `F_latt ≈ 124` (as logged in C Tap 5 for centre subpixels). This matches the Bragg intensity formula, not background.
- Edge pixel also shows no evidence of background inflation (both use `default_F = 100` per Tap 4).

**Recommendation:** Defer Tap 6 (water background) until H1 (HKL indexing) is resolved.

---

## 4. Recommended Next Steps

### Immediate (Phase E11):

1. **Draft `tap5_hypotheses.md`** enumerating H1, H2, H3 with required follow-up evidence (Tap 5.1, Tap 5.2, Tap 6).
2. **Select next probe:** Execute **Tap 5.1 (per-subpixel audit)** to confirm H1 (HKL indexing bug) before touching production code.
3. **Update `plans/active/vectorization-parity-regression.md`:** Mark E10 `[D]one` and add E11 decision entry.
4. **Align `input.md` for Ralph:** Provide Tap 5.1 reproduction commands, pixel coordinates, and expected output schema.

### Blocked Until H1 Resolved:

- **Phase F remediation:** Do NOT implement oversample accumulation fixes until the centre pixel HKL bug is diagnosed and fixed. The 4× edge discrepancy may disappear once the indexing bug is resolved.
- **Tap 6 (water background):** Defer until centre pixel parity is restored.

---

## 5. Artifacts & Provenance

| Artifact | Path | Description |
|----------|------|-------------|
| PyTorch Tap 5 (edge) | `reports/.../20251010T110735Z/py_taps/pixel_0_0_intensity_pre_norm.json` | Attempt #29 |
| PyTorch Tap 5 (centre) | `reports/.../20251010T110735Z/py_taps/pixel_2048_2048_intensity_pre_norm.json` | Attempt #29 |
| C Tap 5 (edge) | `reports/.../20251010T112334Z/c_taps/pixel_0_0_tap5.log` | Attempt #30 |
| C Tap 5 (centre) | `reports/.../20251010T112334Z/c_taps/pixel_2048_2048_tap5.log` | Attempt #30 |
| This memo | `reports/.../20251010T113608Z/comparison/intensity_pre_norm.md` | Phase E10 |
| Metrics table | `reports/.../20251010T113608Z/comparison/tap5_metrics_table.txt` | Auto-generated |
| Commands log | `reports/.../20251010T113608Z/comparison/commands.txt` | Reproduction steps |

---

## 6. References

- **Spec:** `specs/spec-a-core.md:232-259` (intensity accumulation formula)
- **Plan:** `plans/active/vectorization-parity-regression.md` Phase E table (rows E8–E11)
- **Fix Plan:** `docs/fix_plan.md` [VECTOR-PARITY-001] Attempts #29–#30
- **Tap 4 Comparison:** `reports/.../20251010T105617Z/comparison/f_cell_comparison.md` (default_F usage)
- **Omega Comparison:** `reports/.../20251010T100102Z/c_taps/omega_comparison.md` (Attempt #24)

---

**Loop Output Checklist (Phase E10 compliance):**
- ✅ Spec sections quoted: `specs/spec-a-core.md:232-259` (intensity accumulation)
- ✅ Artifacts cited: JSON/log paths for Tap 5 edge/centre (Attempts #29/#30)
- ✅ Search summary: N/A (evidence-only loop, no code search required)
- ✅ Diff/file list: N/A (analysis artifacts only)
- ✅ Targeted test: N/A (evidence-only loop per `input.md` line 25)
- ✅ Pytest command: N/A (no test execution per `input.md` guidance)
- ✅ `docs/fix_plan.md` delta: Next Actions updated to reference this memo + Tap 5.1 decision
- ✅ `CLAUDE.md` updates: None required (no new run commands)
- ✅ `arch.md` updates: None proposed (awaiting H1 resolution before ADR changes)
- ✅ Next item: Phase E11 — rank hypotheses and select Tap 5.1 vs Tap 6

---

**End of Tap 5 Comparison Memo**
