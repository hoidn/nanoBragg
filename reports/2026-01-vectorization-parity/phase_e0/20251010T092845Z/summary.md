# Phase E0 Callchain Summary

**Date**: 2025-10-10
**Initiative**: vectorization-parity-edge
**Analysis Question**: Why does 4096×4096 full-frame correlation remain at 0.721 when 512×512 ROI achieves 1.000000?

---

## Problem Statement

- **Success Zone**: 512×512 ROI (detector center, pixels 1792-2303) achieves **perfect parity**:
  - Correlation: 1.000000 (0.9999999985)
  - Sum ratio: 0.999987
  - RMSE: 3.28e-05

- **Failure Zone**: 4096×4096 full-frame fails **dramatically**:
  - Correlation: 0.721177 (required ≥0.999, delta −0.277823)
  - Speedup (warm): 0.81× (slower than C)

- **Implication**: Phase D lattice fixes (unit conversions) resolved central physics but left residual bugs in edge/background handling.

---

## Callchain Findings

### Entry Point

**`Simulator.run()`** (`src/nanobrag_torch/simulator.py:700`) orchestrates:
1. Auto-oversample calculation
2. Pixel coordinate retrieval (cached)
3. Crystal lattice vector rotation
4. Source array preparation
5. Subpixel sampling loop
6. Physics computation per position
7. Normalization/scaling chain
8. Background addition
9. ROI/mask application (post-hoc)

### Factor Order (Execution Sequence)

1. **Physics computation** → raw intensity (dimensionless)
2. **Subpixel accumulation** → sum over `oversample²` grid
3. **Last-value omega** (if `oversample_omega=False`) → multiply by last subpixel's solid angle
4. **Detector absorption** (if enabled) → parallax-based attenuation
5. **Steps division** → divide by `n_sources × phi × mosaic × oversample²`
6. **Physical scaling** → multiply by `r_e² × fluence`
7. **Water background** → add uniform `I_bg` to all pixels
8. **ROI masking** → zero out excluded pixels

### Normalization Chain Constants (Global, Uniform)

- **`steps`**: `n_sources × phi_steps × mosaic_domains × oversample²` (line 892)
- **`r_e_sqr`**: 7.94079248018965e-30 m² (line 524)
- **`fluence`**: 1.259e29 photons/m² (default, line 528)
- **`I_bg`**: Uniform water background (if `water_size_um > 0`, line 1795)

**Conclusion**: Steps, r_e², and fluence are **identical for all pixels** → NOT the source of edge discrepancy.

---

## Primary Divergence Hypothesis

### **Oversample Last-Value Semantics** (🔴 HIGH CONFIDENCE)

**Mechanism**:

1. **Configuration defaults** (`config.py:205-207`):
   - `oversample_omega = False` → Use last subpixel's omega, not average
   - `oversample_polar = False` → Use last subpixel's polarization
   - `oversample_thick = False` → Use last layer's absorption

2. **Edge pixel behavior**:
   - Steep viewing angles → airpath R increases → solid angle ω decreases
   - Subpixel grid spans pixel area (e.g., 2×2 for `oversample=2`)
   - Last subpixel (bottom-right corner) has **different** ω than center

3. **Asymmetry quantification**:
   - For **symmetric center pixels**: last-subpixel ω ≈ mean ω (negligible bias)
   - For **asymmetric edge pixels**: last-subpixel ω can differ by 5-10% from mean

4. **PyTorch implementation** (`simulator.py:1027-1030`):
   ```python
   if not oversample_omega:
       last_omega = omega_all[:, :, -1]  # Last subpixel's solid angle
       accumulated_intensity = accumulated_intensity * last_omega
   ```

5. **C-code uncertainty**:
   - **Unknown**: Does C-code average omega across subpixels OR use last-value?
   - **Hypothesis**: C-code likely averages, creating systematic bias vs PyTorch

**Impact**:
- **Center 512×512 ROI**: Minimal asymmetry → last-value ≈ average → parity holds
- **Edge regions**: High asymmetry → last-value ≠ average → correlation drops

**Validation Path**:
1. Generate C trace for edge pixel (0,0) with `oversample=2`
2. Extract omega values for all 4 subpixels from C log
3. Compare to PyTorch's `omega_all` tensor
4. Check if C applies average vs last-value

---

## Secondary Suspects

### **F_cell=0 Edge Bias** (🟡 MEDIUM CONFIDENCE)

**Mechanism**:
- Edge pixels probe wider range of Miller indices (h,k,l)
- More likely to exceed HKL table bounds → return `default_F=0`
- **Location**: `crystal.py:227, 251-252`

**Impact**:
- Zero Bragg signal → only water background contributes
- Changes signal-to-background ratio non-uniformly

**Validation**:
- Count `out_of_bounds_count` for edge vs center pixels (Tap 4)
- If edge pixels have >50% more zeros, this contributes

### **Water Background Ratio Effect** (🟡 MEDIUM CONFIDENCE)

**Mechanism**:
- Background `I_bg` is **uniform** (constant per pixel)
- Bragg signal dims at edges due to omega falloff (`ω ∝ 1/R²`)
- Uniform background becomes relatively stronger at edges

**Impact**:
- Center: High Bragg signal, low background fraction → clean correlation
- Edges: Low Bragg signal, high background fraction → noisy correlation

**Validation**:
- Rerun full-frame with `water_size_um=0` (disable background)
- If correlation improves, background ratio is culprit

### **ROI Timing (C vs PyTorch)** (🟢 LOW CONFIDENCE)

**Mechanism**:
- **PyTorch**: Computes all pixels, then zeros excluded via mask (post-hoc)
- **C-code**: May skip computation for ROI-excluded pixels (early-exit)

**Impact**:
- Numerical rounding differences accumulate differently
- Unlikely to cause 0.721 correlation (too large)

**Validation**:
- Read C-code pixel loop for ROI condition structure
- Check if `if (inside_roi) { compute(); }` OR `compute(); mask();`

---

## First Taps to Collect

### Recommended Execution Order

1. **Tap 2: Omega Per-Subpixel (Edge Pixel)**
   - Purpose: Quantify asymmetry in solid angle distribution
   - Expected outcome: `relative_asymmetry > 0.05` confirms hypothesis
   - Runtime: <1 second (single pixel)

2. **Tap 3: Omega Per-Subpixel (Center Pixel)**
   - Purpose: Baseline comparison for symmetric case
   - Expected outcome: `relative_asymmetry ≈ 0.001` (negligible)

3. **Tap 4: F_cell Lookup Statistics**
   - Purpose: Count `default_F=0` occurrences (edge vs center)
   - Expected outcome: Edge has 2-5× more zeros if HKL bounds issue

4. **Tap 6: Post-Scaling, Pre-Background**
   - Purpose: Isolate Bragg signal before background dilution
   - Expected outcome: Signal-to-background ratio differs edge vs center

### Minimal Reproduction Command

**Single edge pixel** (fast trace):
```bash
export NB_TRACE_EDGE_PIXEL="0,0"
nb-compare --roi 0 1 0 1 -- \
  -default_F 100 -cell 100 100 100 90 90 90 -lambda 0.5 \
  -distance 500 -detpixels 4096 -pixel 0.05 -N 5 \
  -oversample 2 -floatfile /tmp/edge.bin
```

**Center pixel** (baseline):
```bash
export NB_TRACE_CENTER_PIXEL="2048,2048"
nb-compare --roi 2048 2049 2048 2049 -- \
  -default_F 100 -cell 100 100 100 90 90 90 -lambda 0.5 \
  -distance 500 -detpixels 4096 -pixel 0.05 -N 5 \
  -oversample 2 -floatfile /tmp/center.bin
```

---

## Next Steps (Phase E0d → E1)

### Immediate Actions (Phase E0d)

1. **Synthesize diagnostics** into `phase_e0_summary.md` ✅ (this document)
2. **Update `docs/fix_plan.md`** `[VECTOR-PARITY-001]` Next Actions:
   - "Execute Tap 2/3 for omega asymmetry quantification"
   - "Generate C trace for pixel (0,0) with oversample=2"
   - "Compare C omega handling: average vs last-value"

### Phase E1 Verification (After Taps)

1. **If omega asymmetry confirmed** (`relative_asymmetry > 0.05`):
   - Modify PyTorch to average omega (not last-value)
   - Rerun full-frame benchmark
   - Expected: Correlation improves from 0.721 → >0.99

2. **If F_cell=0 bias confirmed** (edge has 2×+ more zeros):
   - Extend HKL table bounds OR
   - Verify C-code uses same `default_F=0` semantics

3. **If background ratio confirmed** (correlation improves with `water_size=0`):
   - Document as known edge dimming effect
   - Not a bug, but a geometric consequence

---

## Open Questions Requiring Confirmation

1. **C-code omega handling**: Average across subpixels OR last-value? (Read `nanoBragg.c` oversample loop)
2. **HKL table symmetry**: Do C and PyTorch use identical bounds? (Compare `hkl_metadata`)
3. **ROI early-exit**: Does C-code skip or mask? (Read pixel loop structure)

---

## Artifacts Generated

- `callchain/static.md`: Complete execution flow with file:line anchors
- `trace/tap_points.md`: 7 proposed numeric taps for parity debugging
- `summary.md`: This one-page narrative ✅
- `callchain_brief.md`: Initial scoping variables

**Storage**: `reports/2026-01-vectorization-parity/phase_e0/20251010T092845Z/`

---

## Conclusion

The **oversample last-value semantics** (omega, polar, absorption) is the most likely culprit for full-frame parity failure. Edge pixels with asymmetric subpixel profiles accumulate systematic bias when PyTorch multiplies by the last subpixel's factors instead of averaging. This hypothesis is **testable via Tap 2** (omega asymmetry quantification) and **confirmable via C-code inspection** (average vs last-value). Phase E1 remediation depends on tap outcomes.
