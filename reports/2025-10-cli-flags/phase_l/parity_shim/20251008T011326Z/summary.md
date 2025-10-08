# Phase L3k.3c.4 Parity Shim Evidence (2025-10-08T01:13:26Z)

## Scope
- Re-ran `trace_harness.py` for supervisor configuration at pixel (685, 1039) with `phi_carryover_mode` set to `spec` and `c-parity`.
- Captured per-φ traces/JSON, targeted pytest logs, and SHA256 fingerprints under this directory.
- Reused the previously instrumented C trace (`c_trace_phi.log` from 20251008T005247Z) because the current golden binary no longer emits `TRACE_C_PHI` lines.

## Findings
- **Spec mode** remains spec-compliant: φ=0 drift persists (Δk = 1.8116e-02, ΔF_latt_b ≈ 1.91). Tests `TestPhiZeroParity` continue to pass (2/2).
- **C-parity mode** still diverges beyond the tightened VG-1 tolerance: max Δk = 2.8451e-05 (> 1e-6 target). ΔF_latt_b peaks at 4.36e-03; tolerances need to reach ≤1e-6 and ≤1e-4 respectively.
- Device coverage: CPU float64 only (CUDA cases skipped by existing tests); document in fix_plan that GPU evidence is still outstanding.
- Harness now threads `phi-mode` correctly; spec/c-parity pairs captured in `trace_py_*` outputs.

## Artifacts
- `trace_py_spec.log`, `trace_py_spec_per_phi.json`
- `trace_py_c_parity.log`, `trace_py_c_parity_per_phi.json`
- `c_trace_phi.log` (copied from 20251008T005247Z instrumentation run)
- `per_phi_summary_spec.txt`, `per_phi_summary_c_parity.txt`
- `comparison_summary_spec.md`, `comparison_summary_c_parity.md`
- `delta_metrics.json`
- `pytest_phi_carryover.log`, `pytest_phi0.log`
- `sha256.txt`

## Next Steps
1. Investigate why c-parity shim plateaus at Δk ≈ 2.84e-05 (suspect residual rounding in reciprocal recomputation).
2. Re-run the C trace with fresh instrumentation once `TRACE_C_PHI` logging is restored; update evidence when available.
3. Tighten shim logic/tests until VG-1 thresholds (≤1e-6) are met, then revisit Phase L3k.3c.5 documentation tasks.
