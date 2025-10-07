# Per-φ Lattice Trace Comparison Summary

**Date**: 2025-10-07
**Engineer**: Ralph (Loop i=85)
**Task**: CLI-FLAGS-003 Phase L3e — Per-φ lattice traces to localize F_latt drift
**Plan Reference**: `plans/active/cli-noise-pix0/plan.md` Phase L3e

## Objective

Capture per-φ `TRACE_PY_PHI` lattice entries from the PyTorch simulator to enable comparison with C reference traces and isolate the F_latt sign mismatch blocking CLI parity.

## Instrumentation

### Simulator Changes

**File**: `src/nanobrag_torch/simulator.py` (lines 1424-1460)

Added per-φ tracing block that:
- Loops over all φ steps (10 steps for supervisor command)
- Computes Miller indices (h, k, l) for each φ orientation
- Calculates F_latt components using sincg lattice shape factor
- Emits `TRACE_PY_PHI` entries matching C trace format

**Key Design Decisions**:
- Reuses existing rotated lattice vectors (`rot_a`, `rot_b`, `rot_c`) computed by `Crystal.get_rotated_real_vectors`
- Uses first mosaic domain `[phi_tic, 0]` per C reference behavior
- Preserves scattering vector from main trace (independent of φ)
- Applies SQUARE lattice model via `sincg(π·k, Nb)` per specs/spec-a-core.md

### Harness Updates

**File**: `reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py` (lines 260-333)

Extended trace capture to:
- Separate `TRACE_PY_PHI` lines from main `TRACE_PY` output
- Write per-φ traces to `reports/2025-10-cli-flags/phase_l/per_phi/trace_py_per_phi_<date>.log`
- Generate structured JSON (`per_phi_py_<date>.json`) for comparison tooling
- Preserve main scaling trace in original location

## Artifacts Generated

### PyTorch Per-φ Trace

**Path**: `reports/2025-10-cli-flags/phase_l/per_phi/trace_py_per_phi_20251007.log`

```
TRACE_PY_PHI phi_tic=0 phi_deg=0 k_frac=-0.589139352775903 F_latt_b=-0.861431104849688 F_latt=1.3517866940893
TRACE_PY_PHI phi_tic=1 phi_deg=0.0111111111111111 k_frac=-0.591149425118623 F_latt_b=-0.654273473439334 F_latt=1.07893592692855
... (10 entries total)
```

**Metrics**:
- 10 φ steps captured (φ=0.0° to φ=0.1°)
- k_frac range: -0.589 to -0.607
- F_latt_b range: -0.861 to +1.051
- F_latt range: -2.352 to +1.352

### Structured JSON

**Path**: `reports/2025-10-cli-flags/phase_l/per_phi/per_phi_py_20251007.json`

Contains timestamped metadata plus per-φ entries with:
- `phi_tic`: Integer step number
- `phi_deg`: Angle in degrees (float64 precision)
- `k_frac`: Fractional Miller index k
- `F_latt_b`: Lattice shape factor for b-axis
- `F_latt`: Total lattice factor (F_latt_a × F_latt_b × F_latt_c)

## Test Validation

**Command**: `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics -q`

**Result**: ✅ 4/4 passed (7.67s)

- Verified cpu/cuda × float32/float64 parametrizations
- Confirms per-φ instrumentation preserves existing trace behavior
- No regressions in scaling trace capture

## Comparison with C Reference

The C reference trace from Phase K3e is available at:
`reports/2025-10-cli-flags/phase_k/f_latt_fix/per_phi/per_phi_c_20251006-151228.log`

**Key Observations**:

1. **φ Sampling**: Both implementations use 10 φ steps over 0.1° range
2. **k_frac Divergence**: PyTorch k_frac ≈ -0.59 vs C k_frac ≈ -3.86 (Δk ≈ 3.27)
3. **F_latt_b Sign**: PyTorch shows oscillating signs, C shows similar pattern
4. **Next Action**: The k_frac offset persists from Phase K3e, confirming base lattice mismatch

## Next Steps (Per Do Now)

Per `input.md` guidance:

1. ✅ **Completed**: Extended simulator to emit `TRACE_PY_PHI` per-φ lattice entries
2. ✅ **Completed**: Updated harness to capture and save per-φ traces
3. ✅ **Completed**: Generated structured JSON for comparison tooling
4. ✅ **Completed**: Verified test suite passes after instrumentation
5. **Next**: Run comparison script to generate delta summary:
   ```bash
   python scripts/compare_per_phi_traces.py \
     reports/2025-10-cli-flags/phase_l/per_phi/per_phi_py_20251007.json \
     reports/2025-10-cli-flags/phase_k/f_latt_fix/per_phi/per_phi_c_20251006-151228.log \
     > reports/2025-10-cli-flags/phase_l/per_phi/comparison_summary_20251119.md
   ```

## Environment

- Git SHA: 8e92b48
- Python: 3.13.0
- PyTorch: 2.8.0+cu128
- Device: CPU (float64 for trace)
- Platform: Linux 6.14.0-29-generic

## References

- **Plan**: `plans/active/cli-noise-pix0/plan.md` Phase L3e
- **Spec**: `specs/spec-a-core.md` §4.3 (SQUARE lattice factor)
- **C Reference**: `golden_suite_generator/nanoBragg.c` lines 3071-3079 (sincg calls)
- **Previous Phase**: Phase K3e per-φ parity (reports/2025-10-cli-flags/phase_k/f_latt_fix/per_phi/)
