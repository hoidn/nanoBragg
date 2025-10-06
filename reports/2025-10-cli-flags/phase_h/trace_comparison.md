# Phase H1 Trace Comparison

## Summary
PyTorch trace captured without manual `simulator.incident_beam_direction` override. The Detector received `custom_beam_vector` via DetectorConfig, but the simulator is NOT using it.

## First Divergence: Incident Beam Direction

**Line:** incident_vec
**C value:** `[0.000513879494092498, 0.0, -0.999999867963924]`
**PyTorch value:** `[1, 0, 0]`

### Root Cause
The simulator is using the default MOSFLM incident beam direction `[1, 0, 0]` instead of the custom beam vector from the CLI.

The flow is broken:
1. ✅ CLI provides `beam_vector = [0.00051387949, 0.0, -0.99999986]`
2. ✅ Harness passes it to `DetectorConfig.custom_beam_vector`
3. ❌ Detector does NOT propagate this to simulator's `incident_beam_direction`
4. ❌ Simulator uses default convention beam direction instead

## Cascading Effects

Once the incident_vec diverges, everything downstream is wrong:

### Scattering Vector
- **C:** `-4016134701.82 1483170371.50 935911580.51` Å⁻¹
- **PyTorch:** `-14246065965.97 1438565713.12 -9309598569.43` Å⁻¹
- Δ: Complete mismatch due to wrong incident direction

### Miller Indices (fractional)
- **C:** `h=2.001, k=1.993, l=-12.991`
- **PyTorch:** `h=22.502, k=43.588, l=-24.446`
- Δ: Completely different reflection due to scattering vector error

### Miller Indices (rounded)
- **C:** `(2, 2, -13)`
- **PyTorch:** `(23, 44, -24)`
- Δ: Different HKL means different structure factor lookup

### Structure Factor (F_latt)
- **C:** `35636.08` (strong reflection)
- **PyTorch:** `0.0601` (essentially zero - wrong reflection)
- Δ: Factor of ~5.9×10⁵ difference!

### Final Intensity
- **C:** `446.25` photons
- **PyTorch:** `0.0` photons
- Δ: Complete signal loss

## Detector Geometry (matches within tolerance)
- pix0_vector: ~0.14 mm difference (expected from prior phases)
- Pixel position: Close match once pix0 difference accounted for
- omega_pixel: 4.159e-07 (C) vs 4.169e-07 (PyTorch) - negligible
- Detector basis vectors: Match within precision

## Config Verification
- **distance:** 231.275 mm (both)
- **oversample:** 1 (both)
- **pivot:** BEAM (both - `-distance` was specified)
- **phi/osc/phisteps:** 0.0°, 0.1°, 10 steps (both)
- **wavelength:** 0.9768 Å (both)

## Next Actions (Phase H2)
1. Investigate where `custom_beam_vector` should be consumed by Detector
2. Verify how Simulator should receive incident beam direction for CUSTOM convention
3. Check if `Detector.apply_custom_vectors()` is supposed to set incident beam
4. Fix the beam vector flow: DetectorConfig → Detector → Simulator
5. Re-run Phase H1 trace after fix to validate beam vector parity
