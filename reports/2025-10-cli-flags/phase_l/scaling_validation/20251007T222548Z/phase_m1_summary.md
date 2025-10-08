# Phase M1 Complete: Pre-Polar Trace Instrumentation

**Date:** 2025-10-07
**Item:** [CLI-FLAGS-003] Phase M1 (instrumentation alignment)
**Status:** ✅ Complete

## Objective

Align PyTorch `I_before_scaling` trace output with C-code reference by emitting the **pre-polarization** accumulated intensity, matching the point at which nanoBragg.c logs this value.

## Problem Statement

**Galph Debug Memo (2025-12-03):** PyTorch trace recorded `I_before_scaling` *after* polarization was applied inside `compute_physics_for_position`, whereas nanoBragg.c prints `I_before_scaling` **before** the `polar` factor is multiplied. This instrumentation misalignment resulted in an apparent −8.7% divergence that was actually a measurement artifact.

## Solution Implemented

### Code Changes

1. **`src/nanobrag_torch/simulator.py` (compute_physics_for_position)**:
   - Added `intensity_pre_polar = intensity.clone()` after phi/mosaic sum (line 326)
   - Return tuple `(intensity, intensity_pre_polar)` instead of single value (line 425)
   - Applied same multi-source accumulation to pre-polar tensor (lines 414-422)

2. **`src/nanobrag_torch/simulator.py` (run method)**:
   - Updated all 4 calls to `_compute_physics_for_position` to unpack tuple
   - Passed `I_before_normalization_pre_polar` to `_apply_debug_output` (line 1195)

3. **`src/nanobrag_torch/simulator.py` (_apply_debug_output)**:
   - Added `I_total_pre_polar` parameter (line 1214)
   - Emit both `I_before_scaling_pre_polar` and `I_before_scaling_post_polar` (lines 1409, 1417)

4. **`scripts/validation/compare_scaling_traces.py`**:
   - Map `I_before_scaling_pre_polar` → `I_before_scaling` for C comparison (lines 58-62)
   - Preserve both values in parsed dict for reference

### Trace Output

**Before (Post-Polar Only):**
```
TRACE_PY: I_before_scaling 861314.8125
```

**After (Both Values):**
```
TRACE_PY: I_before_scaling_pre_polar 941698.5
TRACE_PY: I_before_scaling_post_polar 861314.8125
```

## Results

### C vs PyTorch Comparison

| Value | C | PyTorch (Pre-Polar) | Δ (abs) | Δ (rel) | Status |
|-------|---|---------------------|---------|---------|--------|
| I_before_scaling | 943654.809 | 941698.5 | −1956.3 | −0.207% | Within expected tolerance |

### Analysis

1. **Instrumentation Alignment:** Pre-polar value (941698.5) is now the canonical comparison point
2. **Residual Δ ≈ −0.207%:** Matches galph debug memo expectation (float32 + F_latt drift < 0.3%)
3. **Post-Polar Sanity Check:**
   - C: 943654.809 × 0.914639699 (polar) = 863104.15
   - PyTorch post-polar: 861314.8125
   - Residual: −0.21% (consistent with pre-polar drift)

## Validation

- ✅ Test collection: `pytest --collect-only -q tests/test_cli_scaling_phi0.py` → 2 tests
- ✅ Trace harness: 44 TRACE_PY lines captured (2 new labels)
- ✅ Comparison script: Recognizes pre-polar as canonical I_before_scaling
- ✅ Per-φ trace: 10 TRACE_PY_PHI lines (unchanged)

## Artifacts

- Main trace: `reports/2025-10-cli-flags/phase_l/scaling_validation/20251007T222548Z/trace_py_scaling_cpu.log`
- Per-φ trace: `reports/2025-10-cli-flags/phase_l/per_phi/reports/2025-10-cli-flags/phase_l/scaling_validation/20251007T222548Z/trace_py_scaling_cpu_per_phi.log`
- Comparison: `reports/2025-10-cli-flags/phase_l/scaling_validation/20251007T222548Z/summary.md`
- Metrics: `reports/2025-10-cli-flags/phase_l/scaling_validation/20251007T222548Z/metrics.json`

## Next Actions (Phase M2)

Per galph debug memo and input.md:
1. The −0.2% residual is expected (float32 + F_latt effects)
2. Instrumentation now aligned with C reference
3. Phase M2 can proceed with structure-factor parity investigation using the corrected pre-polar baseline
4. Update `plans/active/cli-noise-pix0/plan.md` Phase M to mark M1 complete

## Git Provenance

- SHA: 5165754
- Branch: feature/spec-based-2
- Modified files:
  - `src/nanobrag_torch/simulator.py` (compute_physics_for_position, run, _apply_debug_output)
  - `scripts/validation/compare_scaling_traces.py` (parse_trace_file)
