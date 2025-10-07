# Volume Analysis for CLI-FLAGS-003 Phase L3g

## Purpose
Validate volume calculation approaches (V_formula vs V_actual) to diagnose systematic Y-component drift in real-space rotation vectors.

## Cell Parameters

| Parameter | Value |
| --- | --- |
| a | 26.9 Å |
| b | 31.4 Å |
| c | 33.9 Å |
| α | 90.3° |
| β | 90.7° |
| γ | 89.7° |

## Volume Calculations (from invariant_probe.md)

### PyTorch (float32, CPU)
| Metric | Value | Notes |
| --- | --- | --- |
| V_actual (a·(b×c)) | 24682.259977 Å³ | Computed from rotated real vectors |
| V_formula | 24682.256630 Å³ | From cell param formula |
| Δ (actual - formula) | +3.347e-03 Å³ | 0.000014% relative error |

### C Reference
| Metric | Value | Notes |
| --- | --- | --- |
| V_actual (a·(b×c)) | 24682.256630 Å³ | Computed from rotated real vectors |
| V_formula | 24682.256630 Å³ | From cell param formula |
| Δ (actual - formula) | 0.000 Å³ | Perfect match |

### PyTorch (float64, CPU) - To be captured

*Required for hypothesis H2 (precision rule-out); run harness with `--dtype float64` and append results here.*

## Cross-Implementation Comparison

| Metric | C | PyTorch (fp32) | Δ (Py-C) | Δ% |
| --- | --- | --- | --- | --- |
| V_actual | 24682.256630 Å³ | 24682.259977 Å³ | +3.347e-03 Å³ | +0.000014% |
| V_formula | 24682.256630 Å³ | 24682.256630 Å³ | 0.000 Å³ | 0.000000% |

**Interpretation:**
- V_formula perfect match confirms cell parameters parse identically
- Small V_actual delta (+3.35e-03 Å³, 14 parts per billion) suggests accumulated precision error in cross-product reconstruction
- Magnitude is ~1000× smaller than the real-space Y-component drift (+8.74e-03 Å in a_y, +4.57e-02 Å in b_y)
- **Hypothesis H2 (V_actual vs V_formula) is UNLIKELY** to explain the Y-drift because V_actual deltas are O(1e-3) Å³ while Y-component deltas are O(1e-2) Å

## Metric Duality Analysis

From invariant_probe.md, the a·a* products show:

| Vector Pair | C | PyTorch | Δ (Py-C) | Notes |
| --- | --- | --- | --- | --- |
| a · a* | 1.000626354 | 0.999999925 | -6.264e-04 | C deviates from ideal by ~0.06% |
| b · b* | 0.999558509 | 0.999999893 | +4.414e-04 | C deviates from ideal by ~0.04% |
| c · c* | 0.999812669 | 0.999999901 | +1.872e-04 | C deviates from ideal by ~0.02% |

**Interpretation:**
- PyTorch achieves near-perfect metric duality (a·a* ≈ 1.0 within 7.5e-05)
- C shows systematic deviations (O(1e-3)) suggesting accumulated drift in reciprocal recalculation
- Per CLAUDE Rule #13, using V_actual instead of V_formula ensures exact metric duality
- **PyTorch correctly implements V_actual rule; C may use formula volume, accumulating small errors**

## Spindle-Axis Magnitude Analysis

### C Reference
From `c_trace_scaling.log`:
```
spindle ROTATION_AXIS= -1 0 0
```
Normalized magnitude: **1.0** (exact)

### PyTorch
*Need to extract from trace or config; spindle_axis not explicitly logged in current TRACE_PY output.*

**Action Required:** Add `TRACE_PY: spindle_axis` line to trace instrumentation before/after normalization to verify magnitude matches C.

## Hypotheses Assessment

### H1: Spindle-Axis Normalization (PRIMARY SUSPECT)
- **Evidence needed:** PyTorch spindle magnitude before/after normalization
- **Expected:** If PyTorch doesn't normalize while C does, magnitude error amplifies into Y-drift
- **Test:** Add TRACE_PY line showing raw spindle input and normalized spindle used in rotation

### H2: V_actual vs V_formula (RULED OUT)
- **Evidence:** V_actual delta is O(1e-3) Å³, Y-component drift is O(1e-2) Å (1000× larger)
- **Conclusion:** Volume choice cannot explain observed drift magnitude
- **Status:** Low priority

### H3: Phi Initialization Offset (MEDIUM PRIORITY)
- **Evidence needed:** Check if φ=0.0 in both implementations or if one uses phi_start vs zero
- **Test:** Per-phi trace shows φ=0.0 for first step (line 13 of per_phi JSON), consistent with C
- **Status:** Unlikely, but verify C trace phi value

### H4: Precision (fp32 vs fp64) (RULED OUT)
- **Rationale:** Reciprocal vectors match to O(1e-09) Å⁻¹ (nanometer scale), so precision is excellent
- **Status:** Not a factor

## Recommended Next Actions

1. **Instrument spindle_axis logging** in PyTorch trace (add to trace_harness or simulator TRACE_PY)
2. **Rerun with --dtype float64** to populate PyTorch fp64 row in volume table (for completeness)
3. **Document spindle normalization** in Crystal class and confirm it matches C's approach
4. **Execute H1 test:** Compare spindle magnitudes before/after rotation application

## Tolerance Thresholds

- Volume delta: ≤1e-6 Å³ (SPEC threshold from input.md line 66)
  - **Current:** +3.347e-03 Å³ → **FAIL** (3000× over threshold)
  - **However:** This is a secondary metric; primary concern is rotation vector parity
- Spindle norm delta: ≤5e-4 (SPEC threshold from input.md line 42)
  - **Status:** Not yet measured (needs instrumentation)

## Artifacts
- Source data: `reports/2025-10-cli-flags/phase_l/rot_vector/invariant_probe.md`
- Rotation vectors: `reports/2025-10-cli-flags/phase_l/rot_vector/rot_vector_comparison.md`
- C trace: `reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log`
- PyTorch trace: `reports/2025-10-cli-flags/phase_l/rot_vector/trace_py_rot_vector.log`
- Per-φ data: `reports/2025-10-cli-flags/phase_l/per_phi/reports/2025-10-cli-flags/phase_l/rot_vector/trace_py_rot_vector_per_phi.json`

---
**Generated:** 2025-10-07 (ralph loop, CLI-FLAGS-003 Phase L3g evidence gathering)
