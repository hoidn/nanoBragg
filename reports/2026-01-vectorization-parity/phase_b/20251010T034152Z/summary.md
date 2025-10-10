# Phase B3 Option A Execution Summary

## Timestamp
2025-10-10T03:42Z

## Objective
Execute Phase B3a–B3d Option A tasks: generate C golden image, document provenance, implement ROI-based pytest, and run test (expected FAIL) while capturing artifacts.

## Tasks Completed

### B3a: Generate 4096² Golden Float Image ✅
- **Command**: `./nanoBragg -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 -distance 500 -detpixels 4096 -pixel 0.05 -floatfile tests/golden_data/high_resolution_4096/image.bin`
- **Output File**: `tests/golden_data/high_resolution_4096/image.bin`
- **File Size**: 64MB (16,777,216 floats = 4096×4096×4 bytes)
- **SHA256**: `5c623241d3141334449e251fee41901de0edd895f85b9de1aa556cf48d374867`
- **Git SHA**: `dfa74570f16ba70dc2481690d931b049fca174f8`
- **Artifacts**:
  - Command log: `c_golden/command.log`
  - Checksum: `c_golden/checksum.txt`
  - Git info: `c_golden/git_info.txt`

### B3b: Document Golden-Data Provenance ✅
- **Updated**: `tests/golden_data/README.md`
  - Added Section 5: `high_resolution_4096` Test Case
  - Documented canonical C command (copy-pasteable)
  - Captured key parameters (λ=0.5Å, 500mm distance, 0.05mm pixels, 4096×4096 detector)
  - Noted ROI scope (512×512 centered window, slice [1792:2304, 1792:2304])
  - Included acceptance criteria from AT-PARALLEL-012
  - Recorded provenance metadata (timestamp, git SHA, checksum, command log path)

### B3c: Implement ROI-Based Pytest Body ✅
- **File**: `tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_high_resolution_variant`
- **Changes**:
  - Removed `@pytest.mark.skip` decorator
  - Implemented full ROI extraction logic (slice [1792:2304, 1792:2304])
  - Added NaN/Inf checks for both golden and PyTorch ROIs
  - Implemented correlation calculation on 512×512 ROI
  - Added peak detection (top 50) with Hungarian matching
  - Enforced spec thresholds: corr ≥ 0.95, peak match ≥48/50 within 1.0px
  - Maintained vectorization and device/dtype neutrality

### B3d: Execute Targeted Pytest (Expected FAIL) ✅
- **Command**: `KMP_DUPLICATE_LIB_OK=TRUE pytest -xvs tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_high_resolution_variant`
- **Result**: **FAILED** (as expected)
- **Metrics**:
  - **ROI Correlation**: 0.7157 (❌ << 0.95 threshold)
  - **Error Message**: `AssertionError: ROI correlation 0.7157 < 0.95 requirement`
  - **Test Duration**: 5.78s
- **Artifacts**:
  - Full pytest output: `pytest_highres.log`

## Key Findings

### Correlation Parity Failure Confirmed
- **Observed ROI Correlation**: 0.7157
- **Spec Requirement**: ≥ 0.95
- **Gap**: 0.2343 (23.4% below threshold)
- **Consistency**: This 0.716 correlation matches the 0.721 pattern observed in `VECTOR-GAPS-002` Attempts #3–#8 and `VECTOR-PARITY-001` Phase B1/B2

### Pattern Recognition
The recurring correlation value (~0.72) across multiple test configurations suggests:
1. **Systematic Bug**: Not random noise or hardware-dependent behavior
2. **Likely Source Weighting Issue**: Matches VECTOR-GAPS-002 Phase B2/B3 hypothesis about equal-weight source contract violation
3. **Resolution-Independent**: Appears at both 4096² (this test) and other resolutions

### No NaN/Inf Issues
- Both golden and PyTorch ROIs passed NaN/Inf checks
- Indicates numerical stability is intact
- Problem is algorithmic/logic, not numeric precision

## Next Steps (Phase B4)

As outlined in `plans/active/vectorization-parity-regression.md`:

### B4a: ROI Sanity Sweep via nb-compare
Run `nb-compare --resample --roi 1792 2304 1792 2304 --outdir reports/2026-01-vectorization-parity/phase_b/<STAMP>/roi_compare -- -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 -distance 500 -detpixels 4096 -pixel 0.05`

### B4b: Summarise ROI Findings
Compile `roi_scope.md` with:
- Correlation vs ROI size analysis
- Peak offset patterns
- Hypotheses for Phase C trace work
- Reference to spec thresholds

### Phase C: Divergence Localisation
After B4 scope checks, proceed to parallel trace-driven debugging per `docs/debugging/debugging.md`

## Artifact Inventory

```
reports/2026-01-vectorization-parity/phase_b/20251010T034152Z/
├── c_golden/
│   ├── command.log          # Full C nanoBragg execution log
│   ├── checksum.txt         # SHA256 of golden binary
│   └── git_info.txt         # Git commit metadata
├── pytest_highres.log       # Full pytest failure output
└── summary.md               # This document
```

## Blockers / Issues
None - all Phase B3 tasks completed successfully. Evidence captured and ready for Phase B4 ROI analysis.
