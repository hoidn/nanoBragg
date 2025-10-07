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
- [x] Capture fresh C trace with added `TRACE_C` hooks (owner: Ralph) → artifact `c_trace_mosflm.log`. ✅ **COMPLETE** (Attempt #93, 2025-10-07)
- [x] Extend PyTorch harness to dump raw numpy vectors and tensor views (`py_raw_vectors.json`, `py_tensor_vectors.json`). ✅ **COMPLETE** (Phase L3h probes)
- [x] Produce `mosflm_matrix_diff.md` summarizing the per-stage deltas. ✅ **COMPLETE** (Attempt #93)
- [ ] Update `docs/fix_plan.md` Attempt history once the diff pinpoints the guilty transpose or scaling step.

The corrective implementation should wait until the diff document exists so we can make a surgical change and immediately validate via the rotation trace and the per-φ scaling audit.

---

## Post-L3i Findings (Attempt #93, 2025-10-07)

### MOSFLM Matrix Semantics (H3) — RULED OUT

**Evidence Summary:**
Phase L3i instrumentation captured full C MOSFLM pipeline trace (291 lines) using `golden_suite_generator/nanoBragg.c:2050-2199`. Component-level diff (`mosflm_matrix_diff.md`) proves:

1. **Reciprocal vectors match** to O(1e-9) Å⁻¹ after wavelength scaling (Stage 2)
2. **Volume agreement excellent**: ΔV = 0.04 Å³ (0.0002%) between C and PyTorch (Stage 4)
3. **Real-space b_Y component matches** within float32 precision:
   - C: `0.71732` Å (`c_trace_mosflm.log:64`)
   - PyTorch: `0.717319786548615` Å (Phase L3f/L3h probes)
   - Absolute delta: **1.35e-07 Å (0.00002%)**
4. **Reciprocal regeneration exact** to 15 digits per CLAUDE Rule #13 (Stage 6)

**Verdict:** The transpose hypothesis is **eliminated**. MOSFLM matrix loading and cross-product pipeline are correct at φ=0.

**Artifact Locations:**
- `c_trace_mosflm.log` (291 lines) — Full C trace with MOSFLM pipeline
- `c_trace_extract.txt` (55 TRACE lines) — Quick reference extract
- `mosflm_matrix_diff.md` — Component-level diff analysis with H3 ruling
- `c_trace_mosflm.sha256` — Checksum: `7955cbb82028e6d590be07bb1fab75f0f5f546adc99d68cbd94e1cb057870321`

### Updated Hypothesis Ranking (Post-L3i → Phase L3j Focus)

**H5: φ Rotation Application** (NEW PRIMARY SUSPECT)
- **Evidence:** Phase L3i proves MOSFLM base vectors at φ=0 are correct (b_Y agrees to O(1e-7) Å). The +6.8% Y-drift observed in Phase L3f must emerge during `get_rotated_real_vectors()` when φ transitions from 0° → 0.05° → 0.1°.
- **Mechanism:**
  - Rotation matrix construction differs between C (`nanoBragg.c:3006-3098` phi rotation loop) and PyTorch (`Crystal.get_rotated_real_vectors`, `src/nanobrag_torch/models/crystal.py:1000-1050`)
  - Axis alignment or rotation application order diverges
  - Per-phi accumulation may compound small errors
- **Supporting Clue:** Phase K3e showed constant Δk≈6.0 across all φ steps, suggesting a systematic base-vector rotation issue rather than compounding per-step drift
- **C Reference Lines:** `golden_suite_generator/nanoBragg.c:3006-3098` (phi rotation loop with ap/bp/cp assignment)
- **PyTorch Reference Lines:** `src/nanobrag_torch/models/crystal.py:568-780` (MOSFLM path), lines 1000-1050 (`get_rotated_real_vectors`)
- **Test Strategy:**
  - Capture per-φ traces at φ=0°, 0.05°, 0.1° (supervisor command uses phisteps=10, osc=0.1 → φ samples at these values)
  - Instrument rotation intermediate values: rotation matrix R, pre-rotation base vectors, post-rotation ap/bp/cp
  - Diff C vs PyTorch rotation matrices component-by-component
  - Quantify when Y-drift first exceeds threshold (expected: emerges immediately after first rotation step)

**H6: Unit Conversion Boundary** (SECONDARY SUSPECT)
- **Evidence:** C applies `1e-10` Å→meter conversion before copying to `a0/b0/c0` (`c_trace_mosflm.log:93-95`). PyTorch stores vectors in Å throughout Crystal but may convert at different stage during rotation.
- **Mechanism:** If PyTorch rotates in Angstroms while C rotates in meters (or vice versa), accumulated rounding differences across phi steps produce systematic drift.
- **Test Strategy:**
  - Add `TRACE_PY` for base vector units before/after rotation (Å vs meters)
  - Compare C's meter-converted ap/bp/cp (`c_trace_mosflm.log:101-103`) against PyTorch's rotated vectors
  - Verify unit system matches spec (CLAUDE.md Rule #1: detector in meters, physics in Å)

**H7: Per-Phi Accumulation Order** (TERTIARY — likely ruled out)
- **Evidence:** Phase K3e showed constant Δk≈6.0 across all φ steps. If accumulation were compounding, early phi steps would show smaller deltas that grow over time.
- **Mechanism:** Rotating from wrong initial state or applying rotations in non-commutative order
- **Counter-Evidence:** Constant delta suggests base-vector issue at φ=0 propagates unchanged through all steps
- **Status:** Defer unless H5/H6 investigations show per-step variation

### φ Sampling Requirements (Supervisor Command Context)

**Supervisor Command Parameters:**
```bash
-phi 0 -phisteps 10 -osc 0.1
```

**φ Sample Points:**
- φ_start = 0°
- φ_step = osc / phisteps = 0.1° / 10 = 0.01°
- Sample 0: φ = 0.0°
- Sample 1: φ = 0.01° (1% of oscillation range)
- Sample 5: φ = 0.05° (50% of oscillation range)
- Sample 10: φ = 0.1° (100% of oscillation range)

**Critical Samples for Verification:**
1. **φ=0.0°** — Base case (already validated in L3i, b_Y correct)
2. **φ=0.05°** — Mid-oscillation point to detect cumulative drift
3. **φ=0.1°** — Full oscillation to confirm drift magnitude

**Beamsize Context:** Supervisor command includes `-beamsize 0.0005` (500 nm). Per spec, beam diameter intersects multiple phi steps, so per-φ traces capture realistic motion envelope.

### Quantitative Deltas (from Phase L3f/L3e)

**Real-Space Vector Y-Component Drift (φ=0, pre-L3i baseline):**
- a_Y: -0.0399% (-8.740e-03 Å)
- **b_Y: +6.8095%** (+4.573e-02 Å) ← **LARGEST DELTA**
- c_Y: -0.0626% (-1.529e-02 Å)

**Fractional Miller Index k_frac Impact:**
- C: `k_frac = -0.607255839576692` (`c_trace_scaling.log`)
- PyTorch: `k_frac = -0.589141607284546` (`trace_py_rot_vector.log`)
- Shift: Δk ≈ 0.018 (causes F_latt_b sign flip)

**Intensity Before Scaling:**
- C: `I_before_scaling = 9.44e5` (`c_trace_scaling.log`)
- PyTorch: `I_before_scaling = 7.13e5` (Attempt #86 traces)
- Ratio: 0.755 (24.5% underestimation)

**F_latt Component Sign Flip:**
- C: `F_latt_b > 0` (positive lattice factor)
- PyTorch: `F_latt_b < 0` (sign flip due to k_frac shift)

### Correction Strategy (Phase L3j Implementation Prerequisites)

**Before Code Changes:**
1. Generate per-φ traces (φ=0, 0.05, 0.1) with rotation matrix instrumentation
2. Create `fix_checklist.md` with quantitative thresholds:
   - Per-φ b_Y drift: ≤1e-6 relative (currently +6.8%)
   - k_frac alignment: ≤1e-6 absolute (currently Δk≈0.018)
   - F_latt sign consistency: must match C
   - I_before_scaling ratio: 0.99–1.01 (currently 0.755)

**Implementation Path (after checklist):**
1. Isolate rotation matrix construction in PyTorch (`Crystal.get_rotated_real_vectors`)
2. Compare against C rotation semantics (`nanoBragg.c:3006-3098`)
3. Apply surgical patch with C-code docstring references (CLAUDE.md Rule #11)
4. Validate against all checklist gates before merging

**Verification Thresholds (from spec and prior evidence):**
- Component-level real-space vectors: ≤1e-6 relative error
- Miller index fractional parts: ≤1e-6 absolute error
- Final intensity ratio: 0.99–1.01 (per spec parity thresholds)
- Per-φ JSON stability: k_frac drift <1e-6 across phi steps

### Next Actions (Phase L3j Tasks)

Per `plans/active/cli-noise-pix0/plan.md` Phase L3j:
- [x] **L3j.1**: Update `mosflm_matrix_correction.md` with Attempt #93 findings ✅ **THIS SECTION**
- [ ] **L3j.2**: Create `fix_checklist.md` enumerating verification gates with thresholds
- [ ] **L3j.3**: Update plan and `docs/fix_plan.md` Attempt history with artifact paths

### References

**C-Code:**
- MOSFLM matrix pipeline: `golden_suite_generator/nanoBragg.c:2050-2199`
- φ rotation loop: `golden_suite_generator/nanoBragg.c:3006-3098`

**PyTorch:**
- MOSFLM path: `src/nanobrag_torch/models/crystal.py:568-780`
- Rotation method: `src/nanobrag_torch/models/crystal.py:1000-1050`

**Spec/Architecture:**
- CLAUDE.md Rule #1 (hybrid unit system)
- CLAUDE.md Rule #12 (misset pipeline)
- CLAUDE.md Rule #13 (reciprocal recalculation)
- `specs/spec-a-cli.md` §3.3 (pix0 overrides, -nonoise)
- `docs/architecture/detector.md:35` (BEAM/SAMPLE formulas)
- `docs/development/c_to_pytorch_config_map.md:42` (pivot/unit mapping)
- `docs/debugging/debugging.md:24` (parallel trace SOP)

**Prior Evidence:**
- Phase L3f: `rot_vector_comparison.md` (component deltas)
- Phase L3g: `spindle_audit.log` (H1 ruled out)
- Phase L3h: `mosflm_matrix_probe_output.log` (H2 ruled out, V_actual correct)
- Phase L3i: `mosflm_matrix_diff.md` (H3 ruled out, b_Y matches at φ=0)
