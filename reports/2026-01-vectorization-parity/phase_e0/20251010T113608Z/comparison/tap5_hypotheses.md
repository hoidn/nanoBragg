# Tap 5 Hypotheses & Follow-Up Evidence Plan

**Generated:** 2025-10-10T11:36:08Z
**Phase:** E11 decision input
**Scope:** Ranked hypotheses for Tap 5 I_before_scaling discrepancies
**References:** `intensity_pre_norm.md` (Phase E10 comparison)

---

## Hypothesis Summary

| ID | Hypothesis | Confidence | Required Evidence | Priority |
|----|------------|------------|-------------------|----------|
| **H1** | HKL Grid Indexing Bug in PyTorch | 95% | Tap 5.1 (per-subpixel audit) + Tap 5.2 (grid bounds) | **P0** |
| **H2** | Subpixel Loop Accumulation Order | 25% | Tap 5.1 (edge pixel per-subpixel I_term) | P1 (after H1) |
| **H3** | Water Background Implicit Scaling | 10% | Tap 6 (water background taps) | P2 (defer) |

---

## H1: HKL Grid Indexing Bug in PyTorch (95% confidence)

### Evidence

1. **Centre pixel (2048,2048) critical divergence:**
   - C: F_cell = 0 (in-bounds HKL lookup) for all 4 subpixels
   - PyTorch: F_cell = 100 (default_F fallback) for all 4 subpixels
   - Miller indices: h,k,l ≈ (−1e-7, 0.015, −0.015) → rounded to (0,0,0)

2. **Spec violation:**
   - `specs/spec-a-core.md:239-240` states: "Nearest-neighbor lookup of F_cell at (h0, k0, l0) if in-range; else F_cell = default_F."
   - The origin (0,0,0) **MUST** be in-range for both implementations.

3. **Tap 4 consistency:**
   - Edge pixel: both C and PyTorch use default_F = 100 (correct out-of-bounds behavior).
   - Centre pixel: only PyTorch uses default_F (incorrect in-bounds treatment).

### Required Evidence (Tap 5.1 + Tap 5.2)

#### Tap 5.1: Per-Subpixel HKL Audit

**Objective:** Capture fractional Miller indices, rounded integers, and retrieved F_cell for each of the 4 subpixels at centre pixel (2048,2048).

**PyTorch implementation:**
- Extend `scripts/debug_pixel_trace.py --taps hkl_subpixel`.
- For each subpixel `i` in [0,3]:
  - Log: `h_frac[i]`, `k_frac[i]`, `l_frac[i]`
  - Log: `h0[i]`, `k0[i]`, `l0[i]` (rounded)
  - Log: `F_cell[i]` (retrieved value)
  - Log: `out_of_bounds[i]` (boolean: did we use default_F?)

**C implementation:**
- Add `TRACE_C_TAP5_1` guards in `golden_suite_generator/nanoBragg.c` around the HKL lookup logic (lines 3300–3340, near the `Fhkl = stol_of(...)` block).
- Print identical schema.

**Expected Output (JSON/log):**
```json
{
  "tap_id": "hkl_subpixel",
  "pixel_coords": [2048, 2048],
  "subpixels": [
    {
      "subpixel_idx": 0,
      "h_frac": -1.125000004265e-07,
      "k_frac": 0.014999999915623,
      "l_frac": -0.014999999915623,
      "h0": 0,
      "k0": 0,
      "l0": 0,
      "F_cell": 0.0,  // C expects 0, PyTorch currently reports 100
      "out_of_bounds": false
    },
    // ... 3 more subpixels
  ]
}
```

**Acceptance Criteria:**
- If PyTorch's `out_of_bounds` flags are `true` for centre pixel but C's are `false`, H1 is confirmed.
- Document the exact `(h0, k0, l0)` values and compare grid index computation logic in both implementations.

---

#### Tap 5.2: HKL Grid Bounds Check

**Objective:** Print the HKL grid extents in both C and PyTorch to verify (0,0,0) is in-range.

**PyTorch implementation:**
- In `src/nanobrag_torch/models/crystal.py`, add debug log after HKL grid loading:
  ```python
  print(f"TRACE_PY_HKL_BOUNDS: h_min={self.h_min}, h_max={self.h_max}, "
        f"k_min={self.k_min}, k_max={self.k_max}, l_min={self.l_min}, l_max={self.l_max}")
  ```

**C implementation:**
- Add `TRACE_C_HKL_BOUNDS` in `golden_suite_generator/nanoBragg.c` after `read_text_file()` or `read_Fdump()` completes (around line 1800):
  ```c
  printf("TRACE_C_HKL_BOUNDS: h_min=%d h_max=%d k_min=%d k_max=%d l_min=%d l_max=%d\n",
         h_min, h_max, k_min, k_max, l_min, l_max);
  ```

**Expected Output:**
```
TRACE_C_HKL_BOUNDS: h_min=-50 h_max=50 k_min=-50 k_max=50 l_min=-50 l_max=50
TRACE_PY_HKL_BOUNDS: h_min=-50 h_max=50 k_min=-50 k_max=50 l_min=-50 l_max=50
```

**Acceptance Criteria:**
- Both implementations must report identical bounds.
- Verify that `0 ∈ [h_min, h_max]`, `0 ∈ [k_min, k_max]`, `0 ∈ [l_min, l_max]`.
- If bounds match but PyTorch still treats (0,0,0) as out-of-bounds, the bug is in the indexing arithmetic.

---

### Code Audit Focus (if Tap 5.1/5.2 confirm H1)

**PyTorch suspect lines:**
- `src/nanobrag_torch/models/crystal.py:get_structure_factor()` — nearest-neighbor lookup logic.
- Look for off-by-one errors in index computation (e.g., `h0 < h_min` vs. `h0 <= h_min`).

**C reference:**
- `golden_suite_generator/nanoBragg.c` lines 3300–3340 — `Fhkl = stol_of(...)` and grid indexing.
- Compare rounding logic (`ceil(h - 0.5)` vs. `round(h)`).

---

## H2: Subpixel Loop Accumulation Order (25% confidence)

### Evidence

1. **Edge pixel raw intensity:**
   - C: I_before_scaling = 141520.166
   - PyTorch: I_before_scaling = 35428.870
   - Ratio: 3.9945× (C higher)

2. **Omega/polar factors match:**
   - Omega: C=8.8611e-09, PyTorch=8.8614e-09 (0.003% delta)
   - Polar: C=0.96128, PyTorch=0.96129 (0.001% delta)

3. **Default_F usage identical:**
   - Tap 4 confirmed both use default_F = 100 for edge pixel.

### Hypothesis

C and PyTorch may sum `I_term = (F_cell²) × (F_latt²)` across subpixels in different orders, leading to compounded floating-point rounding errors.

**Counter-Evidence:**
- FP rounding should produce ≤1e-6 relative error, not 4×.
- The centre pixel's H1 divergence (HKL indexing bug) is more severe and may explain systematic bias.

### Required Evidence (Tap 5.1 edge)

**Objective:** Log per-subpixel `I_term` contributions for edge pixel (0,0).

**PyTorch implementation:**
- Extend `scripts/debug_pixel_trace.py --taps subpixel_intensity`.
- For each subpixel `i` in [0,3]:
  - Log: `F_cell[i]`, `F_latt[i]`, `I_term[i] = F_cell² × F_latt²`
  - Log: `I_accumulated[i] = sum(I_term[0:i+1])`

**C implementation:**
- Add `TRACE_C_TAP5_1_EDGE` in the oversample loop (nanoBragg.c:3400–3500).
- Print identical schema.

**Acceptance Criteria:**
- If per-subpixel `I_term` values match but cumulative `I_accumulated` diverges, the issue is summation order.
- If `I_term` values differ, the issue is in F_latt computation (unlikely given Tap 4 F_cell parity).

**Decision:** **Defer until H1 is resolved.** If centre pixel fix restores edge pixel parity, H2 becomes moot.

---

## H3: Water Background Implicit Scaling (10% confidence)

### Evidence

1. **Test case:** Both pixels use `-water 0`, so `I_bg = 0`.
2. **Centre pixel:** C reports `I_before_scaling = 0`, consistent with no background.
3. **Spec:** `specs/spec-a-core.md:245-249` states background is added before Bragg terms.

### Hypothesis

PyTorch might add a latent background term even when `-water 0`, inflating `I_before_scaling`.

**Counter-Evidence:**
- Centre pixel's `I_before_scaling = 1.538e8` matches `(F_cell²) × (F_latt²)` with `F_cell = 100`, `F_latt ≈ 124` (per C Tap 5 log).
- This is Bragg intensity, not background.
- Edge pixel shows no evidence of background inflation.

### Required Evidence (Tap 6)

**Objective:** Audit background term application in both implementations.

**Defer until:** H1 is resolved and centre pixel parity is restored.

---

## Recommended Action (Phase E11 Decision)

### Priority: Execute Tap 5.1 + Tap 5.2 (H1)

**Rationale:**
- H1 has 95% confidence and explains the centre pixel divergence.
- Tap 5.1 + Tap 5.2 are low-cost evidence gathering (no code changes).
- Confirming H1 will guide remediation in Phase F.

**Blockers:**
- Do NOT implement Phase F fixes until H1 is diagnosed.
- Do NOT pursue Tap 6 (water background) until centre pixel parity is restored.

**Next Actions:**
1. Draft Tap 5.1 / Tap 5.2 reproduction commands for `input.md`.
2. Update `plans/active/vectorization-parity-regression.md` Phase E table: mark E10 `[D]`, add E11 row with Tap 5.1/5.2 decision.
3. Commit Phase E10 artifacts (this memo + `intensity_pre_norm.md`) before next loop.

---

**End of Hypotheses Memo**
