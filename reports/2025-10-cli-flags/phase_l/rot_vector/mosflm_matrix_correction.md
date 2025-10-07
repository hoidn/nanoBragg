# MOSFLM Matrix Correction Plan (Phase L3i)

## Observed Divergence
- Evidence runs on the supervisor command (`reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log`, `reports/2025-10-cli-flags/phase_l/rot_vector/trace_py_rot_vector.log`) show the first mismatch at φ=0:
  - `rot_b_angstroms` Y component: C = `0.671588233999813` (`c_trace_scaling.log:268`), PyTorch = `0.717319786548615` (`trace_py_rot_vector.log:16`). Relative delta ≈ `+6.81%` (logged in `rot_vector_comparison.md`).
  - Fractional Miller index at φ=0: C reports `k_frac = -0.607255839576692`, PyTorch reports `k_frac = -0.589141607284546`, shifting the peak search window and flipping the sign of `F_latt_b`.
  - Reciprocal vectors match to `O(1e-9)` Å⁻¹ (see `rot_vector_comparison.md`), so the defect is isolated to the real-space reconstruction step.
- Downstream effect: PyTorch computes `F_latt` with the wrong orientation, yielding `I_before_scaling = 7.13e5` while C logs `9.44e5` for the same pixel.

## nanoBragg.c Reference Pipeline
The C implementation constructs MOSFLM orientation as follows:
1. **Matrix load and wavelength scaling** — `golden_suite_generator/nanoBragg.c:2050-2075` (reads three rows, transposes implicitly by assigning into `a_star`, `b_star`, `c_star`, then scales by `1e-10/lambda0`).
2. **Misset rotation (if any)** — `nanoBragg.c:2095-2109` rotates the reciprocal vectors before any real-space work.
3. **Cross products and volumes** — `nanoBragg.c:2121-2153` forms `a_star×b_star`, `b_star×c_star`, `c_star×a_star`, computes `V_star`, and derives `V_cell = 1/V_star`.
4. **Real-space reconstruction** — `nanoBragg.c:2155-2164` scales the cross products by `V_cell` to obtain `a`, `b`, `c` in Å (these values appear in the trace quoted above).
5. **Reciprocal regeneration for metric duality** — `nanoBragg.c:2171-2185` recomputes `a*`, `b*`, `c*` from the real vectors (completing CLAUDE Rule #13).

## PyTorch Implementation Snapshot
- `Crystal.compute_cell_tensors` mirrors the same stages (`src/nanobrag_torch/models/crystal.py:568-780`). When `mosflm_*` vectors are present, it:
  1. Loads them as tensors (lines 572-588).
  2. Applies misset via `angles_to_rotation_matrix` (lines 656-708).
  3. Forms cross products and computes `V_star`, `V_cell`, and real vectors (lines 714-768).
  4. Updates `self.cell_{a,b,c}` and regenerates reciprocal vectors (lines 770-811).
- CLI parsing stores the MOSFLM vectors and derived cell parameters (`src/nanobrag_torch/__main__.py:426-437`).
- The rotation trace harness (`trace_py_rot_vector.log`) confirms PyTorch is executing this path, yet the reconstructed `b` vector still diverges from C.

## Analysis & Hypothesis
1. **Stage parity prior to real reconstruction is verified:** raw MOSFLM vectors after wavelength scaling and misset match to ≤1e-9 Å⁻¹.
2. **Real vectors diverge immediately after scaling by `V_cell`:** comparing `c_trace_scaling.log` vs `trace_py_rot_vector.log` shows the deltas arise during `a = (b* × c*) · V_cell` etc.
3. **Volume calculations agree:** `mosflm_matrix_probe_output.log` records `V_cell` parity to 1.5e-11 Å³, ruling out Rule #13 violations (Hypothesis H2).
4. **Likely culprit:** PyTorch uses the same cross products but performs them in torch with the orientation tensors already on the simulation device/dtype. Because reciprocal vectors match, the only remaining degree of freedom is *axis ordering*. `Torch.cross` treats inputs as column vectors; C stores them in `double[4]` with index origin at 1. If PyTorch is inadvertently transposing the MOSFLM vectors (e.g., due to `torch.as_tensor` assuming row-major layout on already-transposed numpy arrays), the cross product ordering can flip a sign on the y component. This guess aligns with the observed +6.8% bump and sign flip in `F_latt_b`.
5. **Supporting clue:** When the harness reads `A.mat`, it transposes the matrix before returning the vectors (`read_mosflm_matrix`); we need to confirm this transpose agrees with C’s column-wise assignment.

## Correction Plan
1. **Instrument nanoBragg for stage-by-stage export (Phase L3i.a):**
   - Add `TRACE_C` lines after each step in `nanoBragg.c:2050-2169` to dump `b_star×c_star`, `V_cell`, and the resulting `b` vector (retain for diffing).
   - Capture logs under `reports/2025-10-cli-flags/phase_l/rot_vector/c_trace_mosflm.log`.
2. **Mirror instrumentation in PyTorch (Phase L3i.b):**
   - Extend `trace_harness.py` to record the raw numpy vectors returned by `read_mosflm_matrix` *before* conversion to tensors, the tensors passed into `Crystal`, and the intermediate cross products pulled from `Crystal.compute_cell_tensors` (hook via temporary logging patch or an exported helper).
   - Store outputs in `reports/.../py_tap_points.md` to align with the C trace.
3. **Diff the traces (Phase L3i.c):**
   - Build `reports/.../rot_vector/mosflm_matrix_diff.md` summarizing per-component deltas prior to the real-vector scaling step. Confirm whether the discrepancy appears immediately after the numpy→torch conversion.
4. **Adjust PyTorch loader if transpose confirmed (Phase L3i.d):**
   - If the transpose is wrong, flip the ordering in `nanobrag_torch/io/mosflm.py` and add regression coverage in `tests/test_mosflm_matrix.py` to assert the reconstructed `b` matches the C value (`0.671588233999813 Å`).
   - If transpose is correct, revisit `Crystal.compute_cell_tensors` to ensure we replicate the exact `vector_scale` semantics (C stores magnitude in index 0; PyTorch ignores it). We may need to store and reuse the scalar magnitude instead of recomputing via `torch.norm`.
5. **Verification gates (Phase L3j prerequisites):**
   - Update `reports/.../rot_vector/fix_checklist.md` with required reproductions: harness diff, `pytest tests/test_cli_scaling.py -k lattice`, and targeted nb-compare ROI after the fix.

## Immediate Next Steps
- [ ] Capture fresh C trace with added `TRACE_C` hooks (owner: Ralph) → artifact `c_trace_mosflm.log`.
- [ ] Extend PyTorch harness to dump raw numpy vectors and tensor views (`py_raw_vectors.json`, `py_tensor_vectors.json`).
- [ ] Produce `mosflm_matrix_diff.md` summarizing the per-stage deltas.
- [ ] Update `docs/fix_plan.md` Attempt history once the diff pinpoints the guilty transpose or scaling step.

The corrective implementation should wait until the diff document exists so we can make a surgical change and immediately validate via the rotation trace and the per-φ scaling audit.
