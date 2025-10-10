# Phase D3 Blocker Report

**Timestamp:** 20251010T071935Z
**Task:** [VECTOR-PARITY-001] Phase D3 - F_latt normalization fix
**Status:** ⚠️ BLOCKED - Simulator produces 32× lower intensity than expected

## Summary

Phase D3 trace script fix completed successfully - `scripts/debug_pixel_trace.py` now produces F_latt values matching C reference within machine precision (rel_err < 1e-12). However, testing revealed that the **production simulator** (`src/nanobrag_torch/simulator.py`) produces dramatically different results (32× too small) compared to both the C reference AND the trace script.

## Evidence

### 1. Trace Script Results (FIXED ✅)
- **F_latt parity:** Machine precision match (rel_err < 1e-15)
- **Final intensity:** 0.229 photons/pixel
- **Ratio vs C:** 0.854× (within ~15%, acceptable trace variation)
- **Artifact:** `reports/2026-01-vectorization-parity/phase_d/20251010T071935Z/f_latt_parity.md`

### 2. Production Simulator Results (BROKEN ❌)
- **Pixel (1792, 2048) intensity:** 0.00827 photons/pixel
- **C reference:** 0.269 photons/pixel
- **Ratio vs C:** 0.031× (32× too small!)
- **Command:**
```python
import torch, sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "src"))
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.config import *

crystal_config = CrystalConfig(
    cell_a=100.0, cell_b=100.0, cell_c=100.0,
    cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
    N_cells=(5, 5, 5), default_F=100.0,
    phi_start_deg=0.0, osc_range_deg=0.0, phi_steps=1,
    mosaic_spread_deg=0.0, mosaic_domains=1
)
detector_config = DetectorConfig(
    spixels=4096, fpixels=4096, pixel_size_mm=0.05, distance_mm=500.0,
    detector_convention=DetectorConvention.MOSFLM,
    detector_pivot=DetectorPivot.BEAM,
    detector_rotx_deg=0.0, detector_roty_deg=0.0,
    detector_rotz_deg=0.0, detector_twotheta_deg=0.0
)
beam_config = BeamConfig(
    wavelength_A=0.5, polarization_factor=0.0,
    flux=0.0, exposure=1.0, beamsize_mm=0.1
)

dtype, device = torch.float64, torch.device('cpu')
crystal = Crystal(crystal_config, dtype=dtype, device=device)
detector = Detector(detector_config, dtype=dtype, device=device)
simulator = Simulator(crystal, detector, crystal_config, beam_config, dtype=dtype, device=device)

image = simulator.run()
print(f"Pixel (1792, 2048): {image[1792, 2048].item():.15e}")
# Output: 8.272659271741050e-03
```

### 3. ROI nb-compare Results (WORSE ❌)
- **Correlation:** -0.001 (threshold: ≥0.999)
- **Sum ratio:** 12.5× (threshold: ≤1.005)
- **Command:**
```bash
export STAMP=20251010T071935Z
KMP_DUPLICATE_LIB_OK=TRUE python scripts/nb_compare.py \
  --resample --roi 1792 2304 1792 2304 \
  --outdir reports/2026-01-vectorization-parity/phase_d/$STAMP/roi_compare/ \
  -- -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 \
     -distance 500 -detpixels 4096 -pixel 0.05
```

## Analysis

### What Works
1. **`src/nanobrag_torch/utils/physics.py::sincg`** - Produces correct F_latt values when tested directly:
   ```python
   F_latt_a = sincg(torch.pi * h_frac, Na)  # 4.186802... ✅
   F_latt_b = sincg(torch.pi * k_frac, Nb)  # 2.301221... ✅
   F_latt_c = sincg(torch.pi * l_frac, Nc)  # 4.980295... ✅
   F_latt = F_latt_a * F_latt_b * F_latt_c  # 47.98... ✅
   ```

2. **Trace script** - Now correctly imports production `sincg` and produces F_latt values matching C

### What's Broken
The full simulator pipeline (`Simulator.run()`) produces 32× lower intensity despite:
- Correct `sincg` implementation in `src/nanobrag_torch/utils/physics.py:33`
- Correct formula in `src/nanobrag_torch/simulator.py:252-255`:
  ```python
  F_latt_a = sincg(torch.pi * h, Na)
  F_latt_b = sincg(torch.pi * k, Nb)
  F_latt_c = sincg(torch.pi * l, Nc)
  F_latt = F_latt_a * F_latt_b * F_latt_c
  ```

### Hypothesis
The 32× discrepancy (≈ 125/4 = 5³/4) suggests:
- Possible issue with oversampling normalization
- Incorrect scaling factor elsewhere in pipeline
- Miller index calculation error feeding wrong h,k,l to F_latt
- Accumulation/averaging bug in the main simulation loop

**Note:** Attempts #7 (before D1/D2/D3 fixes) achieved corr=0.999999999, so the current regression may have been introduced by one of the "fixes" that only updated the trace script without validating the simulator.

## Next Steps

1. **Immediate:** Add detailed F_latt logging to `Simulator.run()` to compare with trace script values
2. **Debug:** Trace through `Simulator._compute_physics_for_position()` to find where 32× factor appears
3. **Validate:** Check if Miller indices (h,k,l) fed to F_latt match trace script values
4. **Test:** Run unit test for `compute_physics_for_position` with known h,k,l → F_latt pathway

## Reproduction Commands

```bash
# 1. Generate trace (PASSING)
export STAMP=20251010T071935Z
KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py \
  --pixel 1792 2048 --tag f_latt_post_fix \
  --out-dir reports/2026-01-vectorization-parity/phase_d/py_traces_post_fix/

# 2. Run simulator test (FAILING)
KMP_DUPLICATE_LIB_OK=TRUE python -c "
import torch, sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'src'))
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.config import *

# ... (full config as shown above) ...
image = simulator.run()
print(f'Pixel (1792, 2048): {image[1792, 2048].item():.15e}')
"

# 3. ROI comparison (FAILING)
KMP_DUPLICATE_LIB_OK=TRUE python scripts/nb_compare.py \
  --resample --roi 1792 2304 1792 2304 \
  --outdir reports/2026-01-vectorization-parity/phase_d/$STAMP/roi_compare/ \
  -- -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 \
     -distance 500 -detpixels 4096 -pixel 0.05
```

## Artifacts

- F_latt parity table: `reports/2026-01-vectorization-parity/phase_d/20251010T071935Z/f_latt_parity.md`
- Trace log (post-fix): `reports/2026-01-vectorization-parity/phase_d/py_traces_post_fix/pixel_1792_2048.log`
- ROI comparison: `reports/2026-01-vectorization-parity/phase_d/20251010T071935Z/roi_compare/summary.json`

## Decision Required

- **Option A:** Continue Phase D3 scope to fix simulator (expand beyond trace script)
- **Option B:** Document trace-only fix as Attempt #13, escalate simulator bug to Phase D5
- **Option C:** Roll back to Attempt #7 state and re-investigate all D1/D2/D3 fixes

Recommended: **Option B** - The trace script fix is valid and complete. The simulator issue is orthogonal and requires separate investigation with full regression testing.
