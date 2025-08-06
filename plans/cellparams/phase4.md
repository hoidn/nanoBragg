### **Agent Implementation Checklist: Phase 4 - Differentiability Verification & Finalization**

**Overall Goal for this Phase:** To rigorously verify that all six unit cell parameters are fully differentiable and to finalize all related documentation.

**Instructions for Agent:**
1.  Copy this checklist into your working memory.
2.  Update the `State` for each item as you progress: `[ ]` (Open) -> `[P]` (In Progress) -> `[D]` (Done).
3.  Follow the `How/Why & API Guidance` column carefully for implementation details.

---

| ID | Task Description | State | How/Why & API Guidance |
| :--- | :--- | :--- | :--- |
| **Section 0: Preparation & Context Priming** |
| 0.A | **Review Key Documents** | `[ ]` | **Why:** To load the necessary context for implementing the final, most rigorous tests. <br> **Docs:** `plans/geometry/implementation_geometry.md` (Phase 4 section), `docs/development/testing_strategy.md` (Gradient Correctness section). |
| 0.B | **Identify Target Files for Modification** | `[ ]` | **Why:** To have a clear list of files that will be touched during this phase. <br> **Files:** `tests/test_crystal_geometry.py` (Modify), `README.md` (Modify), all relevant module docstrings. |
| **Section 1: Gradient Verification** |
| 1.A | **Implement Individual `gradcheck` Tests** | `[ ]` | **Why:** To verify that each of the six unit cell parameters is independently differentiable. <br> **How:** In `tests/test_crystal_geometry.py`, create a parameterized test that runs `torch.autograd.gradcheck` for each parameter (`cell_a`, `cell_b`, `cell_c`, `cell_alpha`, `cell_beta`, `cell_gamma`). <br> **Parameters:** Use `dtype=torch.float64`, `eps=1e-6`, `atol=1e-6`, `rtol=1e-4`, `check_undefined_grad=True`. |
| 1.B | **Implement Joint `gradcheck` Test** | `[ ]` | **Why:** To catch any cross-coupling issues between parameter gradients. <br> **How:** Create `test_joint_gradcheck`. Concatenate all six cell parameters into a single 6-element tensor. Run `gradcheck` on a function that takes this 6-vector as input and returns the simulation sum. |
| 1.C | **Implement `gradgradcheck` Test** | `[ ]` | **Why:** To ensure second-order gradients are stable, which is important for more advanced optimization algorithms. <br> **How:** Create `test_joint_gradgradcheck`. Use `torch.autograd.gradgradcheck` on the same function and 6-vector input from the joint `gradcheck` test. |
| 1.D | **Test with Edge-Case Geometries** | `[ ]` | **Why:** To ensure gradient stability for challenging, non-ideal crystal geometries. <br> **How:** Add test cases to the `gradcheck` tests that use near-orthogonal (e.g., `gamma=89.9°`) and highly oblique (e.g., `gamma=120°`) cell parameters. |
| **Section 2: Advanced Validation** |
| 2.A | **Implement Property-Based Tests** | `[ ]` | **Why:** To find edge cases in the geometry calculations that fixed unit tests might miss. <br> **How:** If `hypothesis` is a dependency, use it to create `test_property_based_invariants`. If not, create a simple random sampler. Generate N=25 random, well-conditioned cells and assert that the Metric Duality and Volume Identity tests pass for all of them. |
| 2.B | **Implement Optimization Recovery Test** | `[ ]` | **Why:** To provide an end-to-end validation that the gradients are not just correct, but also useful for optimization. <br> **How:** Create `test_optimization_recovers_known_cell`. <br> 1. Define a "target" triclinic cell. <br> 2. Create a "guess" cell with slightly perturbed parameters (as `torch.Tensor` with `requires_grad=True`). <br> 3. In a short loop (5-10 steps), run a simple optimization (e.g., `torch.optim.Adam`) to minimize the MSE between the reciprocal vectors of the guess and target. <br> 4. Assert that the final guess parameters are closer to the target than the initial guess. |
| **Section 3: Documentation & Finalization** |
| 3.A | **Update All Relevant Docstrings** | `[ ]` | **Why:** To ensure the code is self-documenting and reflects the new, general capabilities. <br> **How:** Review and update the docstrings for `CrystalConfig`, `Crystal`, and `Simulator` to describe the new triclinic geometry parameters and functionality. Remove any "TODO" or "placeholder" comments related to this work. |
| 3.B | **Update `README.md`** | `[ ]` | **Why:** To update the high-level project documentation. <br> **How:** Add a note to the `README.md` under a "Features" section, stating that the simulator now supports general triclinic cells and differentiable unit cell parameters. |
| 3.C | **Code Formatting & Linting** | `[ ]` | **Why:** To maintain code quality. <br> **How:** Run `black .` and `ruff . --fix` on all modified files. |
| 3.D | **Commit Phase 4 Work** | `[ ]` | **Why:** To checkpoint the completion of the entire initiative. <br> **Commit Message:** `feat(geometry): Phase 4 - Verify differentiability and finalize geometry engine` |

---

**Success Test (Acceptance Gate):**
*   `gradcheck` and `gradgradcheck` pass for all specified parameters and geometries.
*   The randomized property-based tests pass consistently.
*   The optimization recovery test successfully reduces the error between the guess and target cells.
*   All documentation is updated to reflect the new, general-purpose geometry engine.
