# Phase E9 Summary: C Tap 5 Instrumentation

**Date:** 2025-10-10T11:23:34Z
**Focus:** [VECTOR-PARITY-001] Phase E9 — C Tap 5 capture for intensity pre-normalization parity

## Deliverables

1. **C Instrumentation:** Added `TRACE_C_TAP5` guard to `golden_suite_generator/nanoBragg.c` lines 3397-3410, capturing:
   - `I_before_scaling` (accumulated intensity before r_e²·fluence/steps)
   - `steps` (total sampling count = oversample²)
   - `omega_pixel` (solid angle in steradians)
   - `capture_fraction` (detector absorption factor)
   - `polar` (polarization factor)
   - `I_pixel_final` (after final scaling)

2. **Traces Captured:** 
   - Edge pixel (0,0): `pixel_0_0_tap5.log` — I_before_scaling=1.415202e+05, omega=8.861e-09 sr, polar=0.961277
   - Center pixel (2048,2048): `pixel_2048_2048_tap5.log` — I_before_scaling=0.0 (no Bragg contribution), omega=1.000e-08 sr, polar=1.000000

3. **Metadata:** Environment captured in `env/trace_env.json` (git SHA, compiler, CFLAGS, Python version, system info)

4. **Summary:** `comparison/intensity_pre_norm_c_notes.md` — key metrics extracted, ratios computed, hypothesis documented

## Key Findings

- **Edge vs Center Ratios:** ω_center/ω_edge ≈ 1.129, polar_center/polar_edge ≈ 1.040 (matches PyTorch Attempt #29)
- **Intensity Discrepancy:** Edge pixel shows ~4× intensity difference (C: 1.415e5, PyTorch Attempt #29: 3.54e4)
- **Center Pixel Consistency:** Both implementations report zero intensity (F_cell=0 at beam center for this configuration)

## Next Steps (from input.md Next Actions #2)

Compare C Tap 5 metrics with PyTorch Attempt #29 in `comparison/intensity_pre_norm.md`:
1. Quantify the I_before_scaling discrepancy (~4× at edge pixel)
2. Investigate F_cell² and F_latt² per-subpixel contributions
3. Decide whether to escalate to Tap 6 (water background) or proceed to Phase F remediation

## Artifacts

All artifacts stored under `reports/2026-01-vectorization-parity/phase_e0/20251010T112334Z/`:
- `c_taps/pixel_0_0_tap5.log` (edge trace)
- `c_taps/pixel_2048_2048_tap5.log` (center trace)
- `c_taps/commands.txt` (reproduction commands)
- `comparison/intensity_pre_norm_c_notes.md` (summary)
- `comparison/pytest_collect.log` (sanity check, 692 tests collected)
- `env/trace_env.json` (environment metadata)

## Exit Criteria Status

✅ C binary rebuilt with Tap 5 instrumentation  
✅ Traces captured for pixels (0,0) and (2048,2048) at oversample=2  
✅ Metrics extracted and summarized  
✅ Environment metadata recorded  
✅ Pytest collection verified (692 tests, no import errors)

**Status:** COMPLETE — Ready for Next Action #2 (Tap 5 comparison)
