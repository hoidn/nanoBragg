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
