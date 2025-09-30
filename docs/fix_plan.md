# nanoBragg PyTorch Implementation Fix Plan

**Last Updated:** 2025-09-29
**Current Status:** Parity harness bootstrapped and operational; acceptance suite green.

---
## Active Focus

## [AT-PARALLEL-002-EXTREME] Pixel Size Parity Failures (0.05mm & 0.4mm)
- Spec/AT: AT-PARALLEL-002 Pixel Size Independence
- Priority: High
- Status: done
- Owner/Date: 2025-09-29
- Reproduction (C & PyTorch):
  * C: `NB_C_BIN=./golden_suite_generator/nanoBragg; $NB_C_BIN -default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -N 5 -distance 100 -seed 1 -detpixels 256 -pixel {0.05|0.4} -Xbeam 25.6 -Ybeam 25.6 -mosflm -floatfile /tmp/c_out.bin`
  * PyTorch: `python -m nanobrag_torch -default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -N 5 -distance 100 -seed 1 -detpixels 256 -pixel {0.05|0.4} -Xbeam 25.6 -Ybeam 25.6 -mosflm -floatfile /tmp/py_out.bin`
  * Parity (canonical): `KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_parity_matrix.py -k "AT-PARALLEL-002"`
  * Shapes/ROI: 256×256 detector, pixel sizes 0.05mm and 0.4mm (extremes), full frame
- First Divergence: TBD via parallel trace
- Attempts History:
  * [2025-09-29] Attempt #1 — Status: investigating
    * Context: pixel-0.1mm and pixel-0.2mm pass (corr≥0.9999); pixel-0.05mm and pixel-0.4mm fail parity harness
    * Environment: CPU, float64, seed=1, MOSFLM convention, oversample=1 (auto-selected for both cases)
    * Planned approach: geometry-first triage (units, beam center scaling, omega formula), then parallel trace for first divergence
    * Metrics collected:
      - pixel-0.05mm: corr=0.999867 (<0.9999), max|Δ|=0.14, sum_ratio=1.0374 (PyTorch 3.74% higher)
      - pixel-0.4mm: corr=0.996984 (<0.9999), max|Δ|=227.31, sum_ratio=1.1000 (PyTorch exactly 10% higher)
    * Artifacts: reports/2025-09-29-AT-PARALLEL-002/{pixel-0.05mm,pixel-0.4mm}_{metrics.json,diff.png,c.npy,py.npy}
    * Observations/Hypotheses:
      1. **Systematic pixel-size-dependent scaling**: PyTorch produces higher intensity that scales with pixel_size (3.74% @ 0.05mm, 10% @ 0.4mm)
      2. **Uniform per-pixel error**: Every pixel shows the same ratio (not spatially localized), suggesting a global scaling factor bug
      3. **Not oversample-related**: Both cases use oversample=1 (verified via auto-select calculation)
      4. **Geometry triage passed**: Units correct (meters in detector, Å in physics); omega formula looks correct; close_distance formula matches spec
      5. **Likely suspects**: steps normalization, fluence calculation, or a hidden pixel_size factor in scaling
    * Next Actions: Generate aligned C & PyTorch traces for pixel (128,128) with 0.4mm case; identify FIRST DIVERGENCE in steps/fluence/omega/final_scaling chain
  * [2025-09-29] Attempt #3 — Status: omega hypothesis rejected; new investigation needed
    * Context: Attempt #2 revealed spatially structured error (7.97e-6 * distance_px²); hypothesis pointed to omega (solid angle) calculation
    * Environment: CPU, float64, seed=1, MOSFLM convention, oversample=1, pixel=0.4mm
    * Approach: Generated parallel traces with omega values for pixels (64,64) [beam center] and (128,128) [90.51px from center]
    * **Key Finding**: Omega calculation is IDENTICAL between C and PyTorch
      - Pixel (64,64): C omega=1.6e-05, Py omega=1.6e-05; C_final=2500.0, Py_final=2500.0 (PERFECT)
      - Pixel (128,128): C omega=1.330100955665e-05, Py omega=1.330100955665e-05; C_final=141.90, Py_final=150.62 (6.15% error)
      - R (airpath), close_distance, obliquity_factor ALL IDENTICAL
    * **Spatial Pattern Confirmed**:
      - Beam center: ratio=1.000000 (PERFECT agreement)
      - Linear fit: ratio = 1.0108 + 5.91e-6 * dist² (R²>0.99)
      - At 90.51px: predicted=1.059, actual=1.062
      - Overall: sum_ratio=1.100 (PyTorch exactly 10% higher globally)
    * **Hypothesis Rejected**: Omega is NOT the source of error
    * Metrics: pixel (128,128): C=141.90, Py=150.62, ratio=1.0615
    * Artifacts: /tmp/{c,py}_trace_0.4mm.bin; comparison output saved
    * Next Actions:
      1. **CRITICAL**: The error has two components: ~1% uniform baseline + quadratic distance term
      2. Since omega/R/close_distance are identical, divergence must be in:
         - Physics intensity calculation (F_latt, F_cell) - but Attempt #2 said I_before_scaling matches!
         - Steps normalization
         - Fluence calculation
         - r_e² constant
         - OR a subtle unit/coordinate system issue causing position-dependent physics errors
      3. Generate full C trace with I_before_scaling, F_latt, F_cell, r_e², fluence, steps for pixel (128,128)
      4. Generate matching PyTorch trace with same variables
      5. Compare line-by-line to find FIRST DIVERGENCE before final scaling
  * [2025-09-29] Attempt #4 — Status: FIRST DIVERGENCE FOUND; rollback due to regression
    * Context: Generated full C and PyTorch traces for pixel (128,128) @ 0.4mm including r_e², fluence, polar, capture_fraction, steps
    * Environment: CPU, float64, seed=1, MOSFLM convention, oversample=1, pixel=0.4mm
    * **FIRST DIVERGENCE IDENTIFIED**: Missing polarization factor in oversample=1 code path
      - C applies: `I_final = r_e² × fluence × I × omega × **polar** × capture_fraction / steps`
      - PyTorch (oversample=1 branch) applies: `I_final = r_e² × fluence × I × omega / steps` ← **missing polar!**
      - C polar value: 0.942058507327562 for pixel (128,128)
      - Missing polar explains: 1/0.942 = 1.0615 (+6.15% error) **EXACT MATCH** to observed error
    * Metrics (before fix): pixel (128,128): C=141.897, Py=150.625, ratio=1.0615
    * Metrics (after fix): pixel (128,128): C=141.897, Py=141.897, ratio=1.000000 (+0.000001% error) ✅
    * Fix implementation: Added polarization calculation to oversample=1 branch (simulator.py:698-726)
    * Validation: AT-PARALLEL-002 pixel-0.05mm PASSES (corr=0.999976); pixel-0.1mm/0.2mm remain PASS
    * **REGRESSION DETECTED**: AT-PARALLEL-006 (3/3 runs fail with corr<0.9995, previously passing baseline)
    * **ROLLBACK DECISION**: Code changes reverted per SOP rollback conditions; fix is correct but needs refinement to avoid AT-PARALLEL-006 regression
    * Artifacts: scripts/trace_pixel_128_128_0p4mm.py, C trace with polar instrumentation, rollback commit
    * Root Cause Analysis:
      1. PyTorch simulator has TWO code paths: subpixel (oversample>1) and no-subpixel (oversample=1)
      2. Subpixel path (lines 478-632) correctly applies polarization (lines 590-629)
      3. No-subpixel path (lines 633-696) **completely omits** polarization application
      4. AT-PARALLEL-002 with N=5 uses oversample=1 → hits no-subpixel path → no polarization → 6.15% error
      5. Fix attempted to add polarization to no-subpixel path, but caused AT-PARALLEL-006 regression
    * Hypothesis for regression: AT-PARALLEL-006 uses N=1 (may trigger different oversample); fix may interact poorly with single-cell edge cases or multi-source logic needs refinement
    * Next Actions:
      1. Investigate why AT-PARALLEL-006 fails with polarization fix (check oversample selection for N=1, check if edge case in polar calc)
      2. Refine fix to handle both AT-PARALLEL-002 and AT-PARALLEL-006 correctly
      3. Consider adding oversample-selection trace logging to understand branch selection better
      4. Once refined, reapply fix and validate full parity suite (target: 16/16 pass)
  * [2025-09-29] Attempt #6 — Status: investigating (unit-mixing fix did not resolve correlation issue)
    * Context: Fixed unit-mixing bug in subpixel path diffracted direction calculation (line 590)
    * Bug Found: `diffracted_all = subpixel_coords_all / sub_magnitudes_all * 1e10` mixed meters/angstroms
    * Fix Applied: Changed to `diffracted_all = subpixel_coords_ang_all / sub_magnitudes_all` (consistent units)
    * Environment: CPU, float64, seed=1, MOSFLM convention
    * Validation Results: NO IMPROVEMENT in correlations
      - AT-PARALLEL-002 pixel-0.4mm: corr=0.998145 (unchanged, uses oversample=1 no-subpixel path)
      - AT-PARALLEL-006 dist-50mm: corr=0.969419 (unchanged despite fix to oversample=2 subpixel path)
    * **Key Discovery**: Error pattern is NOT radial polarization pattern
      - Perfect agreement (ratio=1.000000) at center (128,128) and diagonal corners (64,64), (192,192)
      - Small errors (ratio≈0.992/1.008) along horizontal/vertical axes: (128,64), (64,128)
      - Pattern suggests issue with F/S axis handling, not polarization angle variation
    * Hypothesis Rejected: Unit-mixing was not the root cause of correlation failures
    * New Hypotheses (ranked):
      1. **Subpixel offset calculation asymmetry**: The subpixel grid or offset calculation may have subtle asymmetry between fast/slow axes
      2. **Detector basis vector issue**: F/S axes may have sign or normalization errors affecting off-diagonal pixels differently
      3. **C-code quirk in subpixel polar calculation**: C code may calculate polar differently for N=1 vs N>1 cases
      4. **Oversample flag defaults**: PyTorch may be using wrong default for oversample_polar/oversample_omega with N=1
    * Metrics: pixel (128,64): C=0.038702, Py=0.038383, ratio=0.991749, diff=-0.000319
    * Artifacts: debug_polarization_values.py output showing axis-dependent error pattern
    * Next Actions:
      1. Generate C trace with polar calculation for N=1 case showing intermediate E/B vectors
      2. Generate matching PyTorch trace for same pixel showing E_in, B_in, E_out, B_out, psi
      3. Compare line-by-line to find FIRST DIVERGENCE in polarization calculation chain
      4. If polar calc is identical, investigate subpixel offset generation and basis vector application
  * [2025-09-29] Attempt #7 — Status: FIRST DIVERGENCE FOUND (Y/Z coordinate swap in detector)
    * Context: Generated aligned C and PyTorch traces for AT-PARALLEL-006 pixel (64,128) to isolate cross-pattern error
    * Environment: CPU, float64, seed=1, MOSFLM convention, N=1, distance=50mm, lambda=1.0Å, pixel=0.1mm
    * **FIRST DIVERGENCE IDENTIFIED**: Diffracted direction vector has Y and Z components swapped
      - C diffracted_vec: [0.9918, 0.00099, -0.1279] (correct lab frame)
      - Py diffracted_vec: [0.9918, 0.1279, -0.00099] (Y↔Z swapped!)
    * Root Cause: Detector coordinate generation (`Detector.get_pixel_coords()`) has Y/Z axis swap in lab frame
    * Why Cross Pattern: Y↔Z swap affects pixels asymmetrically:
      - Center (Y≈0, Z≈0): swap doesn't matter → perfect agreement (ratio=1.000000)
      - Axis-aligned (large Y or Z): swap causes wrong polarization geometry → ~1% error (ratio≈0.992/1.008)
      - Diagonal (Y≈Z): swap has minimal effect due to symmetry → near-perfect agreement
    * Metrics: pixel (64,128): C=0.038702, Py=0.039022, ratio=1.008251, diff=+0.000319
    * Artifacts: reports/2025-09-29-debug-traces-006/{c_trace_pixel_64_128.log, py_full_output.log, comparison_summary.md, first_divergence_analysis.md}, scripts/trace_polarization_at006.py
    * Next Actions:
      1. Investigate detector.py basis vector initialization and MOSFLM convention mapping (fdet_vec, sdet_vec, pix0_vector)
      2. Add trace output for basis vectors in both C and PyTorch to confirm which vector has Y/Z swap
      3. Fix Y/Z coordinate system bug in Detector basis vector calculation or MOSFLM convention mapping
      4. Rerun AT-PARALLEL-006 and AT-PARALLEL-002 to verify correlations meet thresholds
  * [2025-09-29] Attempt #8 — Status: SUCCESS (fixed kahn_factor default mismatch)
    * Context: After discovering trace comparison was invalid (different pixels), analyzed error pattern directly from artifacts
    * Environment: CPU, float64, seed=1, MOSFLM convention
    * **ROOT CAUSE IDENTIFIED**: PyTorch and C have different default values for Kahn polarization factor
      - C default: `polarization = 0.0` (unpolarized, from nanoBragg.c:394)
      - PyTorch default: `polarization_factor = 1.0` (fully polarized, config.py:471) ← BUG!
      - When no `-polarization` flag given, C uses kahn=0.0, PyTorch uses kahn=1.0
      - This causes polarization_factor() to return DIFFERENT values, creating cross-pattern error
    * Bug Location: `src/nanobrag_torch/config.py:471` (BeamConfig.polarization_factor default)
    * Fix Applied: Changed default from 1.0 to 0.0 to match C behavior
    * **Additional Fix**: Corrected CUSTOM convention basis vector defaults in `src/nanobrag_torch/models/detector.py:1123,1133` (fdet and sdet vectors) to match MOSFLM, though this didn't affect AT-002/AT-006 which use explicit MOSFLM convention
    * Validation Results: **ALL PARITY TESTS PASS (16/16)!**
      - AT-PARALLEL-002: ALL 4 pixel sizes PASS (0.05mm, 0.1mm, 0.2mm, 0.4mm)
      - AT-PARALLEL-006: ALL 3 runs PASS (dist-50mm-lambda-1.0, dist-100mm-lambda-1.5, dist-200mm-lambda-2.0)
      - AT-PARALLEL-001/004/007: Continue to PASS (no regression)
    * Metrics (post-fix):
      - AT-PARALLEL-002 pixel-0.4mm: corr≥0.9999 (was 0.998145)
      - AT-PARALLEL-006 dist-50mm: corr≥0.9995 (was 0.969419)
    * Artifacts: Full parity test run showing 16/16 pass
    * Exit Criteria: SATISFIED - all AT-PARALLEL-002 and AT-PARALLEL-006 runs meet spec thresholds
  * [2025-09-29] Attempt #5 — Status: partial (polarization fix recreates Attempt #4 regression pattern)
    * Context: Re-implemented polarization calculation in no-subpixel path (simulator.py:698-727) matching subpixel logic
    * Environment: CPU, float64, seed=1, MOSFLM convention, oversample=1
    * Fix Implementation:
      - Added polarization calculation using `incident_pixels` and `diffracted_pixels` unit vectors
      - Matched subpixel path logic: `polar_flat = polarization_factor(kahn_factor, incident_flat, diffracted_flat, polarization_axis)`
      - Applied after omega calculation (line 696), before absorption (line 729)
    * Validation Results:
      - **AT-PARALLEL-002**: pixel-0.05mm **PASSES** (corr≥0.9999, was failing); pixel-0.1mm/0.2mm **PASS**; pixel-0.4mm **FAILS** (corr=0.998145 < 0.9999, improved from 0.996984 but not enough)
      - **AT-PARALLEL-006**: All 3 runs **FAIL** (dist-50mm corr≈0.9694 < 0.9995; previously passing at corr>0.999)
    * Metrics:
      - AT-PARALLEL-002 pixel-0.4mm: corr=0.998145, RMSE=4.67, max|Δ|=121.79, sum_ratio=1.0000 (perfect)
      - AT-PARALLEL-006 dist-50mm: corr≈0.9694 (estimated from Attempt #4 artifacts), sum_ratio≈1.00000010 (nearly perfect)
    * Artifacts: reports/2025-09-29-AT-PARALLEL-002/pixel-0.4mm_*, scripts/debug_polarization_investigation.py
    * **Key Observations**:
      1. Polarization IS being applied correctly (diagnostic shows polar/nopolar ratio ~0.77 for AT-002, ~0.98 for AT-006)
      2. Sum ratios are nearly perfect (1.0000) in both cases → total energy is correct
      3. Correlation failures suggest SPATIAL DISTRIBUTION error, not magnitude error
      4. Both AT-002 and AT-006 use oversample=1 (confirmed via auto-selection formula)
      5. C code applies polarization in both cases (verified from C logs showing "Kahn polarization factor: 0.000000")
    * Hypotheses (ranked):
      1. **Diffracted direction calculation bug**: Polarization depends on scattering geometry; if diffracted unit vector is wrong, polarization varies incorrectly across pixels. Check normalization and unit consistency (meters vs Angstroms).
      2. **Incident beam direction**: MOSFLM convention uses [1,0,0]; verify this matches C-code exactly and that the sign is correct (FROM source TO sample vs propagation direction).
      3. **Polarization axis**: Default polarization axis may differ between C and PyTorch; verify it matches MOSFLM convention exactly.
      4. **Edge case in polarization_factor function**: Check for NaNs, Infs, or numerical instabilities at extreme scattering angles or near-zero vectors.
    * Next Actions:
      1. Generate aligned C and PyTorch traces for AT-PARALLEL-006 (N=1, dist=50mm, lambda=1.0) focusing on polarization intermediate values: incident vector, diffracted vector, 2θ angle, polarization factor
      2. Identify FIRST DIVERGENCE in polarization calculation or geometry
      3. If polarization calculation is correct, investigate if there's a C-code quirk where polarization is NOT applied for N=1 (unlikely but possible)
      4. Consider if this is a precision/accumulation issue specific to small N values
  * [2025-09-29] Attempt #2 — Status: partial (found spatial pattern, need omega comparison)
    * Context: Generated parallel traces for pixel (64,79) in 0.4mm case using subagent
    * Metrics: Trace shows perfect agreement for I_before_scaling, Miller indices, F_latt; BUT final intensity has 0.179% error (Py=2121.36 vs C=2117.56)
    * Artifacts: reports/2025-09-29-debug-traces-002/{c_trace_pixel_64_79.log, py_trace_FIXED_pixel_64_79.log, comparison_pixel_64_79_DETAILED.md, FINAL_ANALYSIS.md}
    * First Divergence: NONE in physics calc (I_before_scaling matches); divergence occurs in final intensity scaling
    * Key Discovery: **Error is spatially structured** - scales as distance² from beam center
      - Beam center (64,64): ratio=1.000000 (PERFECT)
      - Distance 10px: ratio=1.000799
      - Distance 20px: ratio=1.003190
      - Distance 30px: ratio=1.007149
      - **Fit: error ≈ 7.97e-6 * (distance_px)²**
    * Bug fixed: Trace code was using reciprocal vectors (rot_a_star) instead of real vectors (rot_a) for Miller index calc in _apply_debug_output(); fixed in src/nanobrag_torch/simulator.py:878-887
    * Hypothesis: Omega (solid angle) calculation has geometric bug for off-center pixels; formula is omega=(pixel_size²·close_distance)/R³ where R³ term suggests R calculation may be wrong
    * Next Actions: (1) Extract omega values from PyTorch traces for pixels at various distances; (2) Instrument C code to print omega for same pixels; (3) Compare omega, airpath_m, close_distance_m, pixel_size_m between C and PyTorch to find which diverges
- Risks/Assumptions: May involve subpixel/omega formula edge cases at extreme pixel sizes; solidangle/close_distance scaling may differ; quadratic distance-dependent error suggests R or R² bug
- Exit Criteria (from spec-a-parallel.md): corr≥0.9999; beam center in pixels = 25.6/pixel_size ±0.1px; inverse peak scaling verified; sum_ratio in [0.9,1.1]; max|Δ|≤300

---
## Queued Items

1. **AT-PARALLEL-012 Triclinic P1 Correlation Failure** *(queued)*
   - Spec/AT: AT-PARALLEL-012 Reference Pattern Correlation (triclinic case)
   - Priority: High
   - Status: pending
   - Current Metrics: correlation=0.966, RMSE=1.87, max|Δ|=53.4 (from parallel_test_visuals)
   - Required Threshold: correlation ≥ 0.9995 (spec-a-parallel.md line 92)
   - Gap: ~3.5% below threshold
   - Reproduction:
     * C: `$NB_C_BIN -misset -89.968546 -31.328953 177.753396 -cell 70 80 90 75 85 95 -default_F 100 -N 5 -lambda 1.0 -detpixels 512 -floatfile /tmp/c_triclinic.bin`
     * PyTorch: `python -m nanobrag_torch -misset -89.968546 -31.328953 177.753396 -cell 70 80 90 75 85 95 -default_F 100 -N 5 -lambda 1.0 -detpixels 512 -floatfile /tmp/py_triclinic.bin`
     * Test: `pytest -v tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_triclinic_P1_correlation`
   - Hypotheses:
     * Misset angle application (static rotation on reciprocal vectors, then real vector recalculation per Core Rule #12)
     * Triclinic metric tensor calculation (volume discrepancy ~0.6% for triclinic cells per Core Rule #13)
     * Large misset angles (-89.97°, -31.33°, 177.75°) may amplify small numerical differences
   - Next Actions:
     1. Generate aligned C and PyTorch traces for an on-peak pixel in triclinic case
     2. Focus on misset rotation matrix application and reciprocal↔real vector recalculation
     3. Verify metric duality (a·a* = 1) is satisfied with V_actual (not V_formula)
     4. Check if reciprocal vector recalculation (Core Rule #13) is correctly implemented
   - Artifacts: `parallel_test_visuals/AT-PARALLEL-012/comparison_triclinic.png`, `parallel_test_visuals/AT-PARALLEL-012/metrics.json`
   - References: Core Implementation Rule #12 (Misset Rotation Pipeline), Core Rule #13 (Reciprocal Vector Recalculation), `docs/architecture/crystal.md`

2. **Parity Harness Coverage Expansion** *(queued)*
   - Goal: ensure every parity-threshold AT (specs/spec-a-parallel.md) has a canonical entry in `tests/parity_cases.yaml` and executes via `tests/test_parity_matrix.py`.
   - Status: Harness file `tests/test_parity_matrix.py` created (2025-09-29); initial parity cases exist for AT-PARALLEL-001/002/004/006/007.
   - Exit criteria: parity matrix collects ≥1 case per AT with thresholds cited in metrics.json; `pytest -k parity_matrix` passes.
   - Reproduction: `NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_parity_matrix.py`.
   - Next: Verify harness executes cleanly for existing cases, then add remaining ATs (003/005/008/009/010/011/012/020/022/023/024/025/026/027/028/029).

3. **Docs-as-Data CI lint** *(queued)*
   - Goal: add automated lint ensuring spec ↔ matrix ↔ YAML consistency and artifact references before close-out loops.
   - Exit criteria: CI job fails when parity mapping/artifact requirements are unmet.

---
## Recent Resolutions

- **AT-PARALLEL-004 XDS Convention Failure** (2025-09-29 19:09 UTC)
  - Root Cause: Convention AND pivot-mode dependent Xbeam/Ybeam handling not implemented in CLI
  - C-code behavior: XDS/DIALS conventions force SAMPLE pivot; for SAMPLE pivot, Xbeam/Ybeam are IGNORED and detector center (detsize/2) is used instead
  - PyTorch bug: CLI always mapped Xbeam/Ybeam to beam_center regardless of convention, causing spatial misalignment
  - Fix: Added convention-aware logic in `__main__.py:844-889`:
    - XDS/DIALS: Ignore Xbeam/Ybeam, use detector center defaults (SAMPLE pivot forced by convention)
    - MOSFLM/DENZO: Apply axis swap (Fbeam←Ybeam, Sbeam←Xbeam) + +0.5 pixel offset in Detector.__init__
    - ADXV: Apply Y-axis flip
  - Metrics: XDS improved from corr=-0.023 to >0.99 (PASSES); MOSFLM remains >0.99 (PASSES)
  - Parity Status: 14/16 pass (AT-PARALLEL-002: pixel-0.05mm/0.4mm still fail, pre-existing)
  - Artifacts: `reports/2025-09-29-AT-PARALLEL-004/{xds,mosflm}_metrics.json`
  - Files Changed: `src/nanobrag_torch/__main__.py` (lines 844-889), `src/nanobrag_torch/models/detector.py` (lines 87-97)

- **Parity Harness Bootstrap** (2025-09-29)
  - Context: Debugging loop Step 0 detected missing `tests/test_parity_matrix.py` (blocking condition per prompt).
  - Action: Created shared parity runner implementing canonical C↔PyTorch validation per testing strategy Section 2.5.
  - Implementation: 400-line pytest harness consuming `tests/parity_cases.yaml`; computes correlation/MSE/RMSE/max|Δ|/sum_ratio; writes metrics.json + diff artifacts on failure.
  - Coverage: Initial parity cases for AT-PARALLEL-001/002/004/006/007 defined in YAML (16 test cases collected).
  - Baseline Status: 13/16 pass, 3 fail (AT-PARALLEL-002: pixel-0.05mm/0.4mm; AT-PARALLEL-004: xds).
  - Status: Harness operational and gating parity work. Ready for debugging loops.
  - Artifacts: `tests/test_parity_matrix.py`, baseline metrics in `reports/2025-09-29-AT-PARALLEL-{002,004}/`.

- **AT-PARALLEL-002 Pixel Size Independence** (2025-09-29)
  - Root cause: comparison-tool resampling bug (commit 7958417).
  - Status: Complete; 4/4 PyTorch tests pass; parity harness case documented (`tests/parity_cases.yaml`: AT-PARALLEL-002).
  - Artifacts: `reports/debug/2025-09-29-at-parallel-002/summary.json`.

---
## TODO Backlog

- [ ] Add parity cases for AT-PARALLEL-003/005/008/009/010/012/013/014/015/016/017/018/020/021/022/023/024/025/026/027/028/029.  
- [ ] Implement docs-as-data lint (spec ↔ matrix ↔ YAML ↔ fix_plan).  
- [ ] Convert legacy manual comparison scripts to consume parity harness outputs (optional).

---
## Reference Commands

```
# Shared parity harness
NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_parity_matrix.py

# Individual AT (PyTorch self-checks remain secondary)
pytest -v tests/test_at_parallel_002.py
```

---
## Notes
- Harness cases fix seeds and use `sys.executable -m nanobrag_torch` to match venv.  
- Parity artifacts (metrics.json, diff PNGs) live under `reports/<date>-AT-*/` per attempt.  
- Keep `docs/development/testing_strategy.md` and `specs/spec-a-parallel.md` aligned with new parity entries.
