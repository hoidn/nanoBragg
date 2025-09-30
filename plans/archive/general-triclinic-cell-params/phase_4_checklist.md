# Phase 4: Differentiability Verification & Finalization Checklist

**Initiative:** General Triclinic Cell Parameters
**Created:** 2025-01-29
**Phase Goal:** Validate gradient correctness and update all documentation for the new capability.
**Deliverable:** A fully tested and documented triclinic cell parameter system ready for production use.

## ✅ Task List

### Instructions:
1. Work through tasks in order. Dependencies are noted in the guidance column.
2. The **"How/Why & API Guidance"** column contains all necessary details for implementation.
3. Update the `State` column as you progress: `[ ]` (Open) -> `[P]` (In Progress) -> `[D]` (Done).

---

| ID | Task Description | State | How/Why & API Guidance |
| :--- | :--- | :--- | :--- |
| **Section 0: Preparation & Context Priming** |
| 0.A | **Review Key Documents** | `[D]` | **Why:** To load the necessary context for implementing the final validation tests. <br> **Docs:** `plans/active/general-triclinic-cell-params/implementation.md` (Final Phase section), `docs/development/testing_strategy.md` (Gradient Correctness section), `CLAUDE.md` (Differentiability rules). |
| 0.B | **Identify Target Files for Modification** | `[D]` | **Why:** To have a clear list of files that will be touched during this phase. <br> **Files:** `tests/test_crystal_geometry.py` (Extend), `tests/test_gradients.py` (Create), `README.md` (Update), `docs/tutorials/` (Add notebook). |
| **Section 1: Individual Parameter Gradient Verification** |
| 1.A | **Create Gradient Test Infrastructure** | `[D]` | **Why:** To set up a reusable framework for gradient testing. <br> **How:** Create `tests/test_gradients.py`. Import `torch.autograd.gradcheck` and `gradgradcheck`. Set up helper functions for creating test scenarios with differentiable cell parameters. |
| 1.B | **Implement Cell_a Gradcheck Test** | `[D]` | **Why:** To verify the `a` parameter is fully differentiable. <br> **How:** Create `test_gradcheck_cell_a`. Define a function that takes `cell_a` as input and returns a scalar output (e.g., volume or intensity sum). Run `gradcheck` with `dtype=torch.float64`, `eps=1e-6`, `atol=1e-6`, `rtol=1e-4`. |
| 1.C | **Implement Cell_b Gradcheck Test** | `[D]` | **Why:** To verify the `b` parameter is fully differentiable. <br> **How:** Create `test_gradcheck_cell_b`. Similar to 1.B but for the `b` parameter. Include edge cases like very small or large values. |
| 1.D | **Implement Cell_c Gradcheck Test** | `[D]` | **Why:** To verify the `c` parameter is fully differentiable. <br> **How:** Create `test_gradcheck_cell_c`. Similar structure, ensuring the test covers the full range of reasonable cell dimensions. |
| 1.E | **Implement Cell_alpha Gradcheck Test** | `[D]` | **Why:** To verify the `α` angle parameter is fully differentiable. <br> **How:** Create `test_gradcheck_cell_alpha`. Test with angles from 60° to 120°. Pay special attention to angles near 90° where trigonometric functions may have discontinuities. |
| 1.F | **Implement Cell_beta Gradcheck Test** | `[D]` | **Why:** To verify the `β` angle parameter is fully differentiable. <br> **How:** Create `test_gradcheck_cell_beta`. Include edge cases near 0° and 180° to test numerical stability. |
| 1.G | **Implement Cell_gamma Gradcheck Test** | `[D]` | **Why:** To verify the `γ` angle parameter is fully differentiable. <br> **How:** Create `test_gradcheck_cell_gamma`. Test the full range, including highly skewed cells. |
| **Section 2: Joint and Advanced Gradient Testing** |
| 2.A | **Implement Joint Parameter Gradcheck** | `[D]` | **Why:** To catch any cross-coupling issues between parameter gradients. <br> **How:** Create `test_joint_gradcheck`. Concatenate all six cell parameters into a single tensor. Define a function that unpacks these and computes crystal properties. Verify gradients flow correctly through all parameters simultaneously. |
| 2.B | **Implement Second-Order Gradcheck** | `[D]` | **Why:** To ensure stability for advanced optimization algorithms that use Hessian information. <br> **How:** Create `test_gradgradcheck_cell_params`. Use `torch.autograd.gradgradcheck` on the joint parameter function. This verifies second derivatives are stable. |
| 2.C | **Test Gradient Flow Through Simulator** | `[D]` | **Why:** To verify end-to-end differentiability through the full simulation pipeline. <br> **How:** Create `test_gradient_flow_simulation`. Set up a simple simulation with differentiable cell parameters. Compute a loss on the output image and verify `.grad` is not None for all cell parameters after `.backward()`. |
| **Section 3: Property-Based Testing** |
| 3.A | **Implement Random Cell Generation** | `[D]` | **Why:** To test a wide variety of cell geometries automatically. <br> **How:** Create a helper function `generate_random_cell()` that produces well-conditioned random triclinic cells. Ensure parameters stay within physically reasonable ranges: lengths > 0, angles between 20° and 160°. |
| 3.B | **Property Test: Metric Duality** | `[D]` | **Why:** To verify fundamental crystallographic relationships hold for all random cells. <br> **How:** Create `test_property_metric_duality`. Generate 50 random cells. For each, verify `dot(a*, a) ≈ 1`, `dot(a*, b) ≈ 0`, etc. with appropriate tolerance. |
| 3.C | **Property Test: Volume Consistency** | `[D]` | **Why:** To verify volume calculations are consistent across different formulations. <br> **How:** Create `test_property_volume_consistency`. For random cells, verify the triple product formula matches the closed-form volume formula. |
| 3.D | **Property Test: Gradient Stability** | `[D]` | **Why:** To ensure gradients remain stable across the parameter space. <br> **How:** Create `test_property_gradient_stability`. For 25 random cells, verify gradcheck passes. This catches numerical instabilities in unusual geometries. |
| **Section 4: Optimization Recovery Test** |
| 4.A | **Implement Cell Parameter Recovery** | `[D]` | **Why:** To demonstrate gradients are not just correct but useful for optimization. <br> **How:** Create `test_optimization_recovers_cell`. Start with a target triclinic cell. Initialize guess parameters with 5-10% perturbation. Use `torch.optim.Adam` to minimize MSE between computed reciprocal vectors. Assert convergence within 20 iterations. |
| 4.B | **Test Multiple Optimization Scenarios** | `[D]` | **Why:** To verify robustness across different starting conditions. <br> **How:** Extend the recovery test with multiple scenarios: near-cubic to triclinic, large cell to small cell, different initial perturbation magnitudes. |
| **Section 5: Documentation and Tutorials** |
| 5.A | **Create Tutorial Notebook** | `[D]` | **Why:** To demonstrate the new capabilities to users. <br> **How:** Create `docs/tutorials/cell_parameter_refinement.ipynb`. Include: <br> 1. Loading triclinic crystal data <br> 2. Setting up differentiable parameters <br> 3. Defining a loss function <br> 4. Running optimization <br> 5. Visualizing convergence |
| 5.B | **Update README.md** | `[D]` | **Why:** To announce the new feature at the project level. <br> **How:** Add a "Features" section highlighting: <br> - Support for general triclinic unit cells <br> - Fully differentiable cell parameters <br> - Example use case for structure refinement |
| 5.C | **Update API Documentation** | `[D]` | **Why:** To ensure all docstrings reflect the new capabilities. <br> **How:** Review and update docstrings in: <br> - `CrystalConfig`: Document all 6 cell parameters <br> - `Crystal.compute_cell_tensors`: Full formula documentation <br> - `Simulator`: Note triclinic support |
| 5.D | **Add Migration Guide** | `[D]` | **Why:** To help users transition from hardcoded to dynamic geometry. <br> **How:** Create `docs/migration_guide.md` explaining: <br> - How to update existing cubic simulations <br> - How to enable gradient flow for parameters <br> - Performance considerations |
| **Section 6: Final Validation and Cleanup** |
| 6.A | **Run Full Test Suite with Coverage** | `[D]` | **Why:** To ensure comprehensive test coverage and no regressions. <br> **How:** Run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ --cov=src/nanobrag_torch --cov-report=html`. Review coverage report and add tests for any uncovered edge cases. |
| 6.B | **Performance Benchmarking** | `[D]` | **Why:** To document the computational cost of the new features. <br> **How:** Create benchmark comparing: <br> - Simple cubic (baseline) vs triclinic simulation time <br> - Forward pass vs forward+backward pass time <br> - Document results in `docs/performance.md` |
| 6.C | **Code Quality Review** | `[D]` | **Why:** To ensure production-ready code quality. <br> **How:** <br> - Run `black .` and `ruff . --fix` <br> - Remove all TODO comments related to this feature <br> - Ensure consistent error handling <br> - Verify all tensor operations preserve device/dtype |
| 6.D | **Final Commit and PR Preparation** | `[D]` | **Why:** To complete the feature implementation. <br> **Commit Message:** `feat(geometry): Phase 4 - Complete differentiable triclinic cell parameters with full validation suite` <br> **PR Description:** Include summary of all 4 phases, key capabilities added, and performance impact. |

---

## 🎯 Success Criteria

**This phase is complete when:**
1. All tasks in the table above are marked `[D]` (Done).
2. All gradcheck and gradgradcheck tests pass for individual and joint parameters.
3. Property-based tests pass for 50+ random cell configurations.
4. Optimization recovery test successfully converges to target parameters.
5. Tutorial notebook successfully demonstrates cell parameter refinement.
6. Full test suite passes with >90% code coverage.
7. Documentation comprehensively describes the new capabilities.