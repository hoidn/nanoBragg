# Fluence Parity Verification (Phase D2)

## Context
- Initiative: `[VECTOR-PARITY-001]` Phase D2 — Fix fluence scaling in PyTorch trace pipeline
- Pixel: (1792, 2048) — First row outside ROI, on-peak pixel
- Configuration: 4096² detector, λ=0.5 Å, pixel=0.05 mm, distance=500 mm, MOSFLM convention, oversample=1
- Timestamp: 2025-10-10T07:03:07Z

## Root Cause Analysis

### Problem
Prior to this fix, the PyTorch trace helper (`scripts/debug_pixel_trace.py:378-382`) was **recomputing fluence** from `flux`, `exposure`, and `beamsize`:

```python
# BEFORE (buggy)
flux = beam_config.flux
exposure = beam_config.exposure
beamsize_m = beam_config.beamsize_mm / 1000.0
fluence = flux * exposure / (beamsize_m * beamsize_m)
```

This created a ~10⁹× mismatch (C=1.259e+29 vs Py=1.273e+20) because the trace helper was using default flux values instead of the spec-compliant fluence already calculated in `BeamConfig.__post_init__`.

### Solution
Changed the trace helper to **directly read** the pre-computed fluence from `BeamConfig`:

```python
# AFTER (correct)
fluence = beam_config.fluence
```

This ensures the trace faithfully reflects the simulator's actual fluence value, which is computed per `spec-a-core.md:517`:
> "If -flux, -exposure, and -beamsize are provided, fluence SHALL be set to flux·exposure / beamsize²."

The BeamConfig class (`src/nanobrag_torch/config.py:535-545`) correctly implements this formula, handling edge cases like zero flux, zero beamsize, and sample clipping.

## Parity Metrics

| Metric | C Value | PyTorch Value | Relative Error | Threshold | Status |
|--------|---------|---------------|----------------|-----------|--------|
| fluence_photons_per_m² | 1.25932015286227e+29 | 1.259320152862271e+29 | 7.941e-16 | ≤1e-3 | ✅ PASS |

**Relative error formula:** `|C - Py| / C`

## Evidence Artifacts

### Traces
- **C trace:** `reports/2026-01-vectorization-parity/phase_c/20251010T053711Z/c_traces/pixel_1792_2048.log`
  ```
  TRACE_C: fluence_photons_per_m2 1.25932015286227e+29
  ```

- **PyTorch trace (post-fix):** `reports/2026-01-vectorization-parity/phase_d/20251010T070307Z/py_traces_post_fix/pixel_1792_2048.log`
  ```
  TRACE_PY: fluence_photons_per_m2 1.259320152862271e+29
  ```

### Commands
```bash
# Generate post-fix PyTorch trace
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py \
  --pixel 1792 2048 \
  --tag fluence_post_fix \
  --out-dir reports/2026-01-vectorization-parity/phase_d/$STAMP/py_traces_post_fix/

# Extract and compare fluence values
grep "fluence_photons_per_m2" \
  reports/2026-01-vectorization-parity/phase_c/20251010T053711Z/c_traces/pixel_1792_2048.log \
  reports/2026-01-vectorization-parity/phase_d/20251010T070307Z/py_traces_post_fix/pixel_1792_2048.log
```

## Verification

### Code Changes
- **File:** `scripts/debug_pixel_trace.py:377-381`
- **Diff:**
  ```diff
  -    # Fluence calculation per spec-a-core.md line 517:
  -    # fluence = flux * exposure / beamsize²  (square beam, not circular)
  -    flux = beam_config.flux
  -    exposure = beam_config.exposure
  -    beamsize_m = beam_config.beamsize_mm / 1000.0
  -    fluence = flux * exposure / (beamsize_m * beamsize_m)
  +    # Fluence from BeamConfig (already computed per spec-a-core.md line 517)
  +    # Do NOT recompute; BeamConfig.__post_init__ applies the spec formula
  +    # and handles edge cases (flux=0, beamsize clipping, etc.)
  +    fluence = beam_config.fluence
  ```

### Spec Compliance
- **Spec reference:** `specs/spec-a-core.md:517`
- **Implementation:** `src/nanobrag_torch/config.py:535-545` (BeamConfig.__post_init__)
- **C reference:** `golden_suite_generator/nanoBragg.c:1148-1167`

All three sources align: fluence = flux·exposure / beamsize², with BeamConfig correctly implementing the formula and edge cases.

## Impact Assessment

### Fixed
✅ Fluence trace parity (7.941e-16 relative error, ~machine precision)
✅ Trace helper now faithfully reflects simulator state
✅ Removed parallel "trace-only" implementation drift

### Preserved
✅ Scattering vector parity (Phase D1: rel_err ≤1e-12)
✅ Geometric parity (detector/crystal vectors: ≤10⁻¹² tolerance)
✅ Device/dtype neutrality in trace script

## Next Steps (Phase D3)

Per `plans/active/vectorization-parity-regression.md:61-65`, the next blocking issue is:

**H3:** F_latt normalization (~100× error)
- **Target:** Align `utils/physics.py::sincg` with `nanoBragg.c` (lines ~15000-16000)
- **Metric:** F_latt parity within ≤1e-2 relative error
- **Deliverable:** `reports/2026-01-vectorization-parity/phase_d/<STAMP>/f_latt_parity.md`

## References

- **Plan:** `plans/active/vectorization-parity-regression.md` Phase D2
- **Spec:** `specs/spec-a-core.md:517` (fluence formula)
- **Architecture:** `arch.md §8` (fluence scaling)
- **Config contract:** `docs/development/c_to_pytorch_config_map.md`
- **Gap analysis:** `reports/2026-01-vectorization-parity/phase_d/fluence_gap_analysis.md`
- **Debugging SOP:** `docs/debugging/debugging.md` (trace-driven debugging)
- **C implementation:** `golden_suite_generator/nanoBragg.c:1148-1167`

## Sign-Off

**Phase D2 Exit Criteria:**
- [x] PyTorch trace emits `beam_config.fluence` (not re-derived from flux)
- [x] Fluence parity ≤1e-3 relative error achieved (actual: 7.941e-16)
- [x] Trace artifacts archived under timestamped directory
- [x] Parity memo (`fluence_parity.md`) created with metrics and commands

**Status:** ✅ COMPLETE
**Engineer:** ralph
**Date:** 2025-10-10
**Next:** Phase D3 (F_latt normalization fix)
