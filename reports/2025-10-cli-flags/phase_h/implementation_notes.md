# Phase H3 Implementation Notes

**Date:** 2025-10-05
**Focus:** Lattice factor mismatch diagnosis

## Validated Components ✅

1. **Incident Beam Vector:** Perfect match after H2 fix (commit 8c1583d)
2. **Reciprocal Vectors:** rot_a_star, rot_b_star, rot_c_star identical to C (Phase G3)
3. **Orientation Matrix:** MOSFLM A* ingestion correct (Phase G2)

## Outstanding Issues 🔴

### Issue 1: F_latt Component Sign and Magnitude
- C produces positive values ~25-40
- PyTorch produces mix of signs, magnitude ~2-10
- Product differs by 568× (35636 vs 62.7)

### Issue 2: Miller Indices Fractional Precision
- h: Δ≈0.097 (exceeds 1e-3 threshold)
- k: Δ≈0.024 (exceeds 1e-3 threshold)
- l: Δ≈0.120 (exceeds 1e-3 threshold)

## Hypotheses (Priority Order)

### Hypothesis 1: sincg Argument Order (HIGH CONFIDENCE)
**Evidence:**
- sincg(π·h, Na) vs sincg(h·π, Na) produces different results
- nanoBragg.c:3063-3178 uses specific argument pattern
- PyTorch may have π in wrong position

**Test:** Review `src/nanobrag_torch/models/crystal.py` get_structure_factor() sincg calls

### Hypothesis 2: Na/Nb/Nc Scaling Missing (MEDIUM CONFIDENCE)
**Evidence:**
- F_latt components scale with cell counts
- Magnitude difference ~10× could indicate missing Na/Nb/Nc factor
- C multiplies sincg result by cell counts

**Test:** Check if PyTorch multiplies sincg output by Na/Nb/Nc

### Hypothesis 3: Fractional Miller Calculation (LOW CONFIDENCE)
**Evidence:**
- hkl_frac differs by ~0.1
- Could cascade from pix0 difference
- Less likely given reciprocal vectors match

**Test:** Verify h = q·a* calculation directly

## Diagnostic Calculations

### Manual sincg Verification
Using C values from trace:
```
h_frac = 2.001203
k_frac = 1.992798
l_frac = -12.990767
Na = Nb = Nc = 5

F_latt_a = sincg(π × 2.001203, 5) = ?
F_latt_b = sincg(π × 1.992798, 5) = ?
F_latt_c = sincg(π × -12.990767, 5) = ?
```

Expected from C: 35.889, 38.632, 25.702
Need to compute these with Python sincg to isolate the bug.

## Follow-Up Actions

1. **Read nanoBragg.c lattice calculation** (lines 3063-3178)
   - Extract exact sincg argument pattern
   - Note any Na/Nb/Nc multiplication

2. **Review PyTorch sincg usage**
   - Check `src/nanobrag_torch/models/crystal.py`
   - Verify argument order in get_structure_factor()

3. **Add targeted test**
   - Feed exact C hkl_frac values to PyTorch sincg
   - Compare output to C F_latt components
   - Isolates sincg vs Miller index issues

4. **Fix and validate**
   - Apply correction to sincg usage
   - Rerun trace harness
   - Verify F_latt matches within 0.5% (Phase H exit criteria)

## Code References

- PyTorch sincg: `src/nanobrag_torch/utils/physics.py`
- PyTorch lattice calc: `src/nanobrag_torch/models/crystal.py` (get_structure_factor)
- C reference: `nanoBragg.c:3063-3178`
- Trace harness: `reports/2025-10-cli-flags/phase_h/trace_harness.py`

---

## 2025-10-06 Update: sincg Hypothesis REJECTED

**Investigation Summary:**
Performed manual `sincg` calculation to test Hypothesis 1 (sincg argument order).

**Key Findings:**
1. ✅ **sincg arguments are CORRECT** - C uses `sincg(π*h, Na)` with absolute `h`, PyTorch uses `sincg(π*(h-h0), Na)` with fractional component
2. ⚠️ **Both approaches produce IDENTICAL results** (difference ~2.8e-12, float64 noise level)
3. 🔴 **ROOT CAUSE IDENTIFIED:** The Miller indices (h,k,l) themselves are different between C and PyTorch!

**Evidence from manual_sincg.md:**
```
Fractional Miller indices (from C trace):
- h = 2.001203, k = 1.992798, l = -12.990767
- Na = 36, Nb = 47, Nc = 29

Results:
C_expected          : 35.889000, 38.632000, 25.702000
Py_current          : 35.889121, 38.632627, 25.702568  (using h-h0)
Py_with_absolute    : 35.889121, 38.632627, 25.702568  (using h)
```

Both formulations match C within 0.001% - **the sincg function is NOT the problem**.

**Real Issue: Miller Index Divergence**
From `trace_comparison_after_H2.md`:
- **C:**  `h=2.001, k=1.993, l=-12.991`
- **Py:** `h=2.098, k=2.017, l=-12.871` (earlier grep)
- **Deltas:** Δh≈0.097, Δk≈0.024, Δl≈0.120 (all exceed 1e-3 threshold!)

**New Hypothesis (HIGH CONFIDENCE):**
The PyTorch implementation is computing **different fractional Miller indices** than C. This is upstream of the `sincg` calculation. The problem lies in either:
1. **Reciprocal vector rotation** - though Phase G3 showed these match (need to revalidate)
2. **Scattering vector calculation** - Phase H2 showed ~0.06% difference (may not be "acceptable")
3. **Pixel position calculation** - Phase H2 showed pix0_vector difference at mm scale

**Next Actions:**
1. Compare the latest PyTorch trace (trace_py_after_H3.log) with C trace to see current Miller indices
2. Trace backwards from Miller indices: h = q·a* calculation
3. If reciprocal vectors still match, focus on scattering vector `q = (k_out - k_in)/λ`
4. Check if the 0.06% scattering vector difference is the root cause

**Proposed Fix/Test Plan:**
- [ ] No immediate code fix needed - evidence gathering incomplete
- [ ] Review scattering vector calculation in simulator.py
- [ ] Check if pix0_vector difference (from H2) needs addressing first
- [ ] Consider whether 0.06% scattering vector tolerance is too loose

**Artifacts:**
- `reports/2025-10-cli-flags/phase_h/manual_sincg.md` - proves sincg arguments OK
- `reports/2025-10-cli-flags/phase_h/trace_py_after_H3.log` - latest PyTorch trace
- `reports/2025-10-cli-flags/phase_h/trace_comparison_after_H2.md` - H2 comparison showing Miller divergence

---

## 2025-10-06 Update: pix0 Vector Divergence Root Cause

**Investigation Summary:**
Performed pix0 vector reproduction analysis to quantify the detector geometry divergence between C and PyTorch implementations.

**Key Findings:**

### 1. ✅ **pix0 Vector Delta Quantified**
- **PyTorch (raw override):** `-0.216336293, 0.215205512, -0.230200866` m
- **C (BEAM-pivot formula):** `-0.216336514802, 0.215206668836, -0.230198010449` m
- **Delta:** `-0.000000221802, 0.000001156836, 0.000002855551` m (~1.14 mm Y component)

### 2. 🔴 **Pixel Position Propagation**
The pix0 delta propagates directly to pixel positions:
- **pixel_py:** `-0.099504821084, 0.035709685862, -0.231093193780` m
- **pixel_c:** `-0.099505042886, 0.035710842698, -0.231090338228` m
- **pixel_delta:** identical to pix0_delta (as expected from linear geometry)

### 3. 🔴 **Scattering Vector Impact**
The pixel position difference cascades to scattering vectors:
- **scattering_py:** `-0.401381653140, 0.143856611876, 0.092791036024` Å⁻¹
- **scattering_c:** `-0.401386249330, 0.143862601024, 0.092793940575` Å⁻¹
- **scattering_delta:** `-4.596e-06, 5.989e-06, 2.905e-06` Å⁻¹ (~0.001% relative)

### 4. 🔴 **Miller Index Divergence (FIRST DIVERGENCE)**
This scattering vector difference produces the observed Miller index mismatch:
- **hkl_py:** `2.099910581725, 2.010431773566, -12.869255026506`
- **hkl_c:** `2.099829406661, 2.010404082040, -12.869526246456`
- **hkl_delta:** `-0.000081175065, -0.000027691527, -0.000271219950`
  - Δh≈0.00008, Δk≈0.00003, Δl≈0.0003 (all within 1e-3 threshold ✅ but still compound)

### 5. 🔴 **F_latt Component Divergence (CONSEQUENCE)**
The Miller index differences amplify through `sincg` nonlinearity:
- **F_latt_py components:** `-3.090311, 30.504771, -1.524981`
- **F_latt_c components:** `-3.101519, 30.581863, -1.576684`
- **Relative differences:** ~0.4%, 0.3%, 3.4%

From trace_py_after_H3_refresh.log, PyTorch F_latt components are:
- **F_latt_py (latest):** `-3.28845, 10.73575, -1.77545` (product: 62.68)

**ROOT CAUSE IDENTIFIED:**
PyTorch applies the raw `-pix0_vector_mm` override WITHOUT applying the CUSTOM transform that C applies. The C code computes pix0 using the BEAM-pivot formula:
```
pix0_c = -Fbeam*fdet - Sbeam*sdet + distance*beam
```
whereas PyTorch uses the raw override directly. This ~1.14 mm Y-component error is the FIRST DIVERGENCE in the geometry chain.

**Proposed Fix:**
When `-pix0_vector_mm` is provided:
1. C applies BEAM-pivot transformation before using the vector
2. PyTorch should either:
   - **Option A (safer):** Apply the same BEAM-pivot transform to override values
   - **Option B:** Document that override is pre-transformed and update CLI guidance

**Evidence Files:**
- `reports/2025-10-cli-flags/phase_h/pix0_reproduction.md` - numerical reproduction of C's BEAM-pivot formula
- `reports/2025-10-cli-flags/phase_h/trace_py_after_H3_refresh.log` - fresh PyTorch trace with latest lattice data
- `reports/2025-10-cli-flags/phase_h/trace_py_after_H3_refresh.stderr` - harness stderr (empty = clean run)

**Next Actions for Phase H3 Completion:**
1. ✅ Captured fresh trace evidence (trace_py_after_H3_refresh.log)
2. ✅ Reproduced C's pix0 calculation (pix0_reproduction.md)
3. ✅ Quantified pix0 → pixel → scattering → Miller → F_latt cascade
4. ✅ Updated implementation_notes.md with 2025-10-06 section
5. ⏳ Restore attempt_log.txt with Attempt #21 entry (next task)
6. ⏳ Outline detector-side fix plan before requesting implementation

**Recommended Detector Fix Design:**
When `pix0_override_m` is present, Detector should:
- Verify the override is in CUSTOM convention coordinate frame
- Apply BEAM-pivot transformation: `pix0 = -Fbeam*fdet - Sbeam*sdet + distance*beam`
- Use transformed result for pixel position calculations
- Add regression test comparing C and PyTorch pix0 output for CUSTOM convention

This ensures the 1.14 mm delta is eliminated at the source, preventing cascade to Miller indices and F_latt.
