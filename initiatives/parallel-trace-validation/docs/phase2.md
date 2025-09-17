# Implementation Checklist: Phase 2 - Analysis, Fix & Verification

**Overall Goal for this Phase**: To use the parallel trace infrastructure to identify the root cause of the numerical discrepancy, implement a targeted fix, and validate the solution with a full suite of tests.

## Instructions for Agent:
1. Copy this checklist into your working memory.
2. Update the State for each item as you progress: `[ ]` (Open) -> `[P]` (In Progress) -> `[D]` (Done).
3. Follow the How/Why & API Guidance column carefully for implementation details.

| ID | Task Description | State | How/Why & API Guidance |
|----|----|----|----|
| **Section 1: Analysis - Pinpoint the Bug** | | | |
| 1.A | Run Trace Comparison | `[ ]` | **Why**: To identify the first intermediate variable that diverges between the C and Python implementations. <br> **How**: Run the compare_traces.py script created in Phase 1 on the c_trace.log and py_trace.log files. <br> **Command**: `python scripts/compare_traces.py tests/golden_data/cubic_tilted_detector/c_trace.log tests/golden_data/cubic_tilted_detector/py_trace.log`. |
| 1.B | Identify Root Cause | `[ ]` | **Why**: To understand the exact mathematical or logical error before attempting a fix. <br> **How**: Examine the output from the comparator. The key and value mismatch it reports is the bug. State the root cause clearly (e.g., "The term_fast vector is incorrect due to a sign error in the Fbeam calculation"). |
| **Section 2: Implementation - Apply Targeted Fix** | | | |
| 2.A | Implement the Fix | `[ ]` | **Why**: To correct the single, identified bug in the Detector class without making extraneous changes. <br> **How**: Based on the identified root cause, modify the single corresponding line of code in `src/nanobrag_torch/models/detector.py`. Do not refactor or change any other part of the code. |
| **Section 3: Verification - Confirm the Fix** | | | |
| 3.A | Regenerate Python Trace | `[ ]` | **Why**: To create an updated trace log with the fix applied for a final comparison. <br> **How**: Rerun the `scripts/debug_beam_pivot_trace.py` script (with the same parameters as in Phase 1) to generate a new py_trace.log. **Important**: You must first modify this script to reflect the same code change you made in the Detector class. |
| 3.B | Verify Trace Equivalence | `[ ]` | **Why**: To confirm the fix was successful at the lowest level, ensuring perfect numerical parity. <br> **How**: Rerun the compare_traces.py script. <br> **Expected Outcome**: The script must now print "OK: traces match within tolerance." and exit with a zero status code. If it still reports a mismatch, return to step 2.A. |
| 3.C | Update Ground Truth in Unit Test | `[ ]` | **Why**: The existing ground-truth value in the test suite may be from a previous, incorrect C-code run. We must update it with the value from our newly verified trace. <br> **How**: <br> 1. Open `tests/golden_data/cubic_tilted_detector/c_trace.log`. <br> 2. Copy the final pix0_vector value. <br> 3. Open `tests/test_detector_geometry.py`. <br> 4. Update the `EXPECTED_TILTED_PIX0_VECTOR_METERS` tensor with this new, correct value. |
| 3.D | Run High-Precision Unit Test | `[ ]` | **Why**: To confirm that the actual Detector class (not just the debug script) now produces the correct result and to lock this behavior in with a regression test. <br> **How**: Run the specific test for the BEAM pivot pix0_vector. <br> **Command**: `pytest -v tests/test_detector_geometry.py::TestDetectorGeometryRegressions::test_pix0_vector_matches_c_reference_in_beam_pivot`. <br> **Success Criterion**: The test must pass with the strict atol=1e-8 tolerance. |
| 3.E | Run End-to-End Validation | `[ ]` | **Why**: To confirm that the geometry fix has resolved the high-level correlation failure. <br> **How**: Run the main verification script. <br> **Command**: `KMP_DUPLICATE_LIB_OK=TRUE python scripts/verify_detector_geometry.py`. <br> **Success Criterion**: The correlation for the "tilted" case reported in correlation_metrics.json must be > 0.999. |
| **Section 4: Cleanup & Finalization** | | | |
| 4.A | Remove C-Code Instrumentation | `[ ]` | **Why**: To clean up the reference C code now that the debugging is complete. <br> **How**: Revert the changes made to `golden_suite_generator/nanoBragg.c` during Phase 1. |
| 4.B | Recompile C-Code | `[ ]` | **Why**: To ensure the C executable is back in its production state. <br> **How**: Run `make -C golden_suite_generator clean all`. |
| 4.C | Archive Debug Scripts | `[ ]` | **Why**: To keep the main scripts directory clean while preserving the useful debugging tools. <br> **How**: Move `scripts/debug_beam_pivot_trace.py` and `scripts/compare_traces.py` to a new directory, `archive/parallel_trace_debugger/`. |
| 4.D | Commit the Fix | `[ ]` | **Why**: To formally record the solution. <br> **How**: Commit the changes to `src/nanobrag_torch/models/detector.py` and `tests/test_detector_geometry.py` with a clear message. <br> **Commit Message**: `fix(detector): Align pix0_vector calculation with C-code via parallel trace`. In the body, briefly describe the root cause that was identified and fixed. |

## Success Test (Acceptance Gate):

✅ The `test_pix0_vector_matches_c_reference_in_beam_pivot` test passes with atol=1e-8.

✅ The end-to-end correlation for the tilted detector test case exceeds 0.999.

✅ The bug is understood, fixed, and all debugging artifacts have been cleaned up or archived.

## Phase 2 Key Commands Reference

### Analysis Commands
```bash
# Step 1.A: Run trace comparison
python scripts/compare_traces.py \
  tests/golden_data/cubic_tilted_detector/c_trace.log \
  tests/golden_data/cubic_tilted_detector/py_trace.log
```

### Verification Commands
```bash
# Step 3.A: Regenerate Python trace (after fix)
python scripts/debug_beam_pivot_trace.py \
  --pixel-mm 0.1 --distance-mm 100.0 \
  --xbeam-mm 51.2 --ybeam-mm 51.2 \
  --rotx-deg 1.0 --roty-deg 5.0 \
  --rotz-deg 0.0 --twotheta-deg 3.0 \
  > tests/golden_data/cubic_tilted_detector/py_trace_fixed.log

# Step 3.D: Run unit test
pytest -v tests/test_detector_geometry.py::TestDetectorGeometryRegressions::test_pix0_vector_matches_c_reference_in_beam_pivot

# Step 3.E: Run E2E validation
KMP_DUPLICATE_LIB_OK=TRUE python scripts/verify_detector_geometry.py
```

### Cleanup Commands
```bash
# Step 4.B: Recompile C-code
make -C golden_suite_generator clean all

# Step 4.C: Archive debug scripts
mkdir -p archive/parallel_trace_debugger
mv scripts/debug_beam_pivot_trace.py archive/parallel_trace_debugger/
mv scripts/compare_traces.py archive/parallel_trace_debugger/
```

## Expected Root Cause Categories

Based on the systematic trace analysis, the bug will likely fall into one of these categories:

1. **Sign Error**: Incorrect sign in term_fast or term_slow calculation
2. **Convention Mapping**: Wrong assignment of Fbeam/Sbeam from Xbeam/Ybeam
3. **Rotation Order**: Incorrect matrix multiplication sequence (should be Rz@Ry@Rx)
4. **Twotheta Axis**: Wrong axis for MOSFLM convention (should be [0,0,-1])
5. **Unit Conversion**: Missing or incorrect mm-to-meters conversion
6. **Pixel Center**: Missing +0.5 pixel adjustment in beam center calculation

The parallel trace comparison will pinpoint exactly which category and provide the precise fix location.