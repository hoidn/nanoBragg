# Phase M5a Complete: Per-φ Trace Instrumentation

**Date:** 2025-10-09
**Engineer:** Ralph (loop #103)
**Plan Reference:** plans/active/cli-noise-pix0/plan.md Phase M5a
**Git SHA:** 05fd0e3

## Objective

Extend `trace_harness.py` and PyTorch trace hooks to emit `TRACE_PY_PHI` rows containing `k_frac`, `F_latt_b`, `F_latt` for every φ step, then rerun trace harness and comparison script.

## Execution Summary

### 1. Trace Harness Verification

The trace harness at `reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py` was already configured to capture per-φ traces. Verified that:

- Line 271-274: Captures `TRACE_PY_PHI` lines from stdout
- Line 287-333: Writes per-φ traces to separate files and JSON
- Simulator.py:1607-1611: Emits enhanced `TRACE_PY_PHI` with required fields

### 2. Trace Generation

**Command:**
```bash
env KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py \
  --config supervisor --pixel 685 1039 --device cpu --dtype float64 \
  --out reports/2025-10-cli-flags/phase_l/scaling_validation/per_phi/20251009T002636Z/trace_py_scaling.log
```

**Results:**
- ✅ Main trace: 114 TRACE_PY lines captured
- ✅ Per-φ trace: 10 TRACE_PY_PHI lines captured (one per φ step)
- ✅ Per-φ JSON: Structured data with k_frac, F_latt_b, F_latt values

### 3. Trace Comparison

**Command:**
```bash
python scripts/validation/compare_scaling_traces.py \
  --c reports/2025-10-cli-flags/phase_l/scaling_validation/per_phi/20251009T002636Z/c_trace_scaling.log \
  --py reports/2025-10-cli-flags/phase_l/scaling_validation/per_phi/20251009T002636Z/trace_py_scaling.log \
  --out reports/2025-10-cli-flags/phase_l/scaling_validation/per_phi/20251009T002636Z/summary.md
```

**Results:**
- First divergence: `I_before_scaling`
- C value: 943654.809
- PyTorch value: 805473.787
- Relative delta: -14.64%
- Status: **CRITICAL** (unchanged from prior runs)

### 4. Key Findings

#### Per-φ Trace Data (sample from φ_tic=0 to φ_tic=9)

| φ_tic | φ_deg | k_frac | F_latt_b | F_latt |
|-------|-------|--------|----------|--------|
| 0 | 0.000 | -0.589174 | -0.858428 | 1.379311 |
| 1 | 0.010 | -0.591185 | -0.650087 | 1.095812 |
| 2 | 0.020 | -0.593195 | -0.384052 | 0.677149 |
| 9 | 0.090 | -0.607263 | 1.050668 | -2.380125 |

#### Observations:
1. `k_frac` drifts from -0.589 to -0.607 over 0.09° rotation (consistent with prior analysis)
2. `F_latt_b` oscillates around zero-crossing (sign flip at φ≈0.04°)
3. `F_latt` shows corresponding sign flip due to `F_latt_b` factor
4. Scattering vector `S` remains constant (as expected for fixed pixel)
5. Reciprocal vectors (`a_star_y`, `b_star_y`, `c_star_y`) show small drift
6. Volume `V_actual` remains constant at 24682.2566 Å³

## Artifacts Generated

All files stored under: `reports/2025-10-cli-flags/phase_l/scaling_validation/per_phi/20251009T002636Z/`

- `trace_py_scaling.log` - Main PyTorch trace (114 lines)
- `trace_py_scaling_per_phi.log` - Per-φ trace (10 TRACE_PY_PHI lines) *
- `trace_py_scaling_per_phi.json` - Structured per-φ data *
- `c_trace_scaling.log` - C baseline trace (copied from 20251008T212459Z)
- `summary.md` - Comparison results
- `metrics.json` - Structured comparison metrics
- `run_metadata.json` - Run configuration
- `compare_scaling_traces.txt` - Comparison stdout
- `commands.txt` - Reproduction commands
- `env.json` - Environment metadata
- `sha256.txt` - File checksums
- `stdout.log` - Harness execution log

\* Note: Per-φ files written to nested path per harness line 289 path construction

## Next Actions (Phase M5b-M5e)

Per `plans/active/cli-noise-pix0/plan.md`:

### M5b: Rotation Parity Design Memo (STATUS: [D] per plan)
✅ Already complete - see `reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T232018Z/rotation_fix_design.md`

### M5c: Implement φ Rotation + Reciprocal Recompute Fix (STATUS: [ ])
**Owner:** Ralph (code change loop)
**Requirement:** Update `Crystal.get_rotated_real_vectors` to:
1. Recompute real and reciprocal vectors per φ tick
2. Use actual volume (Rule #13: `V_actual = a · (b × c)`)
3. Maintain vectorization (no Python loops)
4. Preserve device/dtype neutrality
5. Add CLAUDE Rule #11 C-code docstrings

### M5d: Verify Lattice Parity & Compare Traces (STATUS: [ ])
**Requirement:** After M5c implementation:
1. Regenerate PyTorch trace with same command
2. Rerun `compare_scaling_traces.py`
3. Confirm `first_divergence = None`
4. Update `lattice_hypotheses.md` to close H4/H5

### M5e: Targeted Regression & CUDA Smoke (STATUS: [ ])
**Requirement:** After M5d passes:
1. Run `pytest -v tests/test_cli_scaling_phi0.py` (CPU)
2. If available: `pytest -v -m gpu_smoke tests/test_cli_scaling_phi0.py` (CUDA)
3. Archive logs under same timestamp

## Conclusion

Phase M5a is **COMPLETE**. The per-φ trace instrumentation is functioning correctly and capturing all required fields (`k_frac`, `F_latt_b`, `F_latt`) for every φ step. The comparison script confirms the `I_before_scaling` divergence persists at -14.64%, which is expected before the rotation fix (M5c) is implemented.

The trace data provides clear evidence of the φ rotation drift issue (Hypothesis H4) - `k_frac` shifts by ~3% over 0.09° causing `F_latt_b` to cross zero and flip sign. This confirms the need for the reciprocal vector recomputation fix described in M5b design memo.

**Status:** Ready for M5c implementation (Ralph code-change loop)
