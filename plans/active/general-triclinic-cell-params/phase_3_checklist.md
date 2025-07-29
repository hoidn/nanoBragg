# Phase 3: Simulator Integration & End-to-End Validation Checklist

**Initiative:** General Triclinic Cell Parameters
**Created:** 2025-01-29
**Phase Goal:** Integrate the dynamic geometry into the Simulator and validate against golden data.
**Deliverable:** A fully integrated simulator that passes both simple cubic and triclinic test cases.

## ✅ Task List

### Instructions:
1. Work through tasks in order. Dependencies are noted in the guidance column.
2. The **"How/Why & API Guidance"** column contains all necessary details for implementation.
3. Update the `State` column as you progress: `[ ]` (Open) -> `[P]` (In Progress) -> `[D]` (Done).

---

| ID | Task Description | State | How/Why & API Guidance |
| :--- | :--- | :--- | :--- |
| **Section 0: Preparation & Context Priming** |
| 0.A | **Review Key Documents** | `[D]` | **Why:** To load the necessary context from the previous phase and the overall plan. <br> **Docs:** `plans/active/general-triclinic-cell-params/implementation.md` (Phase 3 section), `src/nanobrag_torch/models/crystal.py` (review the new `compute_cell_tensors` method), `tests/test_crystal_geometry.py` (understand Phase 2 tests). |
| 0.B | **Identify Target Files for Modification** | `[D]` | **Why:** To have a clear list of files that will be touched during this phase. <br> **Files:** `src/nanobrag_torch/simulator.py` (Modify), `tests/test_suite.py` (Modify), `src/nanobrag_torch/models/crystal.py` (Minor updates if needed). |
| **Section 1: Simulator Integration** |
| 1.A | **Update `Simulator.run` Method** | `[D]` | **Why:** To replace the use of static, hard-coded lattice vectors with the new dynamically calculated ones. <br> **How:** In the `run` method, replace direct access to `self.crystal.a_star` etc. with calls to the new property methods that use `compute_cell_tensors()`. Ensure all reciprocal vector calculations use the dynamic values. |
| 1.B | **Update Crystal Instantiation in Simulator** | `[D]` | **Why:** To ensure the Crystal class is instantiated with proper configuration. <br> **How:** Modify `Simulator.__init__` to pass `CrystalConfig` to the Crystal constructor. Update any hardcoded cell parameters to use config values. |
| 1.C | **Review HKL Range Calculation** | `[D]` | **Why:** To ensure the logic for determining which reflections to consider is correct for a general triclinic cell. <br> **How:** Review the `get_structure_factor` method and any HKL range logic. Add a `TODO` comment noting that future implementation must calculate `|h*a* + k*b* + l*c*| <= 1/d_min` for correct resolution cutoffs. |
| 1.D | **Update Scattering Vector Calculations** | `[D]` | **Why:** To ensure all scattering vector calculations use the dynamic reciprocal vectors. <br> **How:** In `Simulator.run`, verify that `S = h*a_star + k*b_star + l*c_star` calculations use the property-based vectors, not hardcoded values. |
| **Section 2: Integration Testing** |
| 2.A | **Implement Triclinic Integration Test** | `[D]` | **Why:** To perform an end-to-end validation of the new triclinic geometry engine. <br> **How:** In `tests/test_suite.py`, create `test_triclinic_P1_reproduction`. <br> 1. Load `tests/golden_data/triclinic_P1/image.bin` <br> 2. Configure Simulator with triclinic_P1 parameters (70, 80, 90, 75.0391, 85.0136, 95.0081) <br> 3. Run simulation <br> 4. Assert Pearson correlation ≥ 0.990 |
| 2.B | **Implement Peak Position Validation** | `[D]` | **Why:** To provide a more sensitive check of geometric accuracy than overall correlation. <br> **How:** Within `test_triclinic_P1_reproduction`, find top 50 brightest pixels in both golden and simulated images. Calculate Euclidean distances between corresponding peaks. Assert maximum distance ≤ 0.5 pixels. |
| 2.C | **Verify Simple Cubic Backward Compatibility** | `[D]` | **Why:** To ensure that the refactoring has not broken existing functionality. <br> **How:** Run the existing `test_simple_cubic_reproduction` test. It should pass without modifications. If it fails, debug the regression. |
| 2.D | **Implement Cell Parameter Sensitivity Test** | `[D]` | **Why:** To confirm that the model behaves physically when cell parameters change. <br> **How:** Create `test_sensitivity_to_cell_params` in `tests/test_suite.py`. <br> 1. Run simulation with base triclinic cell <br> 2. Perturb each parameter (a, b, c, α, β, γ) by ±0.1% <br> 3. Verify peak positions shift in expected directions |
| **Section 3: Performance Profiling** |
| 3.A | **Profile Simple Cubic Performance** | `[D]` | **Why:** To establish a performance baseline and identify any regressions. <br> **How:** Create `test_performance_simple_cubic` in `tests/test_suite.py`. Time the execution of simple_cubic simulation. Store baseline time. Assert current runtime is no more than 10% slower than baseline. |
| 3.B | **Profile Triclinic Performance** | `[D]` | **Why:** To understand the computational cost of general triclinic calculations. <br> **How:** Create `test_performance_triclinic` to time triclinic simulation. Compare with simple cubic baseline. Document the performance difference. |
| 3.C | **Memory Usage Analysis** | `[D]` | **Why:** To ensure the dynamic calculation doesn't introduce memory leaks or excessive allocation. <br> **How:** Use memory profiling tools or manual tracking to compare memory usage between old and new implementations. Document findings. |
| **Section 4: Debugging & Edge Cases** |
| 4.A | **Test Extreme Cell Parameters** | `[D]` | **Why:** To ensure numerical stability for edge cases. <br> **How:** Test with: <br> - Nearly cubic cells (angles near 90°) <br> - Highly skewed cells (angles near 45° or 135°) <br> - Very small/large cell dimensions <br> Assert no NaN/Inf in outputs. |
| 4.B | **Debug Any Correlation Failures** | `[D]` | **Why:** To achieve the required >0.99 correlation with C-code. <br> **How:** If tests fail: <br> 1. Use `scripts/debug_pixel_trace.py` for parallel trace <br> 2. Compare intermediate values with C-code trace <br> 3. Fix any discrepancies found |
| 4.C | **Validate Rotation Compatibility** | `[D]` | **Why:** To ensure dynamic geometry works with crystal rotations. <br> **How:** Test that phi rotation and mosaic spread still work correctly with triclinic cells. Run a test with non-zero phi and mosaic values. |
| **Section 5: Finalization** |
| 5.A | **Code Formatting & Linting** | `[D]` | **Why:** To maintain code quality standards. <br> **How:** Run `black .` and `ruff . --fix` on all modified files. Ensure KMP_DUPLICATE_LIB_OK=TRUE is set for all PyTorch operations. |
| 5.B | **Run Full Test Suite** | `[D]` | **Why:** To ensure no regressions and all functionality works. <br> **How:** Run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v` and verify all tests pass, including new integration tests. |
| 5.C | **Update Documentation** | `[D]` | **Why:** To document the new capabilities. <br> **How:** Update any relevant docstrings in Simulator and Crystal classes to reflect dynamic geometry support. Add comments explaining the integration points. |
| 5.D | **Commit Phase 3 Work** | `[ ]` | **Why:** To checkpoint the completion of the integration and validation phase. <br> **Commit Message:** `feat(geometry): Phase 3 - Integrate and validate triclinic geometry in simulator` |

---

## 🎯 Success Criteria

**This phase is complete when:**
1. All tasks in the table above are marked `[D]` (Done).
2. The phase success test passes: Both simple_cubic and triclinic_P1 tests achieve >0.99 correlation with C-code.
3. Performance regression for simple_cubic is ≤ 10%.
4. All edge cases pass without numerical errors.
5. Full test suite passes without regressions.