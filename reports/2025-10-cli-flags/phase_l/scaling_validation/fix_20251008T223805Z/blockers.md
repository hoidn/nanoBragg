# Phase M4d Blocker

**Date:** 2025-10-08
**Context:** CLI-FLAGS-003 Phase M4d evidence capture
**Git SHA:** b2d2f64

## Issue

The `compare_scaling_traces.py` script reports a persistent divergence:
- **first_divergence:** `I_before_scaling`
- **C value:** 943654.809
- **PyTorch value:** 805473.787
- **Relative delta:** -14.6% (CRITICAL)

## Investigation

1. Verified that the normalization fix IS present in the code:
   - `src/nanobrag_torch/simulator.py:1127` has `/ steps` division
   - Comments at lines 956 and 1041 confirm NO early divisions
   - Only ONE normalization division occurs at line 1127

2. Checked git history:
   - Current HEAD: b2d2f64 (SYNC marker)
   - Fix commit: fe3a328 (referenced in attempts #188-#189)
   - Code inspection confirms single `/steps` division

3. Trace generation succeeded:
   - `trace_py_scaling.log` created successfully
   - 114 TRACE_PY lines captured
   - Final intensity: 2.45946637686509e-07

## Hypothesis

The divergence persists because:
1. Either the C trace baseline needs regeneration with updated parameters, OR
2. There's a remaining physics mismatch in `I_before_scaling` calculation upstream of normalization

The -14.6% delta is exactly the same as in the original baseline, suggesting the comparison is against stale C reference data or there's an upstream calculation issue not addressed by the normalization fix alone.

## Next Actions (Escalate to Supervisor)

1. Verify whether the C baseline trace at `20251008T212459Z/spec_baseline/c_trace_scaling.log` was generated with the correct command matching the supervisor ROI
2. Consider regenerating BOTH C and PyTorch traces in a fresh directory to ensure clean comparison
3. If traces remain divergent after regeneration, investigate upstream `I_before_scaling` calculation path (F_cell, F_latt, accumulation loop)

## Failed Command

```bash
python scripts/validation/compare_scaling_traces.py \
  --c reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/c_trace_scaling.log \
  --py reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/trace_py_scaling.log \
  --out reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/compare_scaling_traces.txt
```

**stderr:** None
**exit code:** 0 (script completed but reported divergence)

## Artifacts

- `reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/trace_py_scaling.log`
- `reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/metrics.json`
- `reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/compare_scaling_traces.txt`
- `reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/run_metadata.json`
