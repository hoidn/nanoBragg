# nanoBragg PyTorch Implementation Fix Plan

**Last Updated:** 2025-09-29
**Current Status:** Parity harness bootstrapped and operational; acceptance suite green.

---
## Active Focus

## [AT-PARALLEL-002-EXTREME] Pixel Size Parity Failures (0.05mm & 0.4mm)
- Spec/AT: AT-PARALLEL-002 Pixel Size Independence
- Priority: High
- Status: in_progress
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
- Risks/Assumptions: May involve subpixel/omega formula edge cases at extreme pixel sizes; solidangle/close_distance scaling may differ
- Exit Criteria (from spec-a-parallel.md): corr≥0.9999; beam center in pixels = 25.6/pixel_size ±0.1px; inverse peak scaling verified; sum_ratio in [0.9,1.1]; max|Δ|≤300

---
## Queued Items

1. **Parity Harness Coverage Expansion** *(queued)*
   - Goal: ensure every parity-threshold AT (specs/spec-a-parallel.md) has a canonical entry in `tests/parity_cases.yaml` and executes via `tests/test_parity_matrix.py`.
   - Status: Harness file `tests/test_parity_matrix.py` created (2025-09-29); initial parity cases exist for AT-PARALLEL-001/002/004/006/007.
   - Exit criteria: parity matrix collects ≥1 case per AT with thresholds cited in metrics.json; `pytest -k parity_matrix` passes.
   - Reproduction: `NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_parity_matrix.py`.
   - Next: Verify harness executes cleanly for existing cases, then add remaining ATs (003/005/008/009/010/011/012/020/022/023/024/025/026/027/028/029).

2. **Docs-as-Data CI lint** *(queued)*
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
