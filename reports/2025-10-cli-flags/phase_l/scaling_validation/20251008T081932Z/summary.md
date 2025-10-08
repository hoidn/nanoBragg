# Phase M2 Lattice Evidence Collection - Enhanced Rotated Vector Traces

**Date:** 2025-10-08
**Engineer:** Ralph (loop i=150)
**Mode:** Evidence-only (instrumentation + trace capture)
**Git SHA:** 4a4eff58634937b43a75ca973f58cf0a1d171e58

## Objective
Capture per-φ real-space vectors (ap, bp, cp) alongside existing reciprocal vectors to diagnose F_latt drift (~0.13% between C and PyTorch).

## Implementation
### New Trace Infrastructure
1. **Trace Harness Enhancement**
   - Added `--emit-rot-stars` flag to `trace_harness.py`
   - Flag passed via `debug_config['emit_rot_stars']` to simulator

2. **Simulator Trace Tap**
   - Added `TRACE_PY_ROTSTAR` emission in `simulator.py:1597-1601`
   - Emits `ap_y`, `bp_y`, `cp_y` per φ tick when flag is set
   - Non-intrusive: gated by debug_config, defaults off

### Trace Capture Results
**Main Trace:** `trace_py_scaling.log` (124 lines)
- Standard TRACE_PY lines for pixel 685,1039
- **10 NEW TRACE_PY_ROTSTAR lines** with real-space vectors per φ

**Per-Phi Trace:** `per_phi/.../trace_py_scaling_per_phi.log` (10 lines)
- Existing TRACE_PY_PHI lines (filtered by harness)
- Contains reciprocal vectors, V_actual, F_latt per φ

## Key Data Captured
### TRACE_PY_ROTSTAR Format
```
TRACE_PY_ROTSTAR phi_tic=N ap_y=<val> bp_y=<val> cp_y=<val>
```

### Sample Output (phi_tic=0):
```
TRACE_PY_ROTSTAR phi_tic=0 ap_y=-21.8805340763623 bp_y=0.671588233999813 cp_y=-24.4045855811067
TRACE_PY_PHI phi_tic=0 phi_deg=0 k_frac=-0.607262620986129 F_latt_b=1.05066739326683 F_latt=-2.38013414214076 ...
  a_star_y=-0.0293789623945766 b_star_y=0.0103860193252683 c_star_y=-0.0143496591104365 V_actual=24682.2566301114
```

## Artifacts
- `trace_py_scaling.log` — Main trace (with ROTSTAR lines)
- `per_phi/.../trace_py_scaling_per_phi.log` — Per-φ reciprocal vectors
- `trace_harness.log` — Execution log
- `commands.txt` — Reproduction commands
- `git_sha.txt` — Git commit
- `sha256.txt` — Artifact checksums

## Next Actions
Per input.md:
1. Compare TRACE_PY_ROTSTAR ap/bp/cp against C TRACE_C_PHI equivalents
2. Run float64-only harness to isolate precision effects
3. Use evidence to target Phase M2 implementation fix

## References
- `plans/active/cli-noise-pix0/plan.md:81` — M2c hypothesis log complete
- `docs/fix_plan.md:656` — Instrumentation directive
- `input.md:7-38` — Do Now specification
