# Phase E0 Static Callchain Analysis

**Analysis Question**: Why does the 4096×4096 full-frame parity stay at 0.721 when the 512×512 ROI achieves 1.000000 correlation? Focus: edge/background factors, scaling chain, and normalization.

**Date**: 2025-10-10
**Initiative**: vectorization-parity-edge

---

## Analysis Context

- **ROI Success** (512² center): correlation=1.000000, sum_ratio=0.999987 ✅
- **Full-Frame Failure** (4096² complete): correlation=0.721177 ❌
- **Implication**: Phase D lattice fixes resolved central physics but residual bugs exist at edges/background

---

## Candidate Entry Points

| Candidate | Relevance | Confidence | Expected Code Region |
|-----------|-----------|------------|---------------------|
| `Simulator.run()` | Primary CLI/API entry; orchestrates pixel iteration | **High** | `src/nanobrag_torch/simulator.py:700` |
| `__main__.main()` | CLI argument parsing and config setup | Medium | `src/nanobrag_torch/__main__.py:832` |
| `_compute_physics_for_position()` | Core physics kernel for single position | Medium | `src/nanobrag_torch/simulator.py:19` |

**Selected Entrypoint**: `Simulator.run()` (simulator.py:700) — orchestrates the full pixel loop with ROI masking, oversample logic, and final scaling.

**Rationale**: This is the top-level simulation orchestrator that applies ROI boundaries, handles oversample logic, and invokes normalization/scaling chains. Edge pixel behavior is controlled here.

---

## Config Flow

### Where Inputs Enter Pipeline

| Config Source | File:Line | Keys Accessed | Purpose |
|---------------|-----------|---------------|---------|
| `DetectorConfig.__post_init__()` | config.py:236-381 | `roi_xmin/xmax/ymin/ymax`, `oversample`, `detector_pivot` | Validate ROI bounds, set defaults |
| `BeamConfig.__post_init__()` | config.py:536-539 | `fluence`, `flux`, `exposure`, `beamsize_mm` | Compute fluence from flux/exposure |
| `CrystalConfig` defaults | config.py:145 | `default_F = 0.0` | Default structure factor for missing reflections |
| `Simulator.__init__()` | simulator.py:429-628 | All configs → cached tensors | Cache ROI mask, pixel coords, r_e², fluence |

### ROI Mask Construction (Critical)

**Location**: `simulator.py:571-604`

**Logic**:
```python
if roi_xmin < 0 or roi_ymin < 0 or roi_xmax >= fpixels or roi_ymax >= spixels:
    # ROI specified → build binary mask (1 inside, 0 outside)
    roi_mask = torch.zeros((spixels, fpixels), dtype=torch.bool, device=device)
    roi_mask[roi_ymin:roi_ymax+1, roi_xmin:roi_xmax+1] = True
else:
    # No ROI → all pixels included
    roi_mask = torch.ones((spixels, fpixels), dtype=torch.bool, device=device)
```

**Application Timing**: ROI mask is applied **AFTER** all physics/scaling (line 1166-1206), not during iteration. This is post-hoc zeroing, not early-exit optimization.

---

## Core Pipeline Stages

### Entry → Pixel Iteration Loop

| Stage | Function | File:Line | Purpose |
|-------|----------|-----------|---------|
| **1. Entry** | `Simulator.run()` | simulator.py:700 | Top-level orchestrator |
| **2. Auto-oversample** | `_calculate_recommended_oversample()` | simulator.py:779-803 | `ceil(3 × xtalsize_max / reciprocal_pixel_size)` |
| **3. Pixel coords** | `detector.get_pixel_coords()` (cached) | simulator.py:569, 809-813 | Retrieve all pixel 3D positions in meters |
| **4. Lattice vectors** | `crystal.get_rotated_real_vectors()` | simulator.py:818-863 | Rotated a/b/c, a*/b*/c* (Å → m) |
| **5. Sources** | Prepare beam directions/λ/weights | simulator.py:867-892 | Setup n_sources, wavelengths, weights |
| **6. Steps calculation** | `steps = n_sources × phi × mosaic × oversample²` | simulator.py:892 | Normalization denominator |

### Subpixel Sampling (oversample > 1)

**Location**: `simulator.py:898-941`

**Formula** (subpixel offsets):
```python
subpixel_step = pixel_size_m / oversample
subpixel_offsets = torch.linspace(
    -0.5 * pixel_size_m + subpixel_step / 2,
    0.5 * pixel_size_m - subpixel_step / 2,
    oversample
)
```

**Centering**: Offsets are pixel-centered (symmetric around center). Last subpixel is at `+0.5 * pixel_size - step/2`.

**Iteration**: For each pixel, generate `oversample × oversample` 3D subpixel coordinates by adding offsets to pixel center.

### Physics Computation (Per Position)

**Location**: `compute_physics_for_position()` (simulator.py:19-418)

**Key Steps**:

1. **Scattering vector** (line 103-158):
   ```python
   q = (diffracted_unit - incident_unit) / wavelength_meters
   ```
   Units: m⁻¹ (Phase D fix applied here)

2. **Miller indices** (line 168-203):
   ```python
   h = dot_product(q, rot_a)
   k = dot_product(q, rot_b)
   l = dot_product(q, rot_c)
   h0, k0, l0 = round_to_nearest(h, k, l)
   ```

3. **Structure factor lookup** (line 206-211 → crystal.py:210-245):
   ```python
   F_cell = crystal.get_structure_factor(h0, k0, l0)
   # Returns config.default_F (0.0) if no HKL data or out-of-bounds
   ```

4. **Lattice structure factor** (line 215-306):
   ```python
   F_latt = sincg(π·h, Na) × sincg(π·k, Nb) × sincg(π·l, Nc)
   ```

5. **Intensity** (line 308-323):
   ```python
   intensity = |F_cell × F_latt|²
   # Sum over φ and mosaic dimensions
   ```

6. **Polarization** (line 326-403):
   ```python
   if apply_polarization:
       polar = polarization_factor(kahn, incident, diffracted, axis)
       intensity = intensity * polar
   ```

7. **Source accumulation** (line 405-418):
   ```python
   # Equal weighting: sum across sources (ignore source_weights)
   intensity = torch.sum(intensity, dim=0)
   ```

---

## Normalization/Scaling Chain

**Execution Order (Critical Sequence)**:

### 1. Subpixel Accumulation

**Location**: `simulator.py:1013-1033` (oversample mode)

```python
# Sum over all oversample² subpixels
accumulated_intensity = torch.sum(intensity_all, dim=2)  # Shape: (S, F)
```

**Last-Value Omega** (if `oversample_omega=False`, line 1027-1030):
```python
last_omega = omega_all[:, :, -1]  # Last subpixel's solid angle
accumulated_intensity = accumulated_intensity * last_omega
```

**Units**: Dimensionless → steradian·dimensionless (after omega)

### 2. Solid Angle Calculation

**Location**: `simulator.py:1000-1030` (subpixel) or `1087-1102` (center-only)

**Formula** (obliquity mode, `point_pixel=False`):
```python
omega = (pixel_size_m ** 2 / airpath_m ** 2) * (close_distance_m / airpath_m)
```

**Formula** (point-pixel mode, `point_pixel=True`):
```python
omega = 1.0 / (airpath_m ** 2)
```

**Variables**:
- `airpath_m`: Distance from sample to pixel (R in spec)
- `close_distance_m`: Perpendicular distance to detector plane
- `pixel_size_m`: Physical pixel size

**Units**: steradians

**Edge Sensitivity**: `airpath_m` increases for edge pixels → `omega` decreases → dimmer edges (geometric falloff).

### 3. Detector Absorption

**Location**: `simulator.py:1130-1134` → `_apply_detector_absorption()` (1809-1900)

**Formula** (last-value mode, `oversample_thick=False`):
```python
parallax = detector_normal · observation_direction
t = thicksteps - 1  # Last layer index
delta_z = detector_thick_um / thicksteps
mu = 1 / detector_abs_um
capture_fraction = exp(-t*Δz*μ/ρ) - exp(-(t+1)*Δz*μ/ρ)
intensity = intensity * capture_fraction
```

**Units**: Dimensionless attenuation factor

**Edge Sensitivity**: Parallax factor (`ρ = d·o`) varies with observation angle → different absorption at edges.

### 4. Steps Division & Physical Scaling

**Location**: `simulator.py:1154-1159`

**Formula**:
```python
physical_intensity = (
    normalized_intensity / steps
    * r_e_sqr
    * fluence
)
```

**Constants**:
- `r_e_sqr = 7.94079248018965e-30` m² (line 524-526)
- `fluence = 125932015286227086360700780544.0` photons/m² (default, line 528 from config.py:518)
- `steps = n_sources × phi_steps × mosaic_domains × oversample²` (line 892)

**Units**: `[dimensionless] / [count] × [m²] × [photons/m²] = [photons]`

**Uniformity**: All three scaling factors (steps, r_e², fluence) are **global constants** — same for every pixel. **NOT** a source of edge discrepancy.

### 5. Water Background Addition

**Location**: `simulator.py:1162-1164` → `_calculate_water_background()` (1752-1807)

**Formula**:
```python
F_bg = 2.57  # Water forward scattering amplitude
Avogadro = 6.02214179e23  # mol⁻¹
water_MW = 18.0  # g/mol
water_size_m = water_size_um * 1e-6  # μm to meters

I_bg = (
    F_bg * F_bg
    * r_e_sqr
    * fluence
    * (water_size_m ** 3)
    * 1e6  # Unit inconsistency factor (matches C code)
    * Avogadro
    / water_MW
)

# Uniform background for all pixels
background = torch.full((spixels, fpixels), I_bg, device=device, dtype=dtype)
physical_intensity = physical_intensity + background
```

**Units**: photons (per pixel)

**Uniformity**: `I_bg` is **uniform** across all pixels (constant additive term).

**Edge Impact**: Changes signal-to-background ratio. If Bragg signal is dim at edges (due to omega falloff), uniform background becomes relatively stronger → different correlation behavior.

---

## Sinks/Outputs

### Final ROI & Mask Application

**Location**: `simulator.py:1166-1206`

**Logic**:
```python
# Apply ROI mask (post-hoc zeroing)
physical_intensity = physical_intensity * roi_mask.float()

# Apply detector mask if present
if detector_mask is not None:
    physical_intensity = physical_intensity * detector_mask.float()
```

**Timing**: Applied **AFTER** all physics, normalization, and background addition.

**Semantics**: Multiplicative mask (0 or 1) zeros out excluded pixels. Does NOT skip computation for those pixels during iteration.

### Return Value

**Location**: `simulator.py:1257-1259`

```python
return physical_intensity  # Shape: (spixels, fpixels), dtype: float32/float64
```

---

## Callgraph Edge List

| Caller | Callee | Why | File:Line → File:Line |
|--------|--------|-----|---------------------|
| `Simulator.run()` | `detector.get_pixel_coords()` | Retrieve cached 3D pixel positions | 569, 809 → detector.py:398 |
| `Simulator.run()` | `crystal.get_rotated_real_vectors()` | Get φ/mosaic-rotated lattice vectors | 818 → crystal.py:379 |
| `Simulator.run()` | `_compute_physics_for_position()` | Wrapper for physics kernel | 1015, 1044 → 636 |
| `_compute_physics_for_position()` | `compute_physics_for_position()` | Core physics (Miller indices, F, I) | 680 → 19 |
| `compute_physics_for_position()` | `crystal.get_structure_factor()` | Lookup F_cell for (h0,k0,l0) | 206 → crystal.py:210 |
| `compute_physics_for_position()` | `sincg()` | Lattice structure factor (SQUARE) | 260, 265, 270 → utils/physics.py:73 |
| `compute_physics_for_position()` | `polarization_factor()` | Kahn polarization correction | 373 → utils/physics.py:310 |
| `Simulator.run()` | `_calculate_water_background()` | Compute uniform background | 1162 → 1752 |
| `Simulator.run()` | `_apply_detector_absorption()` | Parallax-based attenuation | 1130 → 1809 |

---

## Data/Units & Constants

| Variable | Units | Definition | File:Line |
|----------|-------|------------|-----------|
| `pixel_coords_angstroms` | Å | 3D pixel positions in Angstroms | simulator.py:22 |
| `scattering_vector` | m⁻¹ | q = (d−i)/λ | simulator.py:158 |
| `h, k, l` | dimensionless | Miller indices (fractional) | simulator.py:193-195 |
| `F_cell` | electrons | Structure factor magnitude | simulator.py:206 |
| `F_latt` | dimensionless | Lattice transform factor | simulator.py:258 |
| `intensity` | dimensionless | \|F_cell × F_latt\|² | simulator.py:308 |
| `omega` | steradians | Pixel solid angle | simulator.py:1000 |
| `steps` | count | Normalization denominator | simulator.py:892 |
| `r_e_sqr` | m² | 7.94079248018965e-30 | simulator.py:524 |
| `fluence` | photons/m² | 1.259e29 (default) | simulator.py:528 |
| `physical_intensity` | photons | Final scaled output | simulator.py:1154 |
| `I_bg` | photons | Uniform water background | simulator.py:1795 |

---

## Device/Dtype Handling

| Location | Assumption | File:Line |
|----------|------------|-----------|
| `Simulator.__init__()` | All tensors initialized on `self.device` with `self.dtype` | 429-628 |
| `compute_physics_for_position()` | Inputs already on correct device (no `.to()` calls) | 19-418 |
| Constants (r_e², fluence) | Created on `self.device` with `self.dtype` | 524, 528 |
| ROI mask | Cached boolean mask on `self.device` | 571-604 |

**Neutrality**: Device/dtype are set once at init and propagated. No mixed-device operations.

---

## Gaps/Unknowns + Confirmation Plan

### Gap 1: Oversample Last-Value Semantics Verification

**Question**: Does C-code apply last-subpixel omega/polar/absorption OR average across subpixels?

**Confirmation**:
1. Read C-code `nanoBragg.c` lines covering oversample loops (search for `oversample` keyword)
2. Check if `omega_pixel`/`polar`/`capture` are updated in-loop or stored from last iteration
3. Compare to PyTorch flags: `oversample_omega`, `oversample_polar`, `oversample_thick` (all default `False` → last-value)

**Suspicion**: If C-code averages but PyTorch uses last-value, edge pixels with asymmetric profiles will diverge.

### Gap 2: F_cell=0 Edge Bias

**Question**: Do edge pixels hit more `default_F=0` reflections due to HKL table bounds?

**Confirmation**:
1. Load HKL data (`crystal.hkl_metadata`) and extract `h_min/max`, `k_min/max`, `l_min/max`
2. Run simulator with trace for edge pixel (e.g., (0,0)) and center pixel (e.g., (2048,2048))
3. Count number of subpaths where `(h0,k0,l0)` is out-of-bounds → returns `default_F=0`

**Suspicion**: Edges have more out-of-bounds lookups → more zero contributions → lower correlation if C-code handles differently.

### Gap 3: ROI Mask Timing (C vs PyTorch)

**Question**: Does C-code zero ROI-excluded pixels post-hoc OR skip their computation entirely?

**Confirmation**:
1. Read C-code main pixel loop (search for `roi` or `xmin/xmax/ymin/ymax`)
2. Check if ROI condition is an `if (inside_roi) { compute(); }` OR `compute(); result *= roi_mask;`

**Suspicion**: If C-code skips computation, numerical rounding differences may accumulate differently than PyTorch's post-hoc zeroing.

### Gap 4: Water Background Ratio Effect

**Question**: What fraction of edge pixels have Bragg signal vs pure background?

**Confirmation**:
1. Run simulator with `water_size_um=0` (disable background) and measure full-frame correlation
2. If correlation improves, background ratio is culprit
3. If correlation stays low, issue is in physics/scaling chain

**Suspicion**: Uniform background changes signal-to-background ratio non-uniformly (edges have dimmer Bragg signal due to omega falloff).

---

## Summary: First Divergence Hypothesis

**Primary Suspect**: **Oversample last-value semantics** (`oversample_omega=False`)

**Mechanism**:
1. Edge pixels have steep viewing angles → airpath R increases → omega decreases
2. Subpixel grid spans pixel area → last subpixel (bottom-right) has different omega than center
3. With `oversample_omega=False`, PyTorch multiplies accumulated intensity by **last subpixel's omega only**
4. For symmetric center pixels, this approximates average; for asymmetric edge pixels, it introduces bias
5. C-code may average omega across all subpixels (needs confirmation)

**Secondary Suspects**:
- **F_cell=0 edge bias**: More out-of-bounds HKL lookups at edges
- **Water background ratio**: Uniform background relatively stronger at dim edges
- **ROI timing**: C-code may skip vs PyTorch post-hoc zeroing (numerical artifacts)

**Next Actions**:
1. Generate C trace for edge pixel (0,0) and center pixel (2048,2048) with identical parameters
2. Compare omega values (per-subpixel vs final applied)
3. Count `F_cell=0` occurrences (edge vs center)
4. Rerun full-frame with `oversample_omega=True` and check if correlation improves
