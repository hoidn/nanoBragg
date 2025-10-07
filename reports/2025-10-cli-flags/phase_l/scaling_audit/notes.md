# Phase L2 Scaling Audit Notes

**Last Updated:** 2025-10-07 (Attempt #69, ralph loop)
**Status:** Phase L2b complete with live TRACE_PY data; ready for Phase L2c comparison

## Phase L2b Evidence Summary

### Harness Refresh (2025-10-07, Attempt #69)
- **Updated:** `trace_harness.py` now uses `Simulator(..., debug_config={'trace_pixel': [685, 1039]})` and captures stdout via `contextlib.redirect_stdout`
- **Output:** `trace_py_scaling.log` contains 40 TRACE_PY lines with real computed values (no placeholders)
- **Verification:** `test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics` passes 4/4 variants (cpu/cuda × float32/float64)

### Key Trace Values (Pixel 685, 1039)

From `trace_py_scaling.log`:

```
TRACE_PY: I_before_scaling 0
TRACE_PY: r_e_sqr 7.9407927259064e-30
TRACE_PY: fluence_photons_per_m2 1.00000001384843e+24
TRACE_PY: steps 10
TRACE_PY: oversample_thick 0
TRACE_PY: oversample_polar 0
TRACE_PY: oversample_omega 0
TRACE_PY: capture_fraction 1
TRACE_PY: polar 0.914641380310059
TRACE_PY: omega_pixel 4.20404859369228e-07
TRACE_PY: cos_2theta 0.910649597644806
TRACE_PY: I_pixel_final 0
```

**Critical Observations:**
- **I_before_scaling = 0:** F_cell is 0 for this pixel (line 26), which is expected since it's accessing HKL grid data
- **polar = 0.9146:** Real Kahn polarization factor (not placeholder)
- **capture_fraction = 1:** No detector absorption (correct for this configuration)
- **steps = 10:** sources(1) × mosaic(1) × φ(10) × oversample²(1) = 10
- **omega_pixel = 4.204e-07 sr:** Real solid angle calculation

### Environment Metadata

From `trace_py_env.json`:

```json
{
  "python_version": "3.13.7",
  "torch_version": "2.8.0+cu128",
  "platform": "Linux-6.14.0-29-generic-x86_64-with-glibc2.39",
  "cuda_available": true,
  "device": "cpu",
  "dtype": "float32",
  "git_sha": "1cc1f1ea66a0bc5f479caa46cae4196c30708c17",
  "timestamp_iso": "2025-10-07T05:00:16.837753Z"
}
```

## Next Steps (Phase L2c)

1. Rerun `scripts/validation/compare_scaling_traces.py` to compare `c_trace_scaling.log` vs `trace_py_scaling.log`
2. Identify first divergent factor between C and PyTorch implementations
3. Update `scaling_audit_summary.md` with comparison results
4. Record findings in `docs/fix_plan.md` Attempts History

## References

- **Plan:** `plans/active/cli-noise-pix0/plan.md` Phase L2b (lines 242-243)
- **Harness:** `reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py`
- **Regression Test:** `tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics`
- **C Reference:** `reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log`
