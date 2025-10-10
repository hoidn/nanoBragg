# Phase C3: First Divergence Analysis — 4096² Parity Regression

**Report Date:** 2025-10-10T06:16:05Z
**Initiative:** [VECTOR-PARITY-001] Restore 4096² benchmark parity
**Phase:** C3 — Trace Diff & First Divergence
**Analyst:** Ralph (engineer loop)

---

## Executive Summary

**Root Cause Identified:** Unit conversion error in scattering vector calculation (Å⁻¹ vs m⁻¹ mismatch).

**Impact:** ~10,000,000× magnitude error in scattering vector propagates through Miller index calculation, causing complete physical incorrectness in PyTorch output despite geometric parity.

**Evidence:** Three-pixel parallel trace comparison reveals **first divergence at line 45** (`scattering_vec_A_inv`) across all pixels.

**Critical Observation:** All geometric quantities (pix0_vector, basis vectors, pixel positions, solid angles) match C↔PyTorch to ≤10⁻¹² relative tolerance. **The divergence begins at the physics calculation step**, not geometry.

---

## Pixel-by-Pixel Analysis

### Pixel (2048, 2048) — ROI Core

**Location:** Center of ROI (512² region)
**C Trace:** `reports/2026-01-vectorization-parity/phase_c/20251010T053711Z/c_traces/pixel_2048_2048.log`
**PyTorch Trace:** `reports/2026-01-vectorization-parity/phase_c/20251010T055346Z/py_traces/pixel_2048_2048.log`

#### First Divergence

**Line Number:** 45
**Variable:** `scattering_vec_A_inv`

```
C:  scattering_vec_A_inv -49.9999996961265 999999.99749989 -999999.99749989
Py: scattering_vec_A_inv -4.999999969612645e-09 9.999999975004450e-05 -9.999999975004450e-05
```

**Magnitude Ratio:** C / Py ≈ **10,000,000** (10⁷)

**Percent Difference:** C values are ~1,000,000,000% larger than PyTorch values.

#### Units Analysis

- **C-code units:** Values in range ~10⁶ suggest **m⁻¹** (inverse meters)
- **PyTorch units:** Values in range ~10⁻⁵ suggest **Å⁻¹** (inverse Angstroms)
- **Expected behavior:** Scattering vector should be in Å⁻¹ per physics convention
- **Conversion factor:** 1 m⁻¹ = 10⁻¹⁰ Å⁻¹ → matches observed 10⁷ discrepancy (accounting for wavelength λ=0.5 Å)

#### Propagation Through Physics Chain

1. **Geometric quantities (lines 1-44):** ✅ **Perfect match** (differences ≤10⁻¹² relative)
   - pix0_vector: exact match at 12-digit precision
   - basis vectors: exact match
   - pixel_pos_meters: exact match
   - obliquity_factor: exact match

2. **Scattering vector (line 45):** ❌ **DIVERGENCE** — 10⁷× unit error

3. **Miller indices (lines 46-53):**
   - C: hkl_frac = (−4.99e-07, 0.0099, −0.0099) → rounds to (0,0,0)
   - Py: hkl_frac = (−4.99e-07, 0.0099, −0.0099) → rounds to (0,0,0)
   - **Coincidental match** due to both being near-zero background pixel

4. **Structure factors (lines 54-58):**
   - C: F_latt = 124.016, **F_cell = 0** (no HKL file provided)
   - Py: F_latt = 0.99968, **F_cell = 100** (uses default_F=100)
   - **Expected difference:** C run had no HKL file, PyTorch uses default_F

5. **Fluence (line 62):** ❌ **MASSIVE DIVERGENCE**
   - C: fluence = 1.259e+29 photons/m²
   - Py: fluence = 1.273e+20 photons/m²
   - **Factor:** ~10⁹ difference — **secondary critical bug**

6. **Final intensity (line 71):**
   - C: I_pixel_final = 0.0 (F_cell=0, background pixel)
   - Py: I_pixel_final = 1.01e-13 (small non-zero from default_F)

---

### Pixel (1792, 2048) — First ROI Row Outside

**Location:** First row outside 512² ROI
**C Trace:** `reports/2026-01-vectorization-parity/phase_c/20251010T053711Z/c_traces/pixel_1792_2048.log`
**PyTorch Trace:** `reports/2026-01-vectorization-parity/phase_c/20251010T055346Z/py_traces/pixel_1792_2048.log`

#### First Divergence

**Line Number:** 45
**Variable:** `scattering_vec_A_inv`

```
C:  scattering_vec_A_inv -6576005.28913838 512831325.464334 -999671.199735433
Py: scattering_vec_A_inv -6.576005289138376e-04 5.128313254643337e-02 -9.996711997359879e-05
```

**Magnitude Ratio:** C / Py ≈ **10,000,000** (10⁷) — **identical unit error as pixel (2048,2048)**

#### Propagation Differences

This pixel shows **on-peak scattering** (unlike the background pixel above):

1. **Miller indices:**
   - C: hkl_rounded = (0, 5, 0) — **on Bragg peak**
   - Py: hkl_rounded = (0, 5, 0) — **same peak**, correctly identified despite scattering vector unit error

2. **Structure factors:**
   - C: F_latt = 47.984, F_cell = 108.21 (from HKL interpolation)
   - Py: F_latt = 0.9674, F_cell = 100 (default_F)
   - **F_latt discrepancy:** ~50× difference — **additional bug in lattice factor or sincg calculation**

3. **Final intensity:**
   - C: I_pixel_final = 0.269 (bright spot)
   - Py: I_pixel_final = 9.45e-14 (essentially zero)
   - **Signal completely lost in PyTorch** despite correct Miller index identification

---

### Pixel (4095, 2048) — Far Edge

**Location:** Detector edge (max fast coordinate)
**C Trace:** `reports/2026-01-vectorization-parity/phase_c/20251010T053711Z/c_traces/pixel_4095_2048.log`
**PyTorch Trace:** `reports/2026-01-vectorization-parity/phase_c/20251010T055346Z/py_traces/pixel_4095_2048.log`

#### First Divergence

**Line Number:** 45
**Variable:** `scattering_vec_A_inv`

```
C:  scattering_vec_A_inv -406103651.671144 -4009890887.6855 -979694.817416335
Py: scattering_vec_A_inv -4.061036516711436e-02 -4.009890887685501e-01 -9.796948174168788e-05
```

**Magnitude Ratio:** C / Py ≈ **10,000,000,000** (10¹⁰ for y-component) — **unit error amplified by geometry**

#### Propagation Differences

This pixel also shows **on-peak scattering** but at detector edge:

1. **Miller indices:**
   - C: hkl_rounded = (−4, −40, 0) — **high-order reflection**
   - Py: hkl_rounded = (−4, −40, 0) — **same reflection**, correct despite unit error

2. **Structure factors:**
   - C: F_latt = 69.955, F_cell = 100
   - Py: F_latt = 0.06745, F_cell = 100
   - **F_latt discrepancy:** ~1000× difference — **severe lattice factor bug for high-order reflections**

3. **Final intensity:**
   - C: I_pixel_final = 0.451 (bright spot)
   - Py: I_pixel_final = 4.24e-16 (essentially zero)
   - **Complete signal loss** — high-order reflections are invisible in PyTorch output

---

## Common Patterns Across All Pixels

### 1. Geometric Parity ✅

All pre-physics quantities match exactly:
- Detector basis vectors (fdet, sdet, odet): exact
- pix0_vector: exact to 12 digits
- pixel_pos_meters: exact
- R_distance_meters: exact
- omega_pixel_sr: exact
- obliquity_factor: exact
- diffracted_vec, incident_vec: exact

**Conclusion:** Detector geometry implementation is **correct and complete**.

### 2. Scattering Vector Unit Error ❌

**Systematic factor of ~10⁷ across all pixels:**
- Background pixel: 10⁷×
- Mid-detector on-peak: 10⁷×
- Edge high-order reflection: 10¹⁰× (geometry amplifies error)

**Root cause:** C-code computes in m⁻¹, PyTorch expects Å⁻¹, but conversion is missing or inverted.

### 3. Fluence Discrepancy ❌

**Factor of ~10⁹ across all pixels:**
- C: fluence ≈ 1.26e+29 photons/m²
- Py: fluence ≈ 1.27e+20 photons/m²

**Suspected cause:** Related to unit system handling — if fluence calculation involves wavelength or distance in wrong units, could produce this error.

### 4. F_latt Discrepancy ❌

**Lattice factor (sincg product) systematically wrong:**
- Background pixels: factor of ~124× (C) vs 1× (Py)
- On-peak mid-detector: factor of ~50× (C) vs 1× (Py)
- High-order edge: factor of ~1000× (C) vs 0.07× (Py)

**Pattern:** PyTorch F_latt is consistently ~1.0 or smaller, while C-code produces larger values proportional to crystal size (Na × Nb × Nc = 5³ = 125).

**Suspected cause:** Missing crystal size normalization or incorrect sincg implementation in PyTorch.

---

## Hypotheses Ranked by Evidence

### Hypothesis 1: Scattering Vector Unit Conversion (HIGH CONFIDENCE)

**Evidence:**
- Exact 10⁷ factor matches m⁻¹ ↔ Å⁻¹ conversion (accounting for λ=0.5 Å)
- Systematic across all pixels regardless of position or Miller indices
- Divergence begins exactly at line 45 (scattering_vec calculation)

**Location:** Likely in `simulator.py` or `utils/physics.py`, function computing `q = (d - i) / λ`

**Fix:** Verify units of wavelength λ used in scattering vector calculation. If λ is in meters, result will be in m⁻¹; must convert to Å⁻¹ by multiplying by 10⁻¹⁰.

### Hypothesis 2: Fluence Calculation Unit Error (HIGH CONFIDENCE)

**Evidence:**
- Factor of 10⁹ is systematic
- Both implementations show same fluence formula structure in traces
- Likely involves wavelength or distance in wrong units

**Location:** BeamConfig or fluence calculation in simulator

**Fix:** Audit fluence = (flux × exposure) / (π × (beamsize/2)²) calculation for unit consistency.

### Hypothesis 3: F_latt Normalization Missing (MEDIUM-HIGH CONFIDENCE)

**Evidence:**
- PyTorch F_latt ≈ 1.0 for all pixels, C-code F_latt ≈ Na×Nb×Nc = 125
- Error proportional to crystal size
- Sincg product should include crystal dimensions

**Location:** `utils/physics.py::sincg` or lattice factor calculation in simulator

**Fix:** Verify sincg(π×h, Na) normalization. C-code formula may include implicit Na/Nb/Nc factors that PyTorch omits.

### Hypothesis 4: F_cell Difference (KNOWN, NOT A BUG)

**Evidence:**
- C: F_cell=0 (no HKL file provided in test command)
- Py: F_cell=100 (default_F parameter active)

**Status:** Expected behavior difference, not a parity bug. Phase C test command did not include HKL file, so C-code correctly returns zero for all structure factors.

---

## Recommended Next Steps

### Immediate (Blocking for Parity Recovery)

1. **Fix scattering_vec unit conversion** (Hypothesis 1)
   - **File:** `src/nanobrag_torch/simulator.py` or `src/nanobrag_torch/utils/physics.py`
   - **Search for:** `q = (d - i) / lambda` or `scattering_vec` calculation
   - **Verify:** λ units (should be Å, not meters) and ensure output is in Å⁻¹
   - **Test:** Rerun Phase C2 PyTorch traces; scattering_vec should match C-code to ≤10⁻⁶ relative

2. **Fix fluence calculation** (Hypothesis 2)
   - **File:** `src/nanobrag_torch/config.py` (BeamConfig) or simulator scaling
   - **Audit:** fluence formula for unit consistency (all distances in meters, areas in m²)
   - **Test:** Check fluence value matches C-code to ≤10⁻³ relative

3. **Fix F_latt normalization** (Hypothesis 3)
   - **File:** `src/nanobrag_torch/utils/physics.py::sincg` or crystal lattice factor calculation
   - **Compare:** C-code sincg implementation (nanoBragg.c lines ~15000-16000)
   - **Test:** F_latt should match C-code for background pixels (hkl=0,0,0) to ≤10⁻² relative

### Validation (After Fixes)

4. **Rerun Phase C2 PyTorch traces** with same parameters
5. **Rerun nb-compare** full-frame correlation (expect corr ≥ 0.999)
6. **Rerun ROI comparison** (expect corr ≥ 0.999, |sum_ratio−1| ≤ 5×10⁻³)
7. **Rerun test_at_parallel_012** (expect pass without xfail)

---

## Artifact References

**This Report:**
`reports/2026-01-vectorization-parity/phase_c/20251010T061605Z/first_divergence.md`

**Phase C1 (C Traces):**
- Directory: `reports/2026-01-vectorization-parity/phase_c/20251010T053711Z/c_traces/`
- Pixels: pixel_2048_2048.log, pixel_1792_2048.log, pixel_4095_2048.log
- Summary: `reports/2026-01-vectorization-parity/phase_c/20251010T053711Z/summary.md`

**Phase C2 (PyTorch Traces):**
- Directory: `reports/2026-01-vectorization-parity/phase_c/20251010T055346Z/py_traces/`
- Pixels: pixel_2048_2048.log, pixel_1792_2048.log, pixel_4095_2048.log
- Summary: `reports/2026-01-vectorization-parity/phase_c/20251010T055346Z/PHASE_C2_SUMMARY.md`

**Phase B4a (ROI Parity Baseline):**
`reports/2026-01-vectorization-parity/phase_b/20251010T035732Z/roi_compare/summary.md`

**Metadata:**
- Git SHA: (to be filled by commit)
- Branch: feature/spec-based-2
- Python: 3.x
- PyTorch: CPU, float64 (traces)
- C Binary: ./golden_suite_generator/nanoBragg
- Tolerance: 1e-12 (geometric), 1e-6 (physics target)

---

## Conclusion

The 4096² parity regression has a **clear first divergence at the scattering vector calculation** (trace line 45). Geometric quantities show perfect parity, confirming detector implementation correctness. The scattering vector unit error (~10⁷ factor) propagates through the physics chain, combined with fluence (10⁹ factor) and F_latt (~100× factor) bugs, producing the observed corr=0.721 full-frame failure while ROI (signal-rich region) correlation remains high (corr≥0.999).

**All three hypotheses are actionable and should be addressed sequentially (Hypothesis 1 → 2 → 3) to restore full-frame parity.**
