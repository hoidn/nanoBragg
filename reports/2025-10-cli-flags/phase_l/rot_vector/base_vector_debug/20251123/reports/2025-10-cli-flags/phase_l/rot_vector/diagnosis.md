# CLI-FLAGS-003 Phase L3k.3b: φ Rotation Parity Diagnosis

## L3k.3c.2 Update (2025-10-07 T12:17 UTC)

### Context
After implementing the reciprocal vector recomputation fix (Attempt #97), we executed Phase L3k.3b to regenerate C and PyTorch per-φ traces under the `base_vector_debug/20251123/` timestamp.

### VG-1 Delta Metrics

From `delta_metrics.json`:

```json
{
  "status": "ok",
  "phi0": {
    "py_k_frac": -0.589139352775903,
    "c_k_frac": -0.607255839576692,
    "delta_k": 0.018116486800789033
  },
  "phi9": {
    "py_k_frac": -0.607227388110849,
    "c_k_frac": -0.607255839576692,
    "delta_k": 2.8451465843071233e-05
  }
}
```

### Key Findings

1. **φ=0 Divergence**: Δk_frac = **1.8117×10⁻²** at φ_tic=0 (φ=0.0°)
   - PyTorch k_frac: -0.5891
   - C k_frac: -0.6073
   - Status: **DIVERGE** (exceeds tolerance by 36×)

2. **φ>0 Parity**: Δk_frac ≈ **2.8×10⁻⁵** for φ_tic=1…9
   - All φ steps from 0.01° to 0.1° show OK status
   - Within 5e-4 tolerance threshold

3. **Root Cause Hypothesis**: The rotation fix successfully aligns φ>0 steps but φ=0 still returns the base vector instead of carrying forward prior rotation state.

### C vs PyTorch Behavior

**C implementation** (from `c_trace_phi_20251123.log`):
- k_frac @ φ_tic=0: -0.6073 (matches φ_tic=9: -0.6073)
- Appears to preserve rotated state even at φ=0

**PyTorch implementation** (from `trace_py_rot_vector_20251123_per_phi.json`):
- k_frac @ φ_tic=0: -0.5891 (base vector)
- k_frac @ φ_tic=9: -0.6072 (correctly rotated)
- Resets to base vector when φ=0

### Remediation Path

Per input.md guidance, the φ==0 mismatch requires either:
1. A vectorized mask preserving the prior-state φ values when φ==0, or
2. An equivalent carryover mechanism matching C behavior

### Artifact Inventory

All artifacts stored under: `reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/`

- `c_trace_phi_20251123.log` — C TRACE_C_PHI output (10 phi steps)
- `trace_py_rot_vector_20251123.log` — PyTorch main trace
- `trace_py_rot_vector_20251123_per_phi.json` — PyTorch per-φ JSON
- `comparison_stdout_20251123.txt` — Comparison script output
- `delta_metrics.json` — VG-1 delta metrics
- `commands.txt` — Full command transcript with timestamps
- `sha256.txt` — SHA256 checksums for all artifacts

### Next Actions (Phase L3k.3c.3)

1. Implement φ==0 carryover fix in `Crystal.get_rotated_real_vectors`
2. Rerun per-φ harness and comparison script
3. Verify Δk ≤ 1e-6 for all φ steps including φ=0
4. Update `fix_checklist.md` VG-1.4 to ✅
5. Proceed to VG-3/VG-4 (nb-compare ROI parity)

### References

- C instrumentation: `golden_suite_generator/nanoBragg.c` TRACE_C_PHI lines
- PyTorch trace harness: `reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py`
- Comparison tool: `scripts/compare_per_phi_traces.py`
- Spec reference: `specs/spec-a-cli.md` §3.3 (φ rotation semantics)
- Implementation: `src/nanobrag_torch/models/crystal.py:1008-1035`
- Active plan: `plans/active/cli-noise-pix0/plan.md` Phase L3k.3c.2

---

**Status**: VG-1 evidence collected; diagnosis confirms φ=0 carryover as the lone remaining blocker before nb-compare rerun.

**Command hashes**: See `sha256.txt` for verification of all artifacts.

**Timestamp**: 2025-10-07 12:17:00 UTC
