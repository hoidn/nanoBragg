# Phase C3 Summary: First Divergence Analysis Complete

**Timestamp:** 2025-10-10T06:16:05Z
**Phase:** C3 — Trace Diff & First Divergence
**Status:** ✅ **Complete** — Root causes identified

---

## Key Findings

### First Divergence: Line 45 (scattering_vec_A_inv)

**Magnitude:** ~10⁷× unit error (C in m⁻¹, PyTorch in Å⁻¹)
**Pixels Analyzed:** 3 (background, on-peak mid-detector, edge high-order)
**Pattern:** Systematic across all pixels regardless of position

### Three Critical Bugs Identified

1. **Scattering Vector Unit Conversion** (Hypothesis 1 — HIGH CONFIDENCE)
   - Factor: 10⁷×
   - Root cause: Missing or inverted m⁻¹ ↔ Å⁻¹ conversion
   - Impact: Complete physics incorrectness downstream

2. **Fluence Calculation** (Hypothesis 2 — HIGH CONFIDENCE)
   - Factor: 10⁹×
   - Root cause: Unit inconsistency in flux/exposure/beamsize formula
   - Impact: Intensity scaling completely wrong

3. **F_latt Normalization** (Hypothesis 3 — MEDIUM-HIGH CONFIDENCE)
   - Factor: ~100× (varies by reflection order)
   - Root cause: Missing crystal size (Na×Nb×Nc) normalization in sincg
   - Impact: Lattice factors systematically under-scaled

### Geometric Parity Confirmed ✅

All detector geometry quantities match C↔PyTorch to ≤10⁻¹² relative tolerance:
- pix0_vector: exact
- basis vectors (fdet, sdet, odet): exact
- pixel_pos_meters: exact
- obliquity_factor: exact
- omega_pixel_sr: exact

**Conclusion:** Detector implementation is correct and complete. Divergence begins at physics calculations, not geometry.

---

## Pixel Details

### Pixel (2048, 2048) — ROI Core
- **Type:** Background (hkl = 0,0,0)
- **C intensity:** 0.0 (no HKL file)
- **Py intensity:** 1.01e-13 (default_F active)
- **First divergence:** scattering_vec 10⁷× error

### Pixel (1792, 2048) — First ROI Row Outside
- **Type:** On-peak (hkl = 0,5,0)
- **C intensity:** 0.269 (bright spot)
- **Py intensity:** 9.45e-14 (signal lost)
- **First divergence:** scattering_vec 10⁷× error + F_latt 50× error

### Pixel (4095, 2048) — Far Edge
- **Type:** High-order reflection (hkl = −4,−40,0)
- **C intensity:** 0.451 (bright spot)
- **Py intensity:** 4.24e-16 (signal completely lost)
- **First divergence:** scattering_vec 10¹⁰× error + F_latt 1000× error

---

## Next Actions (Delegated to Debugging Loop)

1. **Fix scattering_vec unit conversion** (blocking)
   - Location: `simulator.py` or `utils/physics.py`
   - Search: `q = (d - i) / lambda`

2. **Fix fluence calculation** (blocking)
   - Location: `config.py` (BeamConfig) or simulator scaling
   - Audit: unit consistency in fluence formula

3. **Fix F_latt normalization** (blocking)
   - Location: `utils/physics.py::sincg`
   - Compare: C-code sincg implementation

4. **Revalidate full chain** after each fix
   - Rerun Phase C2 PyTorch traces
   - Rerun nb-compare (expect corr ≥ 0.999)
   - Rerun test_at_parallel_012 (expect pass)

---

## Artifacts

**Main Report:** `first_divergence.md`
**This Summary:** `summary.md`
**Metadata:** `env/trace_env.json`
**Commands:** `commands.txt`
**C Traces (Phase C1):** `../20251010T053711Z/c_traces/`
**Py Traces (Phase C2):** `../20251010T055346Z/py_traces/`

---

## Confidence Assessment

**Hypothesis 1 (scattering_vec):** 95% confidence — unit factor exactly matches theory
**Hypothesis 2 (fluence):** 90% confidence — systematic 10⁹× error consistent with unit bug
**Hypothesis 3 (F_latt):** 85% confidence — pattern matches missing normalization

**Overall:** Root causes are well-constrained. Implementation fixes should be straightforward and testable via trace rerun.

---

## Status Gate

Phase C3 is **COMPLETE**. Evidence package is ready for delegation to debugging/implementation loop.

**Blocking for:** `[VECTOR-PARITY-001]` exit criteria (corr ≥ 0.999, |sum_ratio−1| ≤ 5×10⁻³)
