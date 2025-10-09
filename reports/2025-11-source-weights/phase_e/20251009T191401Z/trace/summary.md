# TC-D1 Trace Parity Analysis

**Date:** 2025-10-09T19:14:01Z
**Mode:** Evidence-only (no code changes)
**Purpose:** Capture parallel trace to identify first C vs PyTorch divergence for SOURCE-WEIGHT-001

## Configuration

**Trace Pixel:** (slow=158, fast=147)
**Fixture:** `reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt`
- Source 1: (0, 0, 10) weight=1.0 wavelength=6.2e-10 m
- Source 2: (0, 0, 10) weight=0.2 wavelength=6.2e-10 m

**Shared Parameters:**
- `-lambda 0.9768` Å (CLI override per spec-a-core.md:150-151)
- `-default_F 100`
- `-distance 231.274660` mm
- `-pixel 0.172` mm
- `-detpixels_x 256 -detpixels_y 256`
- `-oversample 1`
- `-nonoise -nointerpolate`

## Key Findings

### 1. Source Count Divergence (PRIMARY BLOCKER)

**PyTorch:**
- Reports 2 sources (from fixture file)
- `steps = 2` (line 114 of py_trace.txt)

**C:**
- Creates 4 sources total (line 116-120 of c_trace.txt):
  ```
  0 0 0   0 0        # Zero-weight divergence placeholder 1
  0 0 0   0 0        # Zero-weight divergence placeholder 2
  0 0 10   1 6.2e-10  # Actual source from fixture
  0 0 10   0.2 6.2e-10 # Actual source from fixture
  ```
- `steps = 4` (line 296 of c_trace.txt)

**Impact:** 2× normalization error in final intensity. PyTorch divides by 2, C divides by 4.

### 2. Divergence Placeholder Sources (ARCHITECTURAL GAP)

The C code adds TWO zero-weight divergence sources with:
- Position: (0, 0, 0)
- Weight: 0
- Wavelength: 0

These sources participate in the `steps` denominator but contribute zero intensity due to:
- `lambda_meters = 0` → `scattering_vec_A_inv = inf -inf inf`
- `incident_vec = -0 -0 -0` (zero incident direction)
- `hkl_frac = -nan -inf -nan`
- Result: `F_latt = 1`, `F_cell = 100`, but effectively filtered out

**Trace Evidence (c_trace.txt lines 272-290):**
```
TRACE_C: incident_vec -0 -0 -0
TRACE_C: lambda_meters 0
TRACE_C: lambda_angstroms 0
TRACE_C: scattering_vec_A_inv inf -inf inf
TRACE_C: hkl_frac -nan -inf -nan
TRACE_C: hkl_rounded -2147483648 -2147483648 -2147483648
TRACE_C: F_latt_a 1
TRACE_C: F_latt_b 1
TRACE_C: F_latt_c 1
TRACE_C: F_latt 1
TRACE_C: F_cell 100
```

### 3. Geometry/Crystal Alignment (PASS)

**Both implementations agree on:**
- `pix0_vector_meters` (PyTorch: `0.231274664402008 0.0221880003809929 -0.0221880003809929`, C: `0.23127466 0.022188 -0.022188`) ✅
- `fdet_vec`, `sdet_vec` (basis vectors match) ✅
- `pixel_pos_meters` ✅
- `R_distance_meters` (both ≈0.2313521) ✅
- `omega_pixel_sr` (both ≈5.525e-07) ✅
- Rotated crystal vectors `rot_a_angstroms`, `rot_b_angstroms`, `rot_c_angstroms` (match to ~1e-6) ✅
- Reciprocal vectors `rot_a_star_A_inv`, `rot_b_star_A_inv`, `rot_c_star_A_inv` ✅

### 4. Physics Calculation Alignment (CONDITIONAL PASS)

**For the ACTUAL sources (sources 3 & 4 in C, sources 1 & 2 in PyTorch):**

**Fractional Miller indices:** Both compute valid `hkl_frac` ≈ (0.417, -0.422, 0.403) for non-zero wavelength.

**Lattice shape factors:** PyTorch computes individual components:
```
F_latt_a = 0.279455929994583
F_latt_b = 0.35054013133049
F_latt_c = 0.0503052361309528
F_latt = 0.00492792700969224 (product)
```

C only reports final `F_latt = 1` in the zero-wavelength trace shown. Need to compare a valid source contribution.

### 5. Scaling Chain Divergence (CRITICAL)

**PyTorch (for pixel (158, 147)):**
```
I_before_scaling_post_polar = 154450368
r_e_sqr = 7.9407927259064e-30
fluence = 1.25932017574725e+29
steps = 2
I_pixel_final = 42.6700248718262
```

**C (for same pixel):**
```
I_before_scaling = 104370.1042
r_e_sqr = 7.94079248018965e-30
fluence = 1.25932015286227e+29
steps = 4
I_pixel_final = 0.00720858779258755
```

**Ratios:**
- Intensity ratio (PyTorch/C): 42.67 / 0.0072 = **5926×**
- Expected from steps alone: 4/2 = 2×
- Additional factor: 5926 / 2 = **2963×**

This ~3000× divergence exceeds the 2× steps normalization error and points to a deeper physics mismatch.

### 6. Polar/Capture/Omega Factors

**PyTorch:**
```
polar = 0.999664902687073 (Kahn factor)
capture_fraction = 1
omega_pixel = 5.52540427634085e-07
```

**C:**
```
polar = 0.5 (Kahn factor)
capture_fraction = 1
omega_pixel = 5.52540430832495e-07
```

**Polar mismatch:** PyTorch ≈1.0, C = 0.5 → 2× additional factor.

Combining steps (2×) + polar (2×) = **4× expected divergence**. Observed 5926× suggests ~1500× additional error.

## Root Cause Hypothesis

1. **Steps normalization:** PyTorch counts only fixture sources (2), C counts fixture + divergence placeholders (4) → 2× error ✅ **CONFIRMED**
2. **Polarization factor:** PyTorch applies ~1.0, C applies 0.5 → 2× additional error ✅ **CONFIRMED**
3. **Remaining 1500× divergence:** Likely caused by:
   - Missing per-source polarization (PyTorch may be applying polarization only once vs per-source)
   - Source weighting still being applied despite Phase C/D fixes
   - Lambda override not fully propagating through all code paths
   - Divergence grid auto-generation interacting with source count

## Recommended Next Steps

1. **BLOCKER:** Implement zero-weight divergence placeholder generation when `hdivsteps=0` and `vdivsteps=0` to match C's 4-source count
2. **CRITICAL:** Debug the 1500× residual scaling error:
   - Check if PyTorch is multiplying by `source_weights` anywhere in the accumulation
   - Verify per-source polarization is applied correctly
   - Trace a single-source case to isolate the weighting vs polarization vs lambda effects
3. After steps + polarization fixes, rerun TC-D1 parity and expect correlation ≥0.999, |sum_ratio-1| ≤1e-3

## Artifacts

- `commands.txt` — Exact CLI commands for both PyTorch and C
- `py_trace.txt` — 140 lines of PyTorch step-by-step trace
- `c_trace.txt` — 326 lines of C step-by-step trace
- `diff.txt` — First divergence analysis (line 0: different header formats)
- `env.json` — Environment metadata (torch version, CUDA availability, trace pixel)
- `py_tc_d1.bin` — PyTorch float image output (256×256, max=42.67)
- `c_tc_d1.bin` — C float image output (256×256, max=0.0104)

## Spec/Architecture References

- `specs/spec-a-core.md:150-162` — Source weights/wavelengths ignored, CLI -lambda is authoritative
- `golden_suite_generator/nanoBragg.c:2570-2720` — Source ingestion and steps computation
- `src/nanobrag_torch/simulator.py:824-878` — PyTorch steps normalization and source accumulation
- `plans/active/source-weight-normalization.md` — Phase E parity requirements
- `docs/fix_plan.md:4035-4184` — SOURCE-WEIGHT-001 attempts history

## Conclusion

This evidence-only capture successfully identified the first divergence:

1. **Source count mismatch:** 2 (PyTorch) vs 4 (C) confirmed via trace logs
2. **Steps normalization gap:** PyTorch divides by 2, C divides by 4
3. **Polarization factor mismatch:** PyTorch ≈1.0, C = 0.5
4. **Residual 1500× error:** Requires deeper investigation (likely source weighting or per-source polarization)

The trace artifacts are stored under `reports/2025-11-source-weights/phase_e/20251009T191401Z/trace/` and ready for handoff to the implementation phase.

**Phase E3 (parity metrics) is BLOCKED** until the steps reconciliation and residual error debugging are complete.
