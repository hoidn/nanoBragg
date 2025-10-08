# Phase M1 Manual Scaling Comparison

- Timestamp: 2025-10-08T06:09:38.540491+00:00
- C trace: reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log
- PyTorch trace: reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T060721Z/trace_py_scaling.log

## Table

| Key | Description | C Value | PyTorch Value | Δ (abs) | Δ (rel) | Status |
| --- | --- | --- | --- | --- | --- | --- |
| hkl_frac | Fractional HKL (h component shown) | -6.8795206 | -6.87953496 | -1.43601468e-05 | 2.08737608e-06 | delta |
| F_latt_a | Lattice factor along a | -2.36012736 | -2.35819512 | 0.00193223985 | -0.000818701518 | delta |
| F_latt_b | Lattice factor along b | 1.05079664 | 1.05066739 | -0.000129249756 | -0.000123001684 | delta |
| F_latt_c | Lattice factor along c | 0.960961004 | 0.960630659 | -0.000330344252 | -0.000343764472 | delta |
| F_latt | Composite lattice factor | -2.38319665 | -2.38013414 | 0.00306251085 | -0.00128504328 | delta |
| F_cell | Structure factor amplitude | 190.27 | 190.27 | 0.000000e+00 | 0.000000e+00 | OK |
| I_before_scaling | Accumulated intensity before scaling (C pre-polar vs Py pre-polar) | 943654.809 | 941686.236 | -1968.57326 | -0.00208611585 | delta |
| polar | Polarization factor | 0.914639699 | 0.914639662 | -3.663390e-08 | -4.005282e-08 | OK |
| omega_pixel_sr | Solid angle (steradians) | 4.204127e-07 | 4.204125e-07 | -2.026682e-13 | -4.820695e-07 | OK |
| capture_fraction | Detector capture fraction | 1 | 1 | 0.000000e+00 | 0.000000e+00 | OK |
| steps | Normalization divisor | 10 | 10 | 0.000000e+00 | 0.000000e+00 | OK |
| fluence_photons_per_m2 | Incident fluence | 1.000000e+24 | 1.000000e+24 | 0.000000e+00 | 0.000000e+00 | OK |

## Notes
- Relative deltas larger than 1e-6 are flagged as `delta`.
- PyTorch `I_before_scaling` column uses the pre-polar value for parity with C trace.
- Differences persist around the lattice factors, yielding ~0.21% drop in `I_before_scaling`.