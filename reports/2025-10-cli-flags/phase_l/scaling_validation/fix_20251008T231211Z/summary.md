# Phase M5a: Enhanced φ-Rotation Trace Capture

## Objective
Capture enhanced per-φ traces with rot_* fields before implementing φ rotation fix (Phase M5b-c).

## Execution
**Timestamp:** 2025-10-08T23:12:11Z  
**Command:** 
```bash
KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --pixel 685 1039 --device cpu --dtype float64 --emit-rot-stars --out reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T231211Z/trace_py_scaling.log
```

## Artifacts Captured
1. **Main scaling trace:** `trace_py_scaling.log` (124 lines)
   - Includes per-φ rot_* values via `TRACE_PY_ROTSTAR` lines
   - Final intensity: 2.45946637686509e-07
   
2. **Per-φ detail trace:** `trace_py_scaling_per_phi.log` (10 lines, one per φ step)
   - Each line captures: phi_tic, phi_deg, k_frac, F_latt_b, F_latt, S_x/y/z, a_star_y, b_star_y, c_star_y, V_actual
   - Key observation: b_star_y varies from 0.0104376 (φ=0°) to 0.010386 (φ=0.09°) - ~0.5% drift
   
3. **Per-φ JSON:** `trace_py_scaling_per_phi.json` (machine-readable version)

4. **Reproduction metadata:** `commands.txt`, `pytest_collect.log`

## Key Observations

### Rotation Drift Evidence
The per-φ trace shows systematic drift in reciprocal vector components:
- **b_star_y** drifts ~0.5% over 0.09° rotation (0.010438 → 0.010386)
- **k_frac** varies from -0.589 to -0.607 across phi steps
- **F_latt** shows sign flips and large magnitude swings (1.379 → -2.380)

This aligns with Hypothesis H4 (φ rotation mismatch) from `lattice_hypotheses.md` - the current PyTorch implementation applies φ rotation correctly per spec but diverges from the C code's carryover behavior at φ=0.

### Comparison with C Baseline
From Phase M1 spec_baseline (`20251008T212459Z`):
- **C reference:** k_frac ≈ -0.607, F_latt ≈ -2.383
- **PyTorch (this run):** k_frac ≈ -0.589 (φ=0), F_latt ≈ +1.379 (sign flip!)

The 3% shift in k_frac causes the sincg factor to cross zero (see M3b sincg sweep), flipping F_latt sign and creating the 14.6% I_before_scaling deficit.

## Status
✅ Phase M5a COMPLETE - Enhanced traces captured successfully  
➡️ Next: Phase M5b (rotation parity design memo) referencing these artifacts

## References
- Plan: `plans/active/cli-noise-pix0/plan.md` Phase M5
- Prior baseline: `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/`
- Hypothesis doc: `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md`
