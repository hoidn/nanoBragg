# Phase D4 Summary - Simulator F_latt Diagnosis

**Timestamp:** 20251010T073708Z
**Task:** [VECTOR-PARITY-001] Phase D4 - Diagnose simulator F_latt regression (32× intensity gap)
**Status:** ✅ ROOT CAUSE IDENTIFIED

## Scope

Instrument the production simulator (`Simulator.run()` → `compute_physics_for_position()`) to capture F_latt pipeline values for pixel (1792,2048) and compare against the trace helper output from Phase D3.

## Root Cause Identified

**BUG: Miller Index Unit Mismatch (10^10× error)**

### Symptom
Miller indices in the simulator are 10^10 times too large compared to the trace helper:

| Variable | Trace Helper (Correct) | Simulator (WRONG) | Ratio |
|----------|----------------------|-------------------|-------|
| h        | -6.576e-02          | -6.576e+08        | 1e+10 |
| k        | 5.128e+00           | 5.128e+10         | 1e+10 |
| l        | -9.997e-03          | -9.997e+07        | 1e+10 |

### Root Cause

**Unit mismatch in Miller index calculation (simulator.py:196-198):**

```python
h = dot_product(scattering_broadcast, rot_a_broadcast)
k = dot_product(scattering_broadcast, rot_b_broadcast)
l = dot_product(scattering_broadcast, rot_c_broadcast)
```

- **scattering_vector**: m⁻¹ (meters⁻¹) after Phase D1 fix (line 158)
- **rot_a/b/c**: Angstroms (Å) from Crystal.get_rotated_real_vectors()
- **Result**: h/k/l are dimensionless but 10^10 too large

The correct formula requires both vectors in the same units:
```
h = a · S    where both a and S are in m⁻¹ (or both in Å⁻¹)
```

Currently:
```
h = (a in Å) · (S in m⁻¹) = (a × 1e-10 m) · (S in m⁻¹) = correct × 1e-10
→ We need h × 1e10 to get the correct value!
```

### Impact on F_latt

Because sincg(π·h, N) is highly nonlinear, the 10^10× error in h completely destroys the lattice factor calculation. The values we're seeing (F_latt_a≈3.66, F_latt_b≈0.51, F_latt_c≈4.86) are essentially random outputs from sincg() with astronomically large inputs.

**Expected values** (from trace helper with correct h/k/l):
- F_latt_a: 4.186802197313074e+00
- F_latt_b: 2.301221333639228e+00
- F_latt_c: 4.980295808862998e+00
- F_latt: 4.798394755717462e+01

**Actual simulator values** (with 10^10× error):
- F_latt_a: 3.658078245859421e+00
- F_latt_b: 5.115733689553132e-01
- F_latt_c: 4.863481600288290e+00
- F_latt: 9.101399884157525e+00

Intensity is ~25× too low due to incorrect F_latt (9.1 vs 47.98).

## Recommended Fix

**Option A (Preferred): Convert lattice vectors to m⁻¹ at the call site**

In `Simulator.run()`, before calling `compute_physics_for_position()`:
```python
# Convert rotated lattice vectors from Å to m⁻¹
rot_a_meters_inv = rot_a * 1e10  # Å → m⁻¹
rot_b_meters_inv = rot_b * 1e10
rot_c_meters_inv = rot_c * 1e10
```

This ensures h = (a in m⁻¹) · (S in m⁻¹) yields dimensionless Miller indices at the correct scale.

**Option B: Convert scattering_vector back to Å⁻¹**

Revert the Phase D1 fix and keep scattering_vector in Å⁻¹. However, this contradicts the spec (spec-a-core.md line 446 states q in m⁻¹) and would break the trace helper parity we just achieved.

**Recommendation**: Option A. The spec is clear that q (scattering vector) should be in m⁻¹. The lattice vectors must match.

## Artifacts

- Instrumentation patch: `src/nanobrag_torch/simulator.py:312-367`
- Simulator trace log: `reports/2026-01-vectorization-parity/phase_d/20251010T073708Z/simulator_f_latt.log`
- Trace helper reference: `reports/2026-01-vectorization-parity/phase_d/py_traces_post_fix/pixel_1792_2048.log`

## Next Actions

1. ✅ **Root cause identified**: 10^10× unit mismatch in Miller index calculation
2. **Implement fix**: Convert rot_a/b/c from Å to m⁻¹ before passing to compute_physics_for_position()
3. **Verify**: Rerun simulator and confirm h/k/l match trace helper within ≤1e-12
4. **Validate**: Rerun ROI nb-compare and confirm corr≥0.999, |sum_ratio−1|≤5e-3
5. **Remove instrumentation**: Clean up NB_TRACE_SIM_F_LATT logging after validation
6. **Update fix_plan.md**: Mark Phase D4 complete and prepare for Phase D5 smoke test

## References

- Spec: `specs/spec-a-core.md` line 446 (q in m⁻¹)
- Phase D1 fix: `reports/2026-01-vectorization-parity/phase_d/20251010T062949Z/diff_scattering_vec.md`
- Phase D3 summary: `reports/2026-01-vectorization-parity/phase_d/20251010T071935Z/PHASE_D3_SUMMARY.md`
- Plan: `plans/active/vectorization-parity-regression.md` task D4
