# Phase M2 Analysis Summary Addendum

**Date:** 2025-10-22
**Bundle:** `20251008T212459Z/spec_baseline/`
**Phase:** CLI-FLAGS-003 Phase M2 (Docs-mode divergence analysis)

## Quick Reference

This bundle contains the **comprehensive Phase M2 divergence analysis** following the fresh spec-mode baseline capture (Phase M1).

### Key Deliverables

1. **`analysis_20251008T212459Z.md`** — Complete quantitative breakdown of the 14.6% I_before_scaling divergence
   - F_cell parity: ✅ CONFIRMED (190.27 exact match)
   - F_latt divergence: 🔴 CRITICAL (sign flip: C=-2.383, PyTorch=+1.379)
   - Root cause: φ-rotation application inconsistency (rot_b Y-component +6.8% error)
   - Ranked hypotheses (H4-H8) with validation probes for Phase M3

2. **`../20251008T075949Z/lattice_hypotheses.md`** — Updated with 20251008T212459Z findings section
   - H4 (φ-Rotation Inconsistency) elevated to HIGH CONFIDENCE, P0 priority
   - Comparison table showing per-factor deltas at φ=0
   - Next actions mapped to Phase M3 validation probes

3. **`scaling_validation_summary.md`** (parent directory) — Regenerated with fresh metrics
   - First divergence: I_before_scaling (-14.6%)
   - 2 divergent factors identified
   - All downstream factors (r_e², fluence, steps, etc.) remain ≤1e-6 relative

### Artifact Integrity

- **SHA-256 checksums:** All files validated via `sha256.txt`
- **Git SHA:** (to be appended post-commit)
- **Environment:** CPU, dtype=float64, Python 3.13.7, PyTorch 2.8.0
- **Test collection:** 2 tests in test_cli_scaling_phi0.py (passing collection)

### Phase M3 Gate

Before physics implementation (Phase M4), the following validation probes must be delivered:

1. Per-φ PyTorch trace with TRACE_PY_PHI format
2. Manual sincg sensitivity table for k ∈ [-0.61, -0.58]
3. Single-φ parity test (phisteps=1, phi=0)
4. Rotation matrix construction audit (PyTorch vs nanoBragg.c:2797-3095)

All Phase M3 artifacts to be stored under:
`reports/2025-10-cli-flags/phase_l/scaling_validation/<date>/phase_m3_probes/`

### Historical Context

- **Phase M0:** Trace instrumentation cleanup (device/dtype neutrality)
- **Phase M1:** Fresh spec-mode baseline after φ-carryover shim removal (Phase D)
- **Phase M2:** This analysis (divergence partitioning and hypothesis ranking)
- **Phase M3:** Validation probes (next step)
- **Phase M4:** Physics fix implementation (blocked on M3)

### Conclusion

The divergence is **not** in structure factors (F_cell), interpolation, or downstream scaling factors. The issue is isolated to **φ-rotation application** causing a 6.8% rot_b Y-component error, which propagates to k_frac (+3% shift) and triggers a sincg sign flip in F_latt_b. This sign flip cascades to the final F_latt product and explains the entire 14.6% I_before_scaling deficit.

**Recommended reading order:**
1. This addendum (overview)
2. `analysis_20251008T212459Z.md` (detailed breakdown)
3. `../20251008T075949Z/lattice_hypotheses.md` (historical context + new H4 hypothesis)

---

*Document authored: 2025-10-22 by Ralph (CLI-FLAGS-003 Phase M2 Docs loop)*
