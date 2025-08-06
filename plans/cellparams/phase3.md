### **Agent Implementation Checklist: Phase 3 - Simulator Integration & End-to-End Validation**

**Overall Goal for this Phase:** To integrate the new dynamic `Crystal` model into the `Simulator` and validate the correctness of the full, end-to-end simulation.

**Instructions for Agent:**
1.  Copy this checklist into your working memory.
2.  Update the `State` for each item as you progress: `[ ]` (Open) -> `[P]` (In Progress) -> `[D]` (Done).
3.  Follow the `How/Why & API Guidance` column carefully for implementation details.

---

| ID | Task Description | State | How/Why & API Guidance |
| :--- | :--- | :--- | :--- |
| **Section 0: Preparation & Context Priming** |
| 0.A | **Review Key Documents** | `[ ]` | **Why:** To load the necessary context from the previous phase and the overall plan. <br> **Docs:** `plans/geometry/implementation_geometry.md` (Phase 3 section), `src/nanobrag_torch/models/crystal.py` (review the new `compute_cell_tensors` method). |
| 0.B | **Identify Target Files for Modification** | `[ ]` | **Why:** To have a clear list of files that will be touched during this phase. <br> **Files:** `src/nanobrag_torch/simulator.py` (Modify), `tests/test_suite.py` (Modify). |
| **Section 1: Simulator Integration** |
| 1.A | **Update `Simulator.run`** | `[ ]` | **Why:** To replace the use of static, hard-coded lattice vectors with the new dynamically calculated ones. <br> **How:** At the beginning of the `run` method, call `self.crystal.compute_cell_tensors(self.crystal_config)` to get the dictionary of lattice vectors. Use these tensors (e.g., `cell_tensors["a_star"]`) in all subsequent calculations. |
| 1.B | **Review HKL Range Logic** | `[ ]` | **Why:** To ensure the logic for determining which reflections to consider is correct for a general triclinic cell. <br> **How:** Review the `get_structure_factor` method and any related logic. The current implementation (simple lookup) is okay for now, but add a `TODO` comment to note that a future implementation must calculate `|h*a* + k*b* + l*c*| <= 1/d_min` to correctly handle resolution cutoffs. |
| **Section 2: Integration & Regression Testing** |
| 2.A | **Implement `triclinic_P1` Integration Test** | `[ ]` | **Why:** To perform an end-to-end validation of the new triclinic geometry engine. <br> **How:** In `tests/test_suite.py`, create a new test `test_triclinic_P1_reproduction`. <br> 1. Load the `triclinic_P1/image.bin` golden data. <br> 2. Configure the `Simulator` with the `triclinic_P1` cell parameters. <br> 3. Run the simulation. <br> 4. Assert that the Pearson correlation coefficient between the simulated and golden images is `≥ 0.990`. |
| 2.B | **Implement Peak Position Check** | `[ ]` | **Why:** To provide a more sensitive check of geometric accuracy than overall correlation. <br> **How:** As part of `test_triclinic_P1_reproduction`, find the coordinates of the top 50 brightest pixels in both the golden and simulated images. Calculate the Euclidean distance between corresponding peak pairs. Assert that the maximum distance is `≤ 0.5` pixels. |
| 2.C | **Verify `simple_cubic` Regression Test** | `[ ]` | **Why:** To ensure that the refactoring has not broken the existing, validated functionality. <br> **How:** Run the existing `test_simple_cubic_reproduction` test in `tests/test_suite.py`. It should pass without any modifications. |
| 2.D | **Implement Sensitivity Sign Test** | `[ ]` | **Why:** To confirm that the model behaves in a physically plausible way. <br> **How:** In `tests/test_crystal_geometry.py`, create `test_sensitivity_to_gamma`. <br> 1. Run a simulation with a triclinic cell and find a reference peak position. <br> 2. Run a second simulation with `gamma` increased by a small amount (e.g., 0.1 degrees). <br> 3. Find the new peak position. <br> 4. Assert that the peak has moved in the expected direction (based on a simple geometric prediction or finite difference). |
| **Section 3: Performance Gating** |
| 3.A | **Establish Performance Benchmark** | `[ ]` | **Why:** To create a baseline for measuring performance regressions. <br> **How:** Add a new test `test_performance_simple_cubic` to `tests/test_suite.py`. Time the execution of the `simple_cubic` simulation. Store this baseline time in a comment or a helper file. |
| 3.B | **Run Performance Gate** | `[ ]` | **Why:** To ensure the new, more complex geometry calculations do not unacceptably slow down the simulation for the simple cubic case. <br> **How:** The `test_performance_simple_cubic` test should assert that the current runtime is no more than 10% slower than the established baseline. |
| **Section 4: Finalization** |
| 4.A | **Code Formatting & Linting** | `[ ]` | **Why:** To maintain code quality. <br> **How:** Run `black .` and `ruff . --fix` on all modified files. |
| 4.B | **Commit Phase 3 Work** | `[ ]` | **Why:** To checkpoint the completion of the integration and validation phase. <br> **Commit Message:** `feat(geometry): Phase 3 - Integrate and validate triclinic geometry in simulator` |

---

**Success Test (Acceptance Gate):**
*   The `simple_cubic` regression test continues to pass.
*   The new `triclinic_P1` integration test passes with Pearson correlation `≥ 0.990`.
*   The peak localization check passes with a maximum error of `≤ 0.5` pixels.
*   The performance benchmark for the `simple_cubic` case shows a regression of `≤ 10%`.
