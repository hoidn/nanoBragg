### **Agent Implementation Checklist: Phase 2 - Core Geometry Engine & Unit Testing**

**Overall Goal for this Phase:** To implement the core differentiable logic for calculating lattice vectors from the six unit cell parameters and to validate it with a comprehensive suite of unit tests.

**Instructions for Agent:**
1.  Copy this checklist into your working memory.
2.  Update the `State` for each item as you progress: `[ ]` (Open) -> `[P]` (In Progress) -> `[D]` (Done).
3.  Follow the `How/Why & API Guidance` column carefully for implementation details.

---

| ID | Task Description | State | How/Why & API Guidance |
| :--- | :--- | :--- | :--- |
| **Section 0: Preparation & Context Priming** |
| 0.A | **Review Key Documents** | `[ ]` | **Why:** To load the necessary context and technical specifications before coding. <br> **Docs:** `plans/geometry/implementation_geometry.md` (Phase 2 section), `tests/golden_data/triclinic_P1/trace.log` (for ground-truth values). |
| 0.B | **Identify Target Files for Modification** | `[ ]` | **Why:** To have a clear list of files that will be touched during this phase. <br> **Files:** `src/nanobrag_torch/models/crystal.py` (Modify), `tests/test_crystal_geometry.py` (Modify). |
| **Section 1: Implement Core Geometry Logic** |
| 1.A | **Refactor `Crystal.__init__`** | `[ ]` | **Why:** To remove hard-coded vectors and prepare for dynamic calculation. <br> **How:** Remove the hard-coded `self.a`, `self.b`, `self.c`, `self.a_star`, etc. tensors. The `__init__` method should now primarily store the `CrystalConfig` and basic parameters like `N_cells`. |
| 1.B | **Implement `compute_cell_tensors` Method** | `[ ]` | **Why:** To create the central, differentiable function for all geometry calculations. <br> **How:** In `src/nanobrag_torch/models/crystal.py`, create a new method `compute_cell_tensors(self, config: CrystalConfig)`. Implement the exact, numerically stable formulas from the R&D plan (v4) using `torch.float64`. <br> **Return:** A dictionary of tensors: `{ "a": a_vec, "b": b_vec, "c": c_vec, "a_star": a_star, "b_star": b_star, "c_star": c_star, "V": V }`. |
| 1.C | **Implement Orientation Matrix Application** | `[ ]` | **Why:** To apply the crystal's orientation after calculating the base lattice vectors, following the C-code's logical flow. <br> **How:** The `compute_cell_tensors` method should accept an optional `orientation_matrix: torch.Tensor` (3x3). If provided, it should be applied to the calculated `a,b,c` and `a*,b*,c*` vectors before they are returned. |
| **Section 2: Unit Testing** |
| 2.A | **Implement Cubic Regression Test** | `[ ]` | **Why:** To ensure the new general formulas correctly reproduce the simple cubic case. <br> **How:** In `tests/test_crystal_geometry.py`, create `test_cubic_regression`. Call `compute_cell_tensors` with cubic parameters. Assert that the returned `a_star` is `[0.01, 0, 0]`, etc., matching the old hard-coded values. |
| 2.B | **Implement Triclinic Correctness Test** | `[ ]` | **Why:** To validate the new formulas against the C-code ground truth. <br> **How:** Create `test_triclinic_correctness`. Call `compute_cell_tensors` with the `triclinic_P1` parameters. Assert that the returned `a,b,c,a*,b*,c*,V` tensors numerically match the values in `tests/golden_data/triclinic_P1/trace.log`. |
| 2.C | **Implement Metric Duality Test** | `[ ]` | **Why:** To verify the fundamental relationship between real and reciprocal space. <br> **How:** Create `test_metric_duality`. For a general triclinic cell, assert that `dot(a_star, a) ≈ 1`, `dot(a_star, b) ≈ 0`, etc., for all 9 pairs. **Tolerance:** `atol=1e-12`. |
| 2.D | **Implement Volume Identity Test** | `[ ]` | **Why:** To provide a redundant check on the volume calculation. <br> **How:** Create `test_volume_identity`. For a general triclinic cell, assert that the volume from the closed-form `sqrt` formula is equal to `dot(a, cross(b, c))`. **Tolerance:** `rtol=1e-12`. |
| 2.E | **Implement Resolution Shell Test** | `[ ]` | **Why:** To verify the d-spacing convention. <br> **How:** Create `test_resolution_shell_consistency`. For a random triclinic cell, calculate `G = h*a* + k*b* + l*c*` for a known `h,k,l`. Assert that `torch.norm(G) ≈ 1/d_hkl`. **Tolerance:** `rtol=5e-13`. |
| 2.F | **Implement Rotation Invariance Test** | `[ ]` | **Why:** To prove that the magnitude of a reciprocal lattice vector is independent of crystal orientation. <br> **How:** Create `test_rotation_invariance`. Calculate `G = h*a* + k*b* + l*c*`. Apply a random rotation matrix `R` to `a,b,c` and re-calculate `G_rotated`. Assert that `torch.norm(G) ≈ torch.norm(G_rotated)`. **Tolerance:** `atol=1e-12`. |
| **Section 3: Finalization** |
| 3.A | **Code Formatting & Linting** | `[ ]` | **Why:** To maintain code quality. <br> **How:** Run `black .` and `ruff . --fix` on all modified files. |
| 3.B | **Commit Phase 2 Work** | `[ ]` | **Why:** To checkpoint the completion of the core geometry engine. <br> **Commit Message:** `feat(geometry): Phase 2 - Implement differentiable triclinic geometry engine and unit tests` |

---

**Success Test (Acceptance Gate):**
*   All new unit tests in `tests/test_crystal_geometry.py` pass with the specified tolerances.
*   The `Crystal` class is fully refactored and no longer contains hard-coded lattice vectors.
