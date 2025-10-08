# H4 Closure Addendum — 2025-10-08 Phase M4d

**Context:**
- Plan Phase M4d: Evidence capture after normalization fix (Attempts #188-#189, commit fe3a328)
- Previous status: H4 hypothesis elevated to HIGH CONFIDENCE (φ-rotation application inconsistency)
- Artifact bundle: `reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/`

## Status: PARTIALLY RESOLVED (Normalization Fix Applied, Upstream Issue Remains)

### Findings

**Normalization Fix Verification:**
- Code inspection confirmed single `/steps` division at `simulator.py:1127`
- Comments at lines 956 and 1041 explicitly state "Do NOT divide by steps here"
- Implementation correctly matches spec (specs/spec-a-core.md:247-250)

**Trace Comparison Results (2025-10-08):**
- PyTorch trace generated: 114 TRACE_PY lines captured successfully
- Comparison script executed against Phase M1 baseline (20251008T212459Z)
- **first_divergence:** I_before_scaling (STILL PRESENT)
- **Relative delta:** -14.6% (unchanged from Phase M2 analysis)

| Factor | Status | Notes |
|--------|--------|-------|
| I_before_scaling | 🔴 DIVERGENT | C: 943,654.81 vs PyTorch: 805,473.79 (-14.6%) |
| r_e_sqr | ✅ PASS | Exact match |
| fluence | ✅ PASS | Exact match |
| steps | ✅ PASS | Both = 10 |
| capture_fraction | ✅ PASS | Both = 1.0 |
| polar | ✅ PASS | δ_rel = -4.0e-08 |
| omega_pixel | ✅ PASS | δ_rel = -4.8e-07 |
| cos_2theta | ✅ PASS | δ_rel = -5.2e-08 |
| I_pixel_final | 🔴 DIVERGENT | Inherits I_before_scaling deficit (-14.6%) |

### Analysis

The normalization fix addressed the `/steps` division issue but did **NOT** eliminate the I_before_scaling divergence. This confirms:

1. **H4 remains the root cause:** The φ-rotation inconsistency affecting rot_b Y-component (+6.8%) propagates through k_frac (+3.0%) to F_latt (sign flip), ultimately causing the I_before_scaling deficit.

2. **Normalization was a red herring:** The -14.6% delta originated entirely from upstream physics (F_latt calculation), not from missing normalization steps. The fix was correct but addressed a different concern.

3. **All downstream factors pristine:** The perfect parity (≤1e-6) for all scaling factors confirms the issue is isolated to I_before_scaling accumulation, not final scaling.

### Revised Hypothesis Status

**H4 — φ-Rotation Application Inconsistency**
- **Status:** HIGH CONFIDENCE → **CONFIRMED PRIMARY CAUSE**
- **Evidence:** Normalization fix did not change divergence magnitude
- **Mechanism:** rot_b error → k_frac shift → F_latt sign flip → I_before_scaling deficit
- **Required Fix:** Address rotation matrix construction in `Crystal.get_rotated_real_vectors`

### Recommended Next Steps

The Phase M3 validation probes documented in the 2025-10-22 update remain the correct path forward:

1. **Per-φ instrumentation** (M3a complete, implementation deferred)
2. **Sincg sensitivity table** (M3b complete: zero-crossing at k≈-0.5955)
3. **Single-φ parity test** (M3c complete: identified 126,000× normalization error, now fixed)
4. **Rotation matrix audit** (M3d complete: confirmed rot_b +6.8% Y-component error)

**Actionable Item:** Investigate root cause of rot_b rotation error per M3d findings:
- Compare `src/nanobrag_torch/models/crystal.py::get_rotated_real_vectors` (lines 1084-1136) with `nanoBragg.c:2797-3095`
- Verify spindle axis orientation, rotation matrix order, and sign conventions
- Check per-φ metric duality enforcement (recalculate reciprocal vectors from actual volume)

### Documentation Updates

This finding should trigger:
1. Update `docs/fix_plan.md` Attempt #190 to note Phase M4d evidence complete, divergence persists
2. Keep CLI-FLAGS-003 status as BLOCKED pending rotation fix
3. Mark Phase M4d as [P] (partially complete - evidence captured, parity not achieved)
4. Phase M5 (CUDA validation) and M6 (ledger sync) remain deferred

### Artifacts Generated

- `trace_py_scaling.log` — Post-fix PyTorch trace (114 lines)
- `compare_scaling_traces.txt` — Detailed factor comparison
- `metrics.json` — Machine-readable results showing persistent divergence
- `run_metadata.json` — Execution metadata
- `blockers.md` — Detailed blocker documentation for supervisor escalation
- `diff_trace.md` — Comprehensive analysis summary
- `commands.txt` — Reproduction commands
- `sha256.txt` — Artifact manifest
- `lattice_hypotheses_h4_closure.md` — This document

### Supervisor Escalation

**Question for supervisor:**
Given that the normalization fix is correct but I_before_scaling divergence persists, should:
1. A fresh C baseline trace be generated with verified parameters?
2. Phase M4 be considered blocked pending rotation matrix fix?
3. The rotation fix be prioritized before continuing M4d closure?

The evidence bundle is complete for documentation purposes, but the parity gate (first_divergence = None) remains unmet.

---
Document appended: 2025-10-08 (Ralph loop i=190, CLI-FLAGS-003 Phase M4d)
