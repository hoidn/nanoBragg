# Phase H5 Parity Summary

**Date:** 2025-10-24 (refreshed from 2025-10-22)
**Task:** CLI-FLAGS-003 Phase H5c — Capture post-unit-fix PyTorch traces after Attempt #33
**Goal:** Verify whether Attempt #33's beam-center mm→m conversion resolved the pix0 discrepancy, then assess readiness for Phase K normalization work.

## Implementation Snapshot
✅ **Updated 2025-10-24 (Attempt #35):** Fresh PyTorch trace captured post-Attempt #33 unit fix. **Critical finding: Attempt #33's beam-center mm→m conversion did NOT affect pix0 calculation. Pix0 deltas identical to 2025-10-22 baseline, indicating the underlying pix0 discrepancy remains unresolved.**

### Code Changes (Prior Work)
**File:** `src/nanobrag_torch/models/detector.py`

1. **H5b - Restored custom-vector guard** (Attempt #31, lines ≈518-540):
   - Added `has_custom_vectors = any([...])` helper mirroring C precedence.
   - Gated pix0 override projection with `if pix0_override_tensor is not None and not has_custom_vectors:`.
   - Refreshed comments to cite `reports/2025-10-cli-flags/phase_h5/c_precedence_2025-10-22.md`.

2. **H5e - Beam-center unit correction** (Attempt #33, lines 490-515):
   - Changed BEAM pivot Fbeam/Sbeam calculation to use `self.config.beam_center_f / 1000.0` instead of pixel-based values.
   - Addressed observed 1.1mm ΔF error from 2025-10-22 trace analysis.
   - **Result: Unit fix confirmed effective for CLI tests but did NOT impact pix0 vector in custom-vector scenarios.**

### Regression Test Results
**Command:** `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestCLIPix0Override -v`

**Results:** ✅ **4 passed** (H5b revert validation)
✅ **26 passed** (H5e unit fix validation, all CLI flags)

## Parity Metrics (Phase H5c — 2025-10-24 Post-Attempt #33)

**Command:**
```bash
export NB_C_BIN=./golden_suite_generator/nanoBragg
export KMP_DUPLICATE_LIB_OK=TRUE
export PYTHONPATH=src
python reports/2025-10-cli-flags/phase_h/trace_harness.py \
  --out reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-24/trace_py.log
```

**Pixel:** (slow=1039, fast=685)
**C Baseline:** `reports/2025-10-cli-flags/phase_h5/c_traces/2025-10-22/with_override.log`
**Threshold:** <5e-5 m (<50 μm per component)

### Pix0 Vector Comparison

| Component | C Value (m) | PyTorch (2025-10-24) | Delta (m) | Delta (μm) | Status |
|-----------|-------------|----------------------|-----------|------------|--------|
| pix0_S | -0.216475836205 | -0.216336513669 | +1.393e-04 | +139.3 | ⚠️ **FAIL** |
| pix0_F | 0.216343050492 | 0.215206681073 | -1.136e-03 | -1136.4 | ⚠️ **FAIL** |
| pix0_O | -0.230192414301 | -0.230198008547 | -5.594e-06 | -5.6 | ✅ **PASS** |
| **Magnitude** | — | — | **1.145e-03** | **1144.9** | ⚠️ **FAIL** |

### Detector Basis Vectors

| Vector | C Value | PyTorch Value | Delta | Status |
|--------|---------|---------------|-------|--------|
| fdet | 0.999982, -0.005998, -0.000118 | 0.999982, -0.005998, -0.000118 | 0.0 | ✅ **PASS** |
| sdet | -0.005998, -0.99997, -0.004913 | -0.005998, -0.99997, -0.004913 | 0.0 | ✅ **PASS** |

### Physics Calculation Metrics

| Variable | C Value | PyTorch Value (2025-10-24) | Delta | Notes |
|----------|---------|----------------------------|-------|-------|
| hkl_frac | (not logged) | (2.098, 2.017, -12.871) | N/A | ⏳ Awaiting C instrumentation |
| hkl_rounded | (not logged) | (2, 2, -13) | N/A | |
| F_latt_a | (not logged) | -3.294 | N/A | ⏳ Phase K1 parity |
| F_latt_b | (not logged) | 10.815 | N/A | |
| F_latt_c | (not logged) | -1.823 | N/A | |
| F_latt (product) | (not logged) | 64.949 | N/A | |
| F_cell | (not logged) | 300.58 | N/A | HKL interpolation value |
| I_before_scaling | (not logged) | 3.811e8 | N/A | |
| I_pixel_final | (not logged) | 0.003838 | N/A | |
| omega_pixel_sr | (not logged) | 4.169e-07 | N/A | |
| polar | (not logged) | 1.0 | N/A | Confirms Attempt #26 fix |

### Critical Findings

1. **⚠️ Attempt #33 Had NO Impact on Pix0:**
   - Pix0 deltas are **identical** to 2025-10-22 baseline (before Attempt #33).
   - ΔF remains at -1136.4 μm (1.136 mm), ΔS at +139.3 μm.
   - This indicates the beam-center mm→m fix targeted a **different code path** than the one computing pix0 in custom-vector scenarios.

2. **✅ Detector Basis Vectors Match Perfectly:**
   - fdet and sdet vectors identical to C, confirming detector orientation is correct.
   - Rotation matrix application validated.

3. **⚠️ Pix0 Discrepancy Root Cause Unknown:**
   - The 1.1mm fast-axis error persists despite:
     - Custom-vector guard restoration (H5b)
     - Beam-center unit conversion fix (H5e)
     - All CLI tests passing
   - Hypothesis: Pix0 calculation in `_calculate_pix0_vector()` may have a **separate unit conversion or pivot-mode logic error** not addressed by H5e.

4. **🔍 Missing C Instrumentation:**
   - F_latt components, fractional h/k/l, and per-pixel intensities not logged in C trace.
   - Phase K1 will require additional C printf statements for lattice factor validation.

## Immediate Analysis & Recommendations

### Pix0 Delta Pattern Analysis
The persistent error pattern (S: +139μm, F: -1136μm, O: -5.6μm) suggests:
- **Systematic bias in fast-axis calculation** (10× larger than slow-axis error)
- Likely causes:
  1. Pivot mode (SAMPLE) calculation differs from C despite identical detector_pivot setting
  2. Custom vector projection math has a unit conversion error
  3. MOSFLM +0.5 pixel offset applied at wrong stage in pix0 calculation
  4. Beam-center values used in pix0 calculation come from a different source than those fixed in H5e

### Phase K Readiness Assessment
⚠️ **BLOCKED** - The 1.1mm pix0 error will cascade into:
- Incorrect Miller index calculations (h/k/l off by several tenths)
- Invalid F_latt comparisons (already evident: C values unknown, PyTorch=64.949)
- Unreliable intensity scaling validation

**Recommendation:** **Pause Phase K work and open Phase H6 to resolve pix0 discrepancy before resuming normalization.**

## Next Steps (Proposed Phase H6)

1. **H6a - Instrument pix0 calculation path:**
   - Add targeted printf statements in `Detector._calculate_pix0_vector()` showing:
     - Input beam_center values (pre- and post-conversion)
     - Pivot mode logic flow
     - MOSFLM offset application
     - Final pix0 components

2. **H6b - Generate comparative pix0 trace:**
   - Run instrumented Python with same parameters as C
   - Identify first divergence point in pix0 calculation chain

3. **H6c - Fix root cause:**
   - Apply corrective logic based on divergence analysis
   - Verify ΔF, ΔS, ΔO all fall below 50μm threshold

4. **H6d - Rerun H5c:**
   - Capture post-H6c PyTorch traces
   - Confirm pix0 parity before Phase K resumes

## Verification Status

✅ **Trace captured** — 2025-10-24 PyTorch trace in `py_traces/2025-10-24/trace_py.stdout`
✅ **Delta analysis complete** — Metrics computed and documented above
⚠️ **Parity NOT achieved** — Pix0 errors exceed threshold (ΔF=-1136μm, ΔS=+139μm)
⚠️ **Attempt #33 ineffective** — Beam-center fix did not impact pix0 calculation
🔄 **Phase H6 required** — Additional debugging needed before Phase K can proceed

## Artifacts

- **C Baseline Trace:** `reports/2025-10-cli-flags/phase_h5/c_traces/2025-10-22/with_override.log`
- **PyTorch Trace (2025-10-24):** `reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-24/trace_py.stdout`
- **C Precedence Proof:** `reports/2025-10-cli-flags/phase_h5/c_precedence_2025-10-22.md`
- **Implementation Notes:** `reports/2025-10-cli-flags/phase_h5/implementation_notes.md`
- **Delta Analysis:** Inline above (Pix0 Vector Comparison table)

### Phase H6 Diagnostics

- **2025-10-26: Phase H6c first divergence recorded** (beam_center_m logged in mm vs m).
  - **Root cause:** PyTorch trace outputs beam_center_m values in millimeters while C logs them in meters (1000× scale difference).
  - **Impact:** This is a trace logging issue, NOT a calculation error. Fclose/Sclose match exactly, confirming the actual pix0 calculation uses correct units.
  - **Key finding:** The 1.1mm pix0 discrepancy persists even though Fclose/Sclose are identical, suggesting the divergence occurs in a different part of the pix0 computation (term_fast/term_slow/term_close combination or missing CUSTOM convention transform).
  - **Artifacts:** See `phase_h6/analysis.md`, `phase_h6/trace_diff.txt` for detailed comparison.
  - **Metrics Table:**

| Variable | C (m) | PyTorch (logged) | PyTorch (corrected to m) | Issue |
| --- | --- | --- | --- | --- |
| Xclose | 0.000211818 | 0.217742295 (mm logged as m) | 0.000217742 | Trace unit label |
| Yclose | 0.000217322 | 0.21390708 (mm logged as m) | 0.000213907 | Trace unit label |
| Fclose_m | 0.217742295 | 0.217742295 | — | ✅ Exact match |
| Sclose_m | 0.21390708 | 0.21390708 | — | ✅ Exact match |

### Phase H6e: Detector Pivot Mismatch Confirmed (2025-10-06)

**Critical Finding:** Evidence loop confirmed PyTorch uses **BEAM pivot** while C uses **SAMPLE pivot** for the supervisor command.

**Evidence:**
```
C trace: "pivoting detector around sample"
PyTorch: DetectorPivot.BEAM (extracted via CLI config inspection)
```

**Impact on Pix0:**
- BEAM pivot formula: `pix0 = -Fbeam·fdet - Sbeam·sdet + distance·beam` (after rotations)
- SAMPLE pivot formula: `pix0 = -Fclose·fdet - Sclose·sdet + close_distance·odet`, then rotate pix0
- **Different formulas → different pix0 vectors → cascading geometry errors**

**Root Cause:**
- `DetectorConfig` pivot selection does not force SAMPLE pivot when custom detector vectors are present
- Missing the C code's implicit rule: *custom vectors → SAMPLE pivot*

**Specification References:**
- `specs/spec-a-cli.md`: Custom detector basis vectors SHALL force SAMPLE pivot mode
- `docs/architecture/detector.md` §5.2: Pivot checklist item #3 (custom geometry override)

**Resolution Path:**
- Phase H6f: Implement custom-vector-to-SAMPLE-pivot forcing rule
- Phase H6g: Revalidate pix0 traces (require |Δpix0| < 5e-5 m)

**Detailed Evidence:** See `reports/2025-10-cli-flags/phase_h6/pivot_parity.md`

## References
- Plan checkpoint: `plans/active/cli-noise-pix0/plan.md` Phase H5/H5c/H6c/H6e
- Fix plan entry: `docs/fix_plan.md` §[CLI-FLAGS-003] Attempt #35 (H5c), Attempt #38 (H6c), Attempt #39 (H6e this loop)
- Unit fix commit: Attempt #33 (commit 831b670, H5e task)
- Custom-vector revert: Attempt #31 (H5b task)
- Phase H6c analysis: `reports/2025-10-cli-flags/phase_h6/analysis.md`
- **Phase H6e pivot evidence:** `reports/2025-10-cli-flags/phase_h6/pivot_parity.md`
