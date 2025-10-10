# PyTorch Tap 5 — Intensity Pre-Normalization

**Attempt:** #29
**Date:** 2025-10-10T11:07:35Z
**Scope:** Phase E0 Task E8 — PyTorch intensity tap for edge and centre pixels

## Objective

Capture intensity accumulation metrics for `--taps intensity` to quantify pre-normalization values and identify any discrepancies between edge (0,0) and centre (2048,2048) pixels.

## Configuration

- **Test case:** 4096×4096 detector, 0.05mm pixel, 500mm distance, λ=0.5Å, MOSFLM convention
- **Crystal:** 100Å cubic cell, 5×5×5 unit cells, default_F=100
- **Oversample:** 2×2 grid (4 subpixels per pixel)
- **Pixels tested:**
  - Edge: (0, 0)
  - Centre: (2048, 2048)

## Commands Executed

```bash
# Edge pixel (0, 0)
KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py \
  --pixel 0 0 --tag edge --oversample 2 --taps intensity --json \
  --out-dir reports/2026-01-vectorization-parity/phase_e0/20251010T110735Z/py_taps

# Centre pixel (2048, 2048)
KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py \
  --pixel 2048 2048 --tag centre --oversample 2 --taps intensity --json \
  --out-dir reports/2026-01-vectorization-parity/phase_e0/20251010T110735Z/py_taps
```

## Results

### Edge Pixel (0, 0)

| Metric | Value | Notes |
|--------|-------|-------|
| **Accumulated intensity** (F_cell² × F_latt²) | 3.5429e+04 | Raw intensity before final scaling |
| **Steps** (sources × phi × mosaic × oversample²) | 4 | 1 source × 1 phi × 1 mosaic × 2² oversample |
| **Last omega applied** | 8.8614e-09 sr | Solid angle of last subpixel |
| **Last capture fraction** | 1.0 | No detector absorption |
| **Last polarization** | 0.9613 | Unpolarized at 2θ≈16° |
| **Normalized intensity** (final) | 7.5448e-05 | After r_e² × fluence / steps × capture × polar × ω |

**Stored artifacts:**
- `pixel_0_0_intensity_pre_norm.json`
- `pixel_0_0.log` (full trace)
- `pixel_0_0_metadata.json`

### Centre Pixel (2048, 2048)

| Metric | Value | Notes |
|--------|-------|-------|
| **Accumulated intensity** (F_cell² × F_latt²) | 1.5380e+08 | ~4340× higher than edge (on-peak) |
| **Steps** (sources × phi × mosaic × oversample²) | 4 | Same as edge |
| **Last omega applied** | 1.0000e-08 sr | Solid angle at beam centre (slightly larger) |
| **Last capture fraction** | 1.0 | No detector absorption |
| **Last polarization** | 1.0000 | Unpolarized at 2θ≈0° (beam centre) |
| **Normalized intensity** (final) | 0.3845 | ~5100× higher than edge |

**Stored artifacts:**
- `pixel_2048_2048_intensity_pre_norm.json`
- `pixel_2048_2048.log` (full trace)
- `pixel_2048_2048_metadata.json`

## Key Observations

1. **Intensity ratio (centre/edge):**
   - Accumulated intensity: 1.5380e+08 / 3.5429e+04 ≈ **4340×**
   - Normalized intensity: 0.3845 / 7.5448e-05 ≈ **5096×**
   - The difference arises from geometric factors (ω≈1.13×, polar≈1.04×)

2. **Omega variation:**
   - Edge: 8.8614e-09 sr
   - Centre: 1.0000e-08 sr
   - Ratio: ~1.13× (centre has slightly larger solid angle due to obliquity)

3. **Polarization variation:**
   - Edge: 0.9613 (2θ≈16°)
   - Centre: 1.0000 (2θ≈0°, beam centre)
   - Ratio: ~1.04×

4. **Steps normalization:**
   - Both pixels divide by 4 (oversample²=4)
   - This is consistent with C-code expectation for oversample=2

5. **Pre-normalization formula verified:**
   - I_pixel = r_e² × fluence × (F_cell² × F_latt²) / steps × capture × polar × ω
   - All multiplicative factors match trace output

## Compliance with Plan Guidance

- ✅ Extended `scripts/debug_pixel_trace.py` with `--taps intensity` flag
- ✅ Captured JSON for pixels (0,0) & (2048,2048) at oversample=2
- ✅ Stored outputs under `reports/2026-01-vectorization-parity/phase_e0/<STAMP>/py_taps/`
- ✅ Cited `specs/spec-a-core.md` §§472–476 (intensity accumulation formula)
- ✅ Avoided recomputing physics; reused `I_before_scaling`, `steps`, `omega`, `r_e_sqr`, `fluence`, `capture_fraction`, `polar`

## Next Steps (per plan)

- **E9:** Instrument C binary (`golden_suite_generator/nanoBragg`) around lines 3770–3815 with `TRACE_C_TAP5` guards for intensity pre-normalization
- **E10:** Compare Tap 5 PyTorch vs C outputs to determine if discrepancies persist before scaling or if Tap 6 (water background) evidence is required

## References

- Plan: `plans/active/vectorization-parity-regression.md` Phase E0 Tasks E8–E10
- Spec: `specs/spec-a-core.md` §§246–259 (Sampling & Accumulation normative formula)
- Architecture: `arch.md` §8 (Differentiability Guidelines)
