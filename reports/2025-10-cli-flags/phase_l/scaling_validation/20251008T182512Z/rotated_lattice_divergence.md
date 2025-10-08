# Scaling Probe — Rotated Lattice vs F_latt divergence

* Pixel: (slow=1039, fast=685)
* Source traces: `reports/2025-10-cli-flags/phase_j/trace_py_scaling.log`, `trace_c_scaling.log`

## Key Observations
- Rotated lattice vectors (`rot_*_angstroms`) differ between PyTorch and C even at `phi_tic=0`. Y/Z components disagree by ~4e-2 Å, producing fractional Miller index offsets (Δh ≈ +0.102, Δk ≈ +0.024, Δl ≈ +0.110).
- Because the C trace lands extremely close to integer Miller values (|h-2| ≈ 0.0012), the C `sincg(π*h, Na)` response amplifies to O(1e1) per axis, yielding `F_latt ≈ 3.56e4`. PyTorch stays farther from the integer crossing, giving `F_latt ≈ 7.69e1`.
- The product mismatch (ratio ≈ 2.16e-3) explains the `I_before_scaling` divergence logged in `phase_j/scaling_chain.md`.

## Numeric Comparison
| Quantity | PyTorch | C | Δ (Py-C) | rel Δ |
| --- | --- | --- | --- | --- |
| rot_a_angstroms[0] | -1.435627e+01 | -1.435627e+01 | +0.000000e+00 | -0.000e+00 |
| rot_a_angstroms[1] | -2.187179e+01 | -2.188053e+01 | +8.741231e-03 | -3.995e-04 |
| rot_a_angstroms[2] | -5.582021e+00 | -5.547658e+00 | -3.436300e-02 | +6.194e-03 |
| rot_b_angstroms[0] | -1.149870e+01 | -1.149870e+01 | +0.000000e+00 | -0.000e+00 |
| rot_b_angstroms[1] | +7.173200e-01 | +6.715882e-01 | +4.573180e-02 | +6.809e-02 |
| rot_b_angstroms[2] | -2.911321e+01 | -2.911431e+01 | +1.090846e-03 | -3.747e-05 |
| rot_c_angstroms[0] | +2.106995e+01 | +2.106995e+01 | +0.000000e+00 | +0.000e+00 |
| rot_c_angstroms[1] | -2.438930e+01 | -2.440459e+01 | +1.528933e-02 | -6.265e-04 |
| rot_c_angstroms[2] | -9.752652e+00 | -9.714329e+00 | -3.832263e-02 | +3.945e-03 |
| hkl_frac[0] | +2.103340e+00 | +2.001203e+00 | +1.021371e-01 | +5.104e-02 |
| hkl_frac[1] | +2.016761e+00 | +1.992798e+00 | +2.396308e-02 | +1.202e-02 |
| hkl_frac[2] | -1.288044e+01 | -1.299077e+01 | +1.103262e-01 | -8.493e-03 |
| F_latt_a | -2.413936e+00 | +3.588906e+01 | -3.830300e+01 | -1.067e+00 |
| F_latt_b | +1.175013e+01 | +3.863249e+01 | -2.688237e+01 | -6.958e-01 |
| F_latt_c | -2.711565e+00 | +2.570248e+01 | -2.841405e+01 | -1.105e+00 |
| F_latt | +7.691098e+01 | +3.563608e+04 | -3.555917e+04 | -9.978e-01 |

PyTorch/C F_latt ratio = 2.158233e-03

## Hypothesis
- The PyTorch run for this trace was executed in spec mode (fresh φ rotations). The C trace, by definition, still carries the `φ=0` state from the prior pixel, so its first φ slice uses the rotated vectors from the previous φ tick. The parity shim (`--phi-carryover-mode c-parity`) must be enabled when collecting PyTorch traces for VG-2 to avoid this drift.
- Alternatively (if the shim was enabled), we need to confirm the cached rotated vectors (`Crystal._phi_carryover_cache`) are being seeded from the previous pixel before φ iteration starts. The current trace suggests the cache is not primed, leaving the spec-compliant fresh vectors in place.

## Proposed Next Steps
1. Re-run `scripts/trace_harness.py` with `--phi-carryover-mode c-parity` (or explicit unit test) to confirm whether PyTorch reproduces the C vectors when the shim is active.
2. If the mismatch persists with the shim, add logging around `Crystal._apply_phi_carryover()` (without breaking graph) to dump the cached `rot_*` vectors before φ looping. Compare to the previous pixel’s final φ vectors captured in the trace to ensure the cache wiring matches the design in `reports/2025-10-cli-flags/phase_l/parity_shim/20251201_dtype_probe/analysis_summary.md`.
3. Once the rotated vectors match, rerun Phase M2i.2 metrics to confirm `F_latt` parity and unblock VG-2.