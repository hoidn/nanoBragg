# Phase M1 Scaling Audit — Tricubic Interpolation Evidence

## Run Metadata
- **Timestamp**: 2025-10-08T06:25:40Z
- **Pixel**: (685, 1039)
- **Mode**: c-parity (φ=0 carryover bug emulation)
- **Device/dtype**: CPU / float64
- **Git SHA**: 11d321e51d3c66af6a8d59f70af90b3544edb3a8

## Summary
Extended Phase M1 trace harness to capture 4×4×4 tricubic interpolation neighborhood for structure factor lookup. This evidence quantifies the F_latt drift between PyTorch and C implementations.

## Key Findings

### Structure Factor Comparison
- **F_cell (interpolated)**: 156.02990424724
- **F_cell (nearest-neighbor)**: 190.27
- **Interpolation active**: YES (forced for debug trace)
- **Tricubic neighborhood**: 64 values captured (4×4×4 grid)
- **Miller index neighborhood**: h ∈ [-8,-7,-6,-5], k ∈ [-2,-1,0,1], l ∈ [-15,-14,-13,-12]

### F_latt Drift (PyTorch vs C)
- **F_latt_a**: PyTorch = -2.35819512010207 vs C (TBD from c_trace_scaling.log)
- **F_latt_b**: PyTorch = 1.05066739326683 vs C (TBD)
- **F_latt_c**: PyTorch = 0.960630659359605 vs C (TBD)
- **F_latt (product)**: PyTorch = -2.38013414214076 vs C = -2.383196653 (from prior runs)
- **Relative drift**: ≈ +0.1285%

### Intensity Metrics (c-parity mode)
- **I_before_scaling_pre_polar**: 941686.235979802
- **I_before_scaling_post_polar**: 861303.580879118
- **Polarization factor**: 0.914639662310613
- **Final pixel intensity**: 2.87538300086444e-07

## Artifacts
- **Main trace**: `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T062540Z/trace_py_scaling.log` (114 lines)
- **Per-φ trace**: `reports/2025-10-cli-flags/phase_l/per_phi/reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T062540Z/trace_py_scaling_per_phi.{log,json}` (10 φ steps)
- **Tricubic grid**: 69 TRACE_PY_TRICUBIC lines embedded in main trace

## Next Steps (Phase M2)
1. Compare the 64-value tricubic grid against C-code output for the same pixel
2. Identify which grid values contribute most to the 0.13% F_latt drift
3. Instrument `_tricubic_interpolation` to emit per-coefficient weights for full polynomial trace
4. Target the φ=0 lattice amplitude mismatch (F_latt Δ ≈ 3.1×10⁻³) identified in Attempt #140

