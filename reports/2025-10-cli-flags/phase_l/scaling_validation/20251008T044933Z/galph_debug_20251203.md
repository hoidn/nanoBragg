# Debug Note — I_before_scaling Mismatch (galph 2025-12-03)

## Context
- Item: `[CLI-FLAGS-003] Phase M` (trace harness parity for supervisor command)
- Pixel: (slow=685, fast=1039)
- PyTorch trace: `trace_py_scaling_cpu.log`
- C trace: `reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log`
- Observation: `I_before_scaling` differs by −8.726% (PyTorch lower)

## Finding
- PyTorch trace records `I_before_scaling` *after* polarization is applied inside `compute_physics_for_position`, because `_apply_debug_output` taps `I_total` **after** `intensity = intensity * polar`.
- nanoBragg.c prints `TRACE_C: I_before_scaling` **before** the `polar` factor is multiplied.
- C value × polarization aligns with PyTorch:
  - C trace: `I_before_scaling = 943654.80923755`
  - C trace: `polar = 0.91463969894451`
  - Product: `943654.80923755 × 0.91463969894451 = 863104.1506`
  - PyTorch trace: `I_before_scaling = 861314.8125`
  - Residual delta (≈−0.2%) matches float32 rounding + small `F_latt` drift (<0.2%).

## Evidence
- PyTorch per-φ lattice factors (`reports/.../per_phi/.../trace_py_scaling_cpu_per_phi.log`) match C within ~1e-3 and yield Σ|F|² ≈ 9.42×10⁵ before polarization.
- Difference between C and PyTorch `I_before_scaling` equals C value × (1 − polar).

## Implication
- The "first divergence" flagged in Attempt #137 is an instrumentation misalignment, not a physics bug.
- Phase M1 should update the comparison script (or PyTorch trace) to emit the **pre-polarization** intensity so metrics align with C.
- Once traces are aligned, the true first divergence will likely move to the next factor (e.g., final intensity or residual rounding).

## Next Steps (for Phase M2)
1. Adjust `_apply_debug_output` (or trace harness) to log both:
   - `I_before_scaling_pre_polar`
   - `I_before_scaling_post_polar`
   ensuring the pre-polar value matches C.
2. Re-run `compare_scaling_traces.py` with the updated tap; expect the I_before delta to drop to ~0.2% (float32 effects).
3. Resume Phase M2 focus on structure-factor parity once instrumentation is synchronized.
