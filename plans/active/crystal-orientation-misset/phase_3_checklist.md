# Phase 3: Full Simulator Integration & Golden Test Checklist

**Initiative:** Crystal Orientation Misset
**Created:** 2025-01-29
**Phase Goal:** To complete the integration into the full simulation pipeline and achieve the primary validation goal against the golden test case.
**Deliverable:** A fully integrated simulator that passes the triclinic_P1 golden test with ≥0.990 correlation.

## ✅ Task List

### Instructions:
1.  Work through tasks in order. Dependencies are noted in the guidance column.
2.  The **"How/Why & API Guidance"** column contains all necessary details for implementation.
3.  Update the `State` column as you progress: `[ ]` (Open) -> `[P]` (In Progress) -> `[D]` (Done).

---

| ID  | Task Description                                   | State | How/Why & API Guidance |
| :-- | :------------------------------------------------- | :---- | :------------------------------------------------- |
| **Section 0: Preparation & Context Review** |
| 0.A | **Review integration requirements**                | `[ ]` | **Why:** To understand how misset fits into the full simulation pipeline. <br> **Files:** Review `src/nanobrag_torch/simulator.py`, `tests/test_suite.py`. <br> **Focus:** How Crystal is instantiated in Simulator, where rotations are applied. |
| 0.B | **Study triclinic_P1 test structure**              | `[ ]` | **Why:** To understand the test we need to pass. <br> **File:** `tests/test_suite.py` - find `test_triclinic_P1_reproduction`. <br> **Note:** Current correlation value, test parameters, golden data path. |
| 0.C | **Locate golden reference data**                   | `[ ]` | **Why:** To understand expected output for validation. <br> **Path:** `tests/golden_data/triclinic_P1/`. <br> **Files:** Check for image files, trace.log, configuration parameters. |
| **Section 1: Update Triclinic Test Configuration** |
| 1.A | **Add misset angles to test config**               | `[ ]` | **Why:** The triclinic_P1 test needs the specific misset angles from C-code. <br> **File:** `tests/test_suite.py` in `test_triclinic_P1_reproduction`. <br> **Add:** `misset_deg=(-89.968546, -31.328953, 177.753396)` to CrystalConfig. |
| 1.B | **Verify test still runs**                         | `[ ]` | **Why:** Ensure basic test infrastructure works with misset parameter. <br> **Command:** `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_suite.py::test_triclinic_P1_reproduction -v`. <br> **Expected:** Test runs (may fail correlation check initially). |
| **Section 2: Debug Correlation Issues** |
| 2.A | **Run initial correlation check**                  | `[ ]` | **Why:** Establish baseline correlation with misset applied. <br> **Command:** Run the test and note the correlation value. <br> **Target:** ≥0.990 Pearson correlation on masked pixels. |
| 2.B | **Add debug output for rotation matrices**         | `[ ]` | **Why:** Help diagnose if rotations are being applied correctly. <br> **Add:** Print statements showing rotation matrices and vectors at key points. <br> **Locations:** After misset application, after phi rotation if applicable. |
| 2.C | **Check rotation pipeline order**                  | `[ ]` | **Why:** Ensure rotations are applied in correct sequence. <br> **Verify:** Misset → Phi → Mosaic order is maintained. <br> **File:** Check `Crystal.get_rotated_real_vectors()` if it exists. |
| 2.D | **Compare with C-code trace if needed**            | `[ ]` | **Why:** Debug any remaining discrepancies. <br> **Method:** Use parallel trace comparison from `docs/development/debugging.md`. <br> **Files:** `scripts/debug_pixel_trace.py` if correlation < 0.990. |
| **Section 3: Regression Testing** |
| 3.A | **Verify simple_cubic test passes**                | `[ ]` | **Why:** Ensure we haven't broken existing functionality. <br> **Command:** `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_suite.py::test_simple_cubic_milestone -v`. <br> **Expected:** Test continues to pass with high correlation. |
| 3.B | **Check other geometry tests**                     | `[ ]` | **Why:** Confirm no regressions in crystal geometry. <br> **Command:** `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_crystal_geometry.py -v`. <br> **Expected:** All tests pass. |
| 3.C | **Run full test suite**                            | `[ ]` | **Why:** Comprehensive regression check. <br> **Command:** `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v`. <br> **Note:** Document any failures for investigation. |
| **Section 4: Performance Profiling** |
| 4.A | **Profile baseline performance**                   | `[ ]` | **Why:** Measure impact of misset rotation on simulation speed. <br> **Method:** Time simple_cubic test without misset (set misset_deg=(0,0,0)). <br> **Record:** Average time over 3 runs. |
| 4.B | **Profile with misset enabled**                    | `[ ]` | **Why:** Compare performance with rotation applied. <br> **Method:** Time simple_cubic test with misset_deg=(30,45,60). <br> **Target:** <5% slowdown from baseline. |
| 4.C | **Optimize if needed**                             | `[ ]` | **Why:** Address any significant performance regressions. <br> **Options:** Cache rotation matrices if angles are constant, vectorize operations. <br> **Only if:** Slowdown exceeds 5% threshold. |
| **Section 5: Clean Up Debug Code** |
| 5.A | **Remove debug print statements**                  | `[ ]` | **Why:** Clean up code before finalizing. <br> **Search:** Remove any print() statements added for debugging. <br> **Files:** All modified files in this phase. |
| 5.B | **Add meaningful comments**                        | `[ ]` | **Why:** Document any non-obvious implementation details. <br> **Focus:** Rotation order, coordinate system conventions. <br> **Avoid:** Over-commenting obvious code. |
| **Section 6: Final Validation** |
| 6.A | **Run triclinic test final validation**            | `[ ]` | **Why:** Confirm we meet the success criteria. <br> **Command:** `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_suite.py::test_triclinic_P1_reproduction -v`. <br> **Success:** Pearson correlation ≥0.990 on masked pixels. |
| 6.B | **Document final correlation value**               | `[ ]` | **Why:** Record achievement of key metric. <br> **Update:** Add comment in test with achieved correlation. <br> **Format:** `# Achieved correlation: 0.XXX with misset rotation`. |
| 6.C | **Verify all phase deliverables**                  | `[ ]` | **Why:** Ensure phase is complete. <br> **Check:** 1) Triclinic test passes with ≥0.990 correlation, 2) No regression in other tests, 3) Performance impact <5%. |

---

## 🎯 Success Criteria

**This phase is complete when:**
1.  All tasks in the table above are marked `[D]` (Done).
2.  The phase success test passes: `pytest tests/test_suite.py::test_triclinic_P1_reproduction -v` achieves ≥0.990 Pearson correlation on masked pixels.
3.  No regressions are introduced in the existing test suite.
4.  Performance impact is documented and within acceptable limits (<5% slowdown).