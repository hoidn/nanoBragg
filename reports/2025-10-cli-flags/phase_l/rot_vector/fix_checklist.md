# φ Rotation Parity Fix Checklist (CLI-FLAGS-003 Phase L3j)

## Overview

This checklist enumerates verification gates for implementing the φ rotation parity fix. All gates must pass before marking CLI-FLAGS-003 Phase L3 complete.

**Primary Hypothesis:** H5 (φ Rotation Application) — Drift emerges during `Crystal.get_rotated_real_vectors()` when φ transitions from 0° → 0.05° → 0.1°.

**Evidence Base:** Phases L3a–L3i proved MOSFLM base vectors correct at φ=0 (b_Y agrees to O(1e-7) Å). Divergence must occur during phi rotation.

## Verification Gates

| ID | Requirement | Owner | Status | Artifact Path | Threshold / Notes |
|----|-------------|-------|--------|---------------|-------------------|
| **VG-1** | **Per-φ Harness Rerun** | Implementation Loop | ⏸️ | `reports/2025-10-cli-flags/phase_l/rot_vector/per_phi/` | After code fix, regenerate traces for φ=0°, 0.05°, 0.1° |
| VG-1.1 | φ=0° trace regeneration | Implementation Loop | ⏸️ | `per_phi/trace_py_phi_0.00.log` | Baseline; b_Y must remain within 1e-6 relative of C (currently 1.35e-07, PASS) |
| VG-1.2 | φ=0.05° trace generation | Implementation Loop | ⏸️ | `per_phi/trace_py_phi_0.05.log` | Mid-oscillation; b_Y drift ≤1e-6 relative (currently ~6.8%, FAIL pre-fix) |
| VG-1.3 | φ=0.1° trace generation | Implementation Loop | ⏸️ | `per_phi/trace_py_phi_0.10.log` | Full oscillation; b_Y drift ≤1e-6 relative |
| VG-1.4 | Per-φ JSON stability | Implementation Loop | ⏸️ | `per_phi/trace_py_scaling_per_phi.json` | k_frac drift <1e-6 across phi steps; F_latt signs match C |
| **VG-2** | **Targeted Pytest (Lattice Factors)** | Implementation Loop | ✅ (Attempt #98, 2025-11-21) | `reports/2025-10-cli-flags/phase_l/rot_vector/pytest_vg2.log` | Regression coverage for lattice vector parity; refresh log if missing |
| VG-2.1 | Execute test command | Implementation Loop | ✅ | `reports/2025-10-cli-flags/phase_l/rot_vector/pytest_vg2.log` | `env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 pytest tests/test_cli_scaling.py::TestFlattSquareMatchesC::test_f_latt_square_matches_c -v` |
| VG-2.2 | All tests pass | Implementation Loop | ✅ | Same as VG-2.1 | Zero failures; captures rotation parity across test matrix |
| **VG-3** | **nb-compare ROI Parity** | Implementation Loop | ⏸️ | `reports/.../nb_compare_phi_fix/` | End-to-end C↔PyTorch visual + metrics validation |
| VG-3.1 | Execute supervisor command | Implementation Loop | ⏸️ | `nb_compare_phi_fix/summary.json` | `nb-compare --roi 100 156 100 156 --resample --outdir reports/2025-10-cli-flags/phase_l/nb_compare_phi_fix/ -- [supervisor flags]` |
| VG-3.2 | Correlation ≥0.9995 | Implementation Loop | ⏸️ | `nb_compare_phi_fix/summary.json` | Image correlation meets spec threshold (specs/spec-a-parallel.md) |
| VG-3.3 | Sum ratio 0.99–1.01 | Implementation Loop | ⏸️ | `nb_compare_phi_fix/summary.json` | Total intensity parity within 1% |
| VG-3.4 | Mean peak distance ≤1px | Implementation Loop | ⏸️ | `nb_compare_phi_fix/summary.json` | Peak positions aligned (Hungarian matching if available) |
| **VG-4** | **Component-Level Delta Audit** | Implementation Loop | ⏸️ | Trace comparison doc | Quantitative verification of Y-drift correction |
| VG-4.1 | b_Y relative error ≤1e-6 | Implementation Loop | ⏸️ | Update `rot_vector_comparison.md` or new diff | Currently +6.8095%; must reduce to O(1e-6) |
| VG-4.2 | k_frac absolute error ≤1e-6 | Implementation Loop | ⏸️ | Updated per-φ JSON | Δk currently ≈0.018; must reduce to O(1e-6) |
| VG-4.3 | F_latt sign consistency | Implementation Loop | ⏸️ | Updated per-φ JSON | F_latt_b sign must match C across all φ samples |
| VG-4.4 | I_before_scaling ratio 0.99–1.01 | Implementation Loop | ⏸️ | Updated scaling trace | Currently 0.755 (24.5% under); must reach parity |
| **VG-5** | **Documentation Updates** | Implementation Loop | ⏸️ | Plan + fix_plan | Traceability for future debugging |
| VG-5.1 | Update `mosflm_matrix_correction.md` | Implementation Loop | ⏸️ | This file | Mark fix applied, cite code changes with line numbers |
| VG-5.2 | Update `plans/active/cli-noise-pix0/plan.md` | Implementation Loop | ⏸️ | Phase L3j rows | Mark L3j.1–L3j.3 [D]; update L4 prerequisites |
| VG-5.3 | Update `docs/fix_plan.md` CLI-FLAGS-003 | Implementation Loop | ⏸️ | Attempts History | Add Attempt #94+ with metrics, artifact paths, observations |
| VG-5.4 | Archive old traces (optional) | Implementation Loop | ⏸️ | `reports/archive/` or timestamped subdir | Move superseded logs to prevent confusion; update README |

## Detailed Gate Specifications

### VG-1: Per-φ Harness Rerun

**Purpose:** Validate rotation matrix construction at multiple φ angles to confirm drift is eliminated.

**Command Template:**
```bash
cd reports/2025-10-cli-flags/phase_l/rot_vector
python trace_harness.py --phi 0.0 --output per_phi/trace_py_phi_0.00.log
python trace_harness.py --phi 0.05 --output per_phi/trace_py_phi_0.05.log
python trace_harness.py --phi 0.1 --output per_phi/trace_py_phi_0.10.log
```

**Environment:**
- Device: CPU (for determinism; float64 optional for gradient debugging)
- Dtype: float32 (matches supervisor command)
- Seed: Use supervisor command seeds (`-seed`, `-mosaic_seed`)

**Trace Fields Required:**
- `TRACE_PY: rot_b_angstroms X Y Z` (real-space b vector after φ rotation)
- `TRACE_PY: k_frac` (fractional Miller index b-component)
- `TRACE_PY: F_latt_b` (lattice factor b-component)
- `TRACE_PY: I_before_scaling` (intensity before final scaling)
- `TRACE_PY: phi_deg` (confirm φ value for each sample)

**Success Criteria:**
- All per-φ traces show b_Y within 1e-6 relative of C baseline (`0.71732` Å from `c_trace_mosflm.log:64`)
- k_frac stable across phi steps (standard deviation <1e-6)
- F_latt_b sign matches C for all samples
- JSON export (`trace_py_scaling_per_phi.json`) contains valid structured data for downstream analysis

### VG-2: Targeted Pytest (Lattice Factors)

**Purpose:** Ensure regression coverage for rotation-dependent lattice factor calculations.

**Command:**
```bash
env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py -k lattice -v \
  2>&1 | tee reports/2025-10-cli-flags/phase_l/rot_vector/pytest_lattice_$(date +%Y%m%d).log
```

**Expected Coverage:**
- Tests exercising `get_rotated_real_vectors` with non-zero phi
- Assertions on F_latt sign consistency
- Multi-phi sweeps (if present in test suite)

**Success Criteria:**
- All tests PASS (zero failures, zero errors)
- Test collection succeeds (no ImportError)
- Output log saved for traceability

**Notes:**
- If `test_cli_scaling.py` does not exist, substitute with nearest equivalent (e.g., `test_at_crystal_*.py`)
- Add new regression test if coverage gaps identified (defer to separate loop if time-boxed)

### VG-3: nb-compare ROI Parity

**Purpose:** End-to-end visual + quantitative validation using the supervisor command.

**Supervisor Command Reference:**
Exact flags documented in `prompts/supervisor.md:18` and `input.md` Context Recap. Key parameters:
- `-lambda 0.9768 -distance 231.274660 -pixel 0.172`
- `-detpixels_x 256 -detpixels_y 256`
- `-phi 0 -phisteps 10 -osc 0.1`
- `-mat A.mat -hkl scaled.hkl`
- `-beamsize 0.0005 -nonoise -nointerpolate`
- Custom detector vectors: `-fdet_vector`, `-sdet_vector`, `-odet_vector`, `-pix0_vector_mm`

**Command:**
```bash
nb-compare --roi 100 156 100 156 --resample \
  --outdir reports/2025-10-cli-flags/phase_l/nb_compare_phi_fix \
  -- [exact supervisor flags]
```

**Environment Variables:**
- `NB_C_BIN=./golden_suite_generator/nanoBragg` (or `./nanoBragg` if fallback)
- `KMP_DUPLICATE_LIB_OK=TRUE`

**Output Artifacts:**
- `summary.json` (correlation, RMSE, sum_ratio, peak_distance)
- `diff_heatmap.png` (visual comparison)
- `c_output.bin`, `py_output.bin` (raw intensity arrays)

**Success Thresholds:**
- Correlation: ≥0.9995 (per specs/spec-a-parallel.md AT-PARALLEL thresholds)
- Sum ratio: 0.99–1.01 (C_sum / Py_sum)
- Mean peak distance: ≤1.0 px (if peak matching implemented)
- Max |Δ|: Document but not blocking (informational)

### VG-4: Component-Level Delta Audit

**Purpose:** Quantitative confirmation that Y-drift and downstream effects are corrected.

**Baseline Values (Pre-Fix):**
- b_Y: C=`0.71732` Å, PyTorch=`0.717319786548615` Å (φ=0, correct)
- b_Y: PyTorch at φ>0 shows +6.8095% drift (Phase L3f finding)
- k_frac: Δk≈0.018 (C=-0.607, PyTorch=-0.589)
- I_before_scaling ratio: 0.755 (C=9.44e5, PyTorch=7.13e5)

**Post-Fix Targets:**
- b_Y relative error: ≤1e-6 (0.0001%)
- k_frac absolute error: ≤1e-6
- F_latt_b sign: must match C (no sign flip)
- I_before_scaling ratio: 0.99–1.01 (within 1%)

**Verification Method:**
1. Extract post-fix values from per-φ traces (VG-1 artifacts)
2. Compute deltas against C baseline (`c_trace_mosflm.log`)
3. Document in updated `rot_vector_comparison.md` or new timestamped diff
4. Save comparison table in checklist completion notes

### VG-5: Documentation Updates

**Purpose:** Maintain traceability and prevent future regressions.

**Required Updates:**
1. **This file (`fix_checklist.md`)**: Mark rows ✅ as gates pass; add completion timestamp
2. **`mosflm_matrix_correction.md`**: Add "Post-Implementation" section citing:
   - Code changes with file:line references (e.g., `Crystal.get_rotated_real_vectors` at `src/nanobrag_torch/models/crystal.py:1000-1050`)
   - C-code docstring references per CLAUDE.md Rule #11
   - Before/after metrics table
3. **`plans/active/cli-noise-pix0/plan.md`**: Update Phase L3j rows to [D], refresh Phase L4 prerequisites
4. **`docs/fix_plan.md` CLI-FLAGS-003**: Add Attempt #94+ (or next sequence) with:
   - Metrics: Correlation, sum_ratio, b_Y delta, k_frac delta
   - Artifacts: List all VG artifact paths
   - Observations: Hypothesis confirmed (H5), code changes applied, thresholds met
   - Next Actions: Proceed to Phase L4 supervisor command parity rerun

**Archive Strategy (Optional):**
- Move superseded traces (e.g., old `trace_py_rot_vector.log`) to `reports/2025-10-cli-flags/phase_l/rot_vector/archive/` with timestamps
- Update `reports/2025-10-cli-flags/phase_l/rot_vector/README.md` to point at canonical post-fix artifacts
- Maintain SHA256 checksums for reproducibility

## Spec & Doc References

### Normative Specifications
- **specs/spec-a-cli.md §3.3**: CLI flags (`-nonoise`, `-pix0_vector_mm`, `-phi`, `-phisteps`, `-osc`)
- **specs/spec-a-core.md §4**: Geometry model (unit systems, rotation order)
- **specs/spec-a-parallel.md**: Parity thresholds (correlation ≥0.9995, sum_ratio 0.99–1.01)

### Architecture & Design
- **docs/architecture/detector.md:35**: BEAM/SAMPLE pivot formulas (meter-based geometry)
- **docs/development/c_to_pytorch_config_map.md:42**: Implicit pivot/unit rules (twotheta→SAMPLE, distance→BEAM)
- **docs/debugging/debugging.md:24**: Parallel trace SOP (trace schema, precision requirements)
- **CLAUDE.md Rule #1**: Hybrid unit system (detector meters, physics Å)
- **CLAUDE.md Rule #11**: C-code reference template (mandatory docstrings)
- **CLAUDE.md Rule #12**: Misset rotation pipeline (apply before phi)
- **CLAUDE.md Rule #13**: Reciprocal recalculation for metric duality

### Testing Strategy
- **docs/development/testing_strategy.md §1.4**: PyTorch device/dtype discipline (CPU+CUDA smoke tests)
- **docs/development/testing_strategy.md §2.5**: Parallel validation matrix (AT-PARALLEL mapping, canonical commands)

### C-Code References
- **golden_suite_generator/nanoBragg.c:2050-2199**: MOSFLM matrix pipeline (load, scale, misset, cross products, real reconstruction, reciprocal regeneration)
- **golden_suite_generator/nanoBragg.c:3006-3098**: φ rotation loop (ap/bp/cp assignment, rotation matrix application)

### PyTorch Implementation
- **src/nanobrag_torch/models/crystal.py:568-780**: `compute_cell_tensors` MOSFLM path
- **src/nanobrag_torch/models/crystal.py:1000-1050**: `get_rotated_real_vectors` (φ rotation application)
- **src/nanobrag_torch/utils/geometry.py:91**: `unitize` helper (spindle normalization)

### Prior Evidence Artifacts
- **Phase L3f**: `rot_vector_comparison.md` (component-level deltas, +6.8% b_Y drift quantified)
- **Phase L3g**: `spindle_audit.log` (H1 ruled out, spindle is exact unit vector)
- **Phase L3h**: `mosflm_matrix_probe_output.log` (H2 ruled out, V_actual correct to O(1e-11) Å³)
- **Phase L3i**: `mosflm_matrix_diff.md` (H3 ruled out, b_Y matches at φ=0 to O(1e-7) Å)
- **Supervisor context**: `input.md` 2025-10-07, `prompts/supervisor.md:18`

## Implementation Notes

### Hypothesis H5 Investigation Path

**Suspected Root Cause:**
Rotation matrix construction or application differs between C (`nanoBragg.c:3006-3098`) and PyTorch (`Crystal.get_rotated_real_vectors`).

**Diagnostic Steps (Before Fix):**
1. Add `TRACE_C`/`TRACE_PY` for rotation matrix R at φ=0.05
2. Compare R component-by-component (should be 3×3 identity at φ=0, non-trivial at φ>0)
3. Log pre-rotation base vectors (a0, b0, c0) and post-rotation (ap, bp, cp)
4. Verify rotation axis (spindle_axis) is identical in both implementations
5. Check rotation direction (CW vs CCW convention)

**Expected Fix Location:**
- `src/nanobrag_torch/models/crystal.py:1000-1050`
- Likely involves `rotate_vector_around_axis` call or rotation matrix construction
- May require reordering axis/angle arguments to match C convention

**Verification After Fix:**
- Rerun VG-1 (per-φ traces) → b_Y drift vanishes
- Rerun VG-3 (nb-compare) → correlation ≥0.9995, sum_ratio parity
- All VG-4 thresholds met

### Implementation Timing

**Pre-Implementation Requirements:**
- This checklist complete and reviewed
- Phase L3j.1 complete (mosflm_matrix_correction.md updated) ✅
- Phase L3j.2 complete (this file) ⏸️
- Phase L3j.3 complete (plan/fix_plan updated) ⏸️

**Implementation Loop:**
- Execute code changes with C-code docstrings
- Run verification gates VG-1 through VG-4
- Update documentation (VG-5)
- Commit with message format: `[CLI-FLAGS-003 L3j] Fix φ rotation parity (H5) - VG gates passed`

**Post-Implementation:**
- Proceed to Phase L4 (supervisor command parity rerun)
- Archive this checklist with completion timestamp
- Update PROJECT_STATUS.md if milestone reached

## Checklist Status

- **Created:** 2025-10-07 (ralph loop i=94, CLI-FLAGS-003 Phase L3j documentation)
- **Last Updated:** 2025-11-21 (galph loop; VG-2 confirmed)
- **Completion:** ⏸️ VG-1/VG-3/VG-4/VG-5 pending; VG-2 complete via Attempt #98
- **Owner:** Implementation loop (post-L3k.3 coordination)

**Next Step:** Continue Phase L3k.3 by regenerating per-φ traces (VG-1) and nb-compare/trace deltas (VG-3/VG-4), then close documentation gates (VG-5) before logging L3k.4.
