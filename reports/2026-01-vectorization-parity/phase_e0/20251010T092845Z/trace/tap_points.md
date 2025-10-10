# Phase E0 Numeric Tap Points

**Purpose**: Propose 5–7 numeric tap locations for edge-pixel parity debugging, aligned to the static callgraph and focused on the oversample/omega/background hypothesis.

---

## Tap 1: Config Snapshot (Entry)

**Key**: `config_snapshot`
**Purpose**: Capture all runtime configuration affecting edge behavior
**Owning Function**: `Simulator.run()` (simulator.py:700)
**Expected Units**: Mixed (mm, degrees, dimensionless counts)

**Tap Values**:
```python
{
    'oversample': int,              # Auto-selected or explicit
    'oversample_omega': bool,       # False = last-value, True = per-subpixel
    'oversample_polar': bool,
    'oversample_thick': bool,
    'roi_xmin': int, 'roi_xmax': int, 'roi_ymin': int, 'roi_ymax': int,
    'fpixels': int, 'spixels': int,
    'pixel_size_mm': float,
    'distance_mm': float,
    'water_size_um': float,
    'default_F': float,
    'steps': int                    # Normalization denominator
}
```

**Rationale**: Confirms configuration parity before execution. Mismatches here explain downstream divergences.

---

## Tap 2: Omega Per-Subpixel (Edge Pixel)

**Key**: `omega_subpixel_edge`
**Purpose**: Measure solid angle variation across subpixel grid for edge pixel
**Owning Function**: `simulator.py:1000-1030` (subpixel omega calculation)
**Expected Units**: steradians

**Tap Values** (for pixel (0,0) or (4095,4095)):
```python
{
    'pixel_coords': (slow, fast),           # Pixel index
    'oversample': int,                       # Subpixel grid size
    'omega_all': torch.Tensor,              # Shape: (oversample, oversample)
    'omega_center': float,                  # omega[oversample//2, oversample//2]
    'omega_last': float,                    # omega[-1, -1] (last subpixel)
    'omega_mean': float,                    # torch.mean(omega_all)
    'omega_std': float,                     # torch.std(omega_all)
    'relative_asymmetry': float             # |omega_last - omega_mean| / omega_mean
}
```

**Rationale**: Quantifies asymmetry in solid angle across subpixel grid. High asymmetry + `oversample_omega=False` → bias.

---

## Tap 3: Omega Per-Subpixel (Center Pixel)

**Key**: `omega_subpixel_center`
**Purpose**: Baseline comparison for symmetric center pixel
**Owning Function**: `simulator.py:1000-1030` (same as Tap 2)
**Expected Units**: steradians

**Tap Values** (for pixel (2048,2048)):
```python
# Same structure as Tap 2, but for center pixel
{
    'pixel_coords': (2048, 2048),
    'omega_all': torch.Tensor,
    'omega_center': float,
    'omega_last': float,
    'omega_mean': float,
    'omega_std': float,
    'relative_asymmetry': float
}
```

**Rationale**: Symmetric center pixel should have `relative_asymmetry ≈ 0`. Establishes baseline for edge comparison.

---

## Tap 4: F_cell Lookup Statistics (Edge vs Center)

**Key**: `f_cell_stats`
**Purpose**: Count out-of-bounds HKL lookups returning `default_F=0`
**Owning Function**: `crystal.get_structure_factor()` (crystal.py:210-245)
**Expected Units**: dimensionless (counts, electrons)

**Tap Values** (accumulated over all subpaths for one pixel):
```python
{
    'pixel_coords': (slow, fast),
    'total_lookups': int,                   # Total (h0,k0,l0) evaluations
    'out_of_bounds_count': int,             # Lookups outside HKL grid
    'zero_f_count': int,                    # F_cell = 0 returned
    'mean_f_cell': float,                   # Average F_cell (electrons)
    'hkl_bounds': {                         # HKL table extents
        'h_min': int, 'h_max': int,
        'k_min': int, 'k_max': int,
        'l_min': int, 'l_max': int
    }
}
```

**Rationale**: If edge pixels have higher `out_of_bounds_count`, they rely more on `default_F=0` → different signal composition.

---

## Tap 5: Pre-Normalization Intensity (Raw Accumulation)

**Key**: `intensity_pre_norm`
**Purpose**: Capture intensity before steps division and physical scaling
**Owning Function**: `simulator.py:1136-1159` (final scaling logic)
**Expected Units**: dimensionless (raw counts)

**Tap Values** (for edge and center pixels):
```python
{
    'pixel_coords': (slow, fast),
    'accumulated_intensity': float,         # Sum over all subpixels/sources
    'last_omega_applied': float,           # If oversample_omega=False
    'steps': int,                           # Normalization denominator
    'normalized_intensity': float          # accumulated / steps (before r_e²·fluence)
}
```

**Rationale**: Compares raw accumulated counts before scaling. If edge/center differ here, issue is in physics loop, not normalization.

---

## Tap 6: Post-Scaling, Pre-Background

**Key**: `intensity_post_scale`
**Purpose**: Capture intensity after r_e²·fluence scaling but before background addition
**Owning Function**: `simulator.py:1154-1162`
**Expected Units**: photons

**Tap Values**:
```python
{
    'pixel_coords': (slow, fast),
    'physical_intensity': float,            # After r_e²·fluence·(I/steps)
    'r_e_sqr': float,                       # 7.94e-30 m²
    'fluence': float,                       # photons/m²
    'water_background': float               # I_bg (uniform, if water_size_um > 0)
}
```

**Rationale**: Isolates Bragg signal before background dilutes it. Enables signal-to-background ratio comparison.

---

## Tap 7: Final Output & ROI Mask

**Key**: `final_output`
**Purpose**: Confirm ROI masking behavior and final pixel values
**Owning Function**: `simulator.py:1166-1259` (ROI application and return)
**Expected Units**: photons

**Tap Values** (for representative pixels):
```python
{
    'edge_pixel': {
        'coords': (0, 0),
        'intensity_before_mask': float,
        'roi_mask_value': int,              # 0 or 1
        'intensity_after_mask': float       # Should be 0 if outside ROI
    },
    'center_pixel': {
        'coords': (2048, 2048),
        'intensity_before_mask': float,
        'roi_mask_value': int,
        'intensity_after_mask': float
    },
    'roi_excluded_pixel': {                 # Pixel known to be outside ROI
        'coords': (100, 100),               # Example
        'intensity_before_mask': float,
        'roi_mask_value': int,              # Should be 0
        'intensity_after_mask': float       # Should be 0
    }
}
```

**Rationale**: Verifies ROI masking correctness. If `intensity_after_mask ≠ 0` for excluded pixel, mask logic is broken.

---

## Tap Execution Strategy

### Minimal ROI for Edge Focus

**Recommended**: Single-pixel ROI covering edge and center:
- Edge pixel: `(0,0)` or `(4095,4095)`
- Center pixel: `(2048,2048)`

**Command** (nb-compare with tight ROI):
```bash
nb-compare --roi 0 1 0 1 -- \
  -default_F 100 -cell 100 100 100 90 90 90 -lambda 0.5 \
  -distance 500 -detpixels 4096 -pixel 0.05 -N 5 \
  -oversample 2
```

### Tap Instrumentation

**Option A**: Environment variable triggers (lightweight)
```bash
export NB_TRACE_EDGE_PIXEL="0,0"
export NB_TRACE_CENTER_PIXEL="2048,2048"
export NB_TRACE_TAPS="omega,f_cell,norm"
```

**Option B**: Dedicated trace script (Phase E0c deliverable)
```python
# scripts/trace_edge_diagnostics.py
# Invokes simulator with instrumentation hooks, writes tap JSON
```

**Output Format**: JSON per tap
```json
{
  "tap_id": "omega_subpixel_edge",
  "pixel": [0, 0],
  "timestamp": "2025-10-10T09:28:45Z",
  "values": { ... }
}
```

---

## Tap Validation Checklist

Before deploying taps:
1. ✅ Confirm owning functions exist at cited file:line anchors
2. ✅ Verify expected units match variable types (e.g., omega in steradians)
3. ✅ Ensure tap reads cached/computed values, does NOT re-derive physics
4. ✅ Check device/dtype neutrality (taps should work on CPU and CUDA)
5. ✅ Validate key names are stable across traces (enables diff tooling)

---

## First Tap to Collect (Priority Recommendation)

**Tap 2: Omega Per-Subpixel (Edge Pixel)**

**Rationale**:
- Oversample last-value semantics is the #1 hypothesis
- Omega variation quantifies asymmetry magnitude
- Single-pixel ROI makes trace fast (<1 second)
- Directly confirms or refutes primary divergence theory

**Expected Outcome**:
- If `relative_asymmetry > 0.05` (5% variation), last-value bias is significant
- If `omega_last` differs from C-code's applied omega by >1%, explains edge divergence
