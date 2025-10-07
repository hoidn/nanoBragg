# Rotation Vector φ=0 Drift Analysis

## Executive Summary

Phase L3f rotation-vector audit reveals component-level discrepancies in real-space vectors at φ=0 while reciprocal vectors remain highly aligned. Key finding: **Y-component drift in all three real-space vectors (0.04-6.8% deltas)** explains the k_frac offset observed in Phase L2c/L3e.

## Key Metrics

### Metric Duality (from invariant_probe.md)
- **Volume discrepancy**: +3.35e-03 Å³ (+0.000014%)
- **a·a* deviation**: -6.264e-04 (C=1.000626, Py=1.000000)
- **b·b* deviation**: +4.414e-04 (C=0.999559, Py=1.000000)
- **c·c* deviation**: +1.872e-04 (C=0.999813, Py=1.000000)

**Interpretation**: PyTorch achieves near-perfect metric duality (a·a* ≈ 1.0 within 7.5e-05) as required by crystallographic convention. C implementation shows O(1e-3) deviations from unity, suggesting accumulated numerical drift in the reciprocal-space recalculation pipeline.

## Component-Level Findings

### Real-Space Vector Deltas (from rot_vector_comparison.md)

**Y-component systematic drift (all vectors):**
- a_y: -0.0399% (-8.740e-03 Å)
- b_y: **+6.8095%** (+4.573e-02 Å) ← **largest delta**
- c_y: -0.0626% (-1.529e-02 Å)

**Z-component drift (moderate):**
- a_z: +0.6194% (+3.436e-02 Å)
- b_z: -0.0037% (+1.089e-03 Å)
- c_z: +0.3945% (+3.832e-02 Å)

**X-component alignment (excellent):**
- All X deltas <1.4e-06 Å (<0.0001%)

### Reciprocal-Space Vector Alignment (excellent)

All reciprocal components match within **O(1e-09)** (nanometer-scale precision), indicating:
1. Initial reciprocal vector construction is identical
2. Drift accumulates during real→reciprocal recalculation

## Hypotheses for Y-Component Drift (Phase L3g Input)

### H1: Spindle Axis Normalization
**Status**: Primary suspect
**Evidence**: Y-component drift pattern matches spindle-axis orientation (spec default: [0,1,0])
**Mechanism**: If PyTorch normalizes spindle vector before φ rotation while C uses raw input, small magnitude errors amplify into real-space Y drift after cross-product reconstruction
**Test**: Compare `spindle_axis` magnitude in traces; verify `Crystal.get_rotated_real_vectors` normalization path

### H2: Reciprocal→Real Reconstruction Volume
**Status**: Secondary suspect
**Evidence**: Volume delta (+3.3e-03 Å³) suggests different V_actual usage
**Mechanism**: Spec (CLAUDE.md Rule #13) mandates V_actual = a·(b×c) for reconstruction. If C uses formula volume while PyTorch uses V_actual, cross-products acquire systematic bias
**Test**: Log V_formula vs V_actual in both implementations; check if C bypasses recalculation

### H3: Phi Step Initialization
**Status**: Unlikely (φ=0 case)
**Evidence**: Phi-independent drift would require base vector misalignment
**Mechanism**: At φ=0, rotation matrix is identity—drift must stem from pre-rotation state
**Test**: Extend probe to φ>0 steps; if drift is phi-invariant, rule out rotation code

### H4: Float32 Precision Loss
**Status**: Ruled out
**Evidence**: Reciprocal vectors maintain 1e-09 precision despite float32 dtype
**Mechanism**: If precision were the issue, reciprocal would drift equally
**Test**: Rerun harness with --dtype float64 (DONE: deltas unchanged per Attempt #71)

## Recommended Corrective Action (for L3g)

1. **Immediate probe** (blocking): Add `TRACE_C/PY: spindle_axis` + `spindle_magnitude` to harness at phi=0
2. **Volume audit**: Log `V_formula` vs `V_actual` in both C (nanoBragg.c:~1450) and PyTorch (Crystal.py:~450)
3. **Normalization check**: Verify `Crystal.get_rotated_real_vectors` (src/nanobrag_torch/models/crystal.py:1000-1050) applies `spindle_axis / torch.linalg.norm(spindle_axis)` before `rotate_vector_around_axis`
4. **C reference**: Cross-check nanoBragg.c lines 3006-3098 (phi rotation loop) for implicit normalization or V choice

## Next Actions (Phase L3g Tasks)

Per `plans/active/cli-noise-pix0/plan.md`:
- [ ] Capture spindle_axis/V_actual probes under `reports/.../rot_vector/spindle_audit.log`
- [ ] Document hypothesis selection in updated `analysis.md`
- [ ] Propose corrective patch (if PyTorch needs C semantics) or spec clarification (if PyTorch is correct)
- [ ] Update docs/fix_plan.md Attempt history with probe results before touching simulator.py

## Artifacts
- `invariant_probe.md` — metric duality summary
- `rot_vector_comparison.md` — component-level deltas (61 lines)
- `trace_py_rot_vector.log` — harness output (40 TRACE_PY lines)
- C reference: `reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log`

## Exit Criteria for Phase L3g
- Hypothesis chosen with supporting probe evidence (spindle/volume logs)
- Corrective action documented (code patch or spec update)
- Analysis.md updated with decision rationale
- Plan/fix_plan refreshed before L3h implementation loop

---

## 2025-10-07 Evidence Refresh (ralph loop i=90 - CLI-FLAGS-003 Phase L3g)

### Summary
Executed spindle-axis magnitude and volume analysis per input.md guidance. Refreshed PyTorch trace with 40 TRACE_PY + 10 TRACE_PY_PHI lines, captured volume metrics, and documented hypotheses.

### Key Findings

#### Spindle-Axis Analysis
- **C Reference:** spindle ROTATION_AXIS = [-1, 0, 0], norm = 1.0 (exact unit vector)
- **PyTorch:** Spindle axis not explicitly logged in current TRACE_PY output
- **LIMITATION:** Cannot directly measure spindle norm delta without instrumentation
- **Hypothesis H1 Status:** PRIMARY SUSPECT - needs TRACE_PY probe for raw + normalized spindle

#### Volume Metrics
| Implementation | V_formula (Å³) | V_actual (Å³) | Delta (Å³) | Rel Err |
| --- | --- | --- | --- | --- |
| PyTorch (fp32) | 24682.256630 | 24682.259977 | +3.347e-03 | 0.000014% |
| C Reference | 24682.256630 | 24682.256630 | 0.000 | 0.000000% |

**Cross-Implementation:** Δ(V_actual) = +3.347e-03 Å³ (0.000014%)

**Tolerance Verdict:**
- ✗ FAIL: V_actual delta exceeds tolerance (>1e-6 Å³, spec threshold from input.md:66)
- **However:** Delta is ~1000× smaller than Y-component drift magnitude (O(1e-2) Å)

#### Hypothesis H2 Assessment: RULED OUT
Volume choice (V_actual vs V_formula) **cannot explain** observed Y-drift:
- V_actual delta: O(1e-3) Å³ (parts per billion)
- Y-component drift: O(1e-2) Å (b_y: +4.573e-02 Å, +6.8%)
- Magnitude ratio: ~1000:1

**Conclusion:** PyTorch correctly uses V_actual per CLAUDE Rule #13, achieving near-perfect metric duality (a·a* ≈ 1.0 within 7.5e-05). C's O(1e-3) metric duality errors suggest formula volume usage, but this is **unrelated to Y-drift**.

#### Metric Duality Evidence
| Metric | C | PyTorch | Δ (Py-C) | Notes |
| --- | --- | --- | --- | --- |
| a · a* | 1.000626354 | 0.999999925 | -6.264e-04 | C deviates ~0.06% |
| b · b* | 0.999558509 | 0.999999893 | +4.414e-04 | C deviates ~0.04% |
| c · c* | 0.999812669 | 0.999999901 | +1.872e-04 | C deviates ~0.02% |

**Interpretation:** PyTorch implementation is **more accurate** for reciprocal↔real consistency.

#### Real-Space Drift Pattern (φ=0)
- **Y-Component (CRITICAL):** Systematic drift in all three vectors
  - b_y: +6.8% (+4.573e-02 Å) ← LARGEST
  - a_y: -0.04% (+8.740e-03 Å)
  - c_y: -0.06% (+1.529e-02 Å)
- **Z-Component (MODERATE):** a_z +0.62%, c_z +0.39%
- **X-Component (EXCELLENT):** All deltas <1.4e-06 Å (<0.0001%)

**Pattern Analysis:** Y-drift dominates, aligns with spindle axis orientation (spec default [0,1,0] or supervisor override [-1,0,0]).

#### Reciprocal Vectors: EXCELLENT PARITY
All reciprocal components (a*, b*, c*) match C within O(1e-09) Å⁻¹ (nanometer scale).
**Indicates:** Initial reciprocal vector construction is identical. Divergence occurs during **real→reciprocal recalculation or phi rotation**.

### Updated Hypothesis Ranking

1. **H1: Spindle-Axis Normalization** (PRIMARY - NEEDS INSTRUMENTATION)
   - **Symptom:** Y-component drift pattern matches spindle orientation
   - **Test:** Add TRACE_C/PY for raw spindle_axis and spindle_axis_normalized
   - **Expected:** Magnitude difference amplifies into Y-drift via cross-products
   - **Next Diagnostic:** Log ap/bp before mosaic (per input.md Step 6 guidance)

2. **H3: Phi Initialization Offset** (MEDIUM - VERIFY C phi VALUE)
   - Per-phi JSON shows φ=0.0 for first step (consistent expectation)
   - Verify C trace also logs φ=0.0

3. **H4: Precision (fp32 vs fp64)** (RULED OUT)
   - Reciprocal vectors match to O(1e-09) Å⁻¹
   - Precision is excellent; not a contributing factor

4. **H2: V_actual vs V_formula** (RULED OUT - SEE ABOVE)
   - Volume delta O(1e-3) Å³ << Y-drift O(1e-2) Å
   - Cannot explain observed magnitude

### Artifacts Generated
- `spindle_audit.log`: Spindle comparison, volume analysis, hypothesis ranking
- `volume_probe.md`: Detailed volume calculations with tolerance thresholds
- `test_collect.log`: Pytest collection verification (4 tests collected)
- `input_files.sha256`: Checksums for A.mat, scaled.hkl + git SHA + timestamp
- `trace_run.log`: Harness execution log (40 TRACE_PY + 10 TRACE_PY_PHI lines captured)

### Tolerance Thresholds (from input.md)
- Spindle norm delta: ≤5e-4
- Volume delta: ≤1e-6 Å³

### Environment
- Commit: b80f8372628f9c025e4204213f08511c926f7a0a
- Timestamp: 2025-10-07T03:57:46-07:00
- Device: CPU
- Dtype: float32

### Next Actions
Per input.md Step 6-7 guidance and plan Phase L3g:
1. **Instrumentation:** Add `TRACE_PY: spindle_axis (raw)` and `TRACE_PY: spindle_axis_normalized` to trace harness
2. **Optional float64 probe:** Rerun with `--dtype float64` to populate fp64 volume row
3. **Verify C phi:** Extract phi value from c_trace_scaling.log or regenerate with phi logging
4. **Phase L3h:** Once H1 probe confirms normalization mismatch, draft implementation strategy with C-code docstring references before touching simulator
