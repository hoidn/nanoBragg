# Phase 2: Core Geometry Engine & Unit Testing Checklist

**Initiative:** General Triclinic Cell Parameters
**Created:** 2025-07-29
**Phase Goal:** Implement the differentiable geometry calculations that transform cell parameters to vectors.
**Deliverable:** A working `compute_cell_tensors` method with comprehensive unit tests.

## ✅ Task List

### Instructions:
1. Work through tasks in order. Dependencies are noted in the guidance column.
2. The **"How/Why & API Guidance"** column contains all necessary details for implementation.
3. Update the `State` column as you progress: `[ ]` (Open) -> `[P]` (In Progress) -> `[D]` (Done).

---

| ID | Task Description | State | How/Why & API Guidance |
| :--- | :--- | :--- | :--- |
| **Section 0: Preparation & Context Priming** |
| 0.A | **Review Key Documents** | `[D]` | **Why:** To load the necessary context and technical specifications before coding. <br> **Docs:** `plans/active/general-triclinic-cell-params/implementation.md` (Phase 2 section), `tests/golden_data/triclinic_P1/trace.log` (for ground-truth values), `CLAUDE.md` (crystallographic conventions). |
| 0.B | **Identify Target Files for Modification** | `[D]` | **Why:** To have a clear list of files that will be touched during this phase. <br> **Files:** `src/nanobrag_torch/models/crystal.py` (Modify), `tests/test_crystal_geometry.py` (Modify). |
| **Section 1: Implement Core Geometry Logic** |
| 1.A | **Refactor `Crystal.__init__`** | `[D]` | **Why:** To remove hard-coded vectors and prepare for dynamic calculation. <br> **How:** Remove the hard-coded `self.a`, `self.b`, `self.c`, `self.a_star`, etc. tensors. The `__init__` method should now primarily store the `CrystalConfig` and basic parameters like `N_cells`. |
| 1.B | **Implement `compute_cell_tensors` Method** | `[D]` | **Why:** To create the central, differentiable function for all geometry calculations. <br> **How:** In `src/nanobrag_torch/models/crystal.py`, create a new method `compute_cell_tensors(self)`. Implement the exact, numerically stable formulas using `torch.float64`. <br> **Formula:** <br> a = (a, 0, 0) <br> b = (b*cos(γ), b*sin(γ), 0) <br> cx = c*cos(β) <br> cy = c*(cos(α) - cos(β)*cos(γ)) / sin(γ) <br> cz = c * sqrt(clamp_min(1 - cos²(β) - cy²/c², eps)) <br> V = dot(a, cross(b, c)) <br> a* = cross(b, c) / V <br> b* = cross(c, a) / V <br> c* = cross(a, b) / V <br> **Return:** A dictionary of tensors: `{ "a": a_vec, "b": b_vec, "c": c_vec, "a_star": a_star, "b_star": b_star, "c_star": c_star, "V": V }`. |
| 1.C | **Implement Orientation Matrix Application** | `[D]` | **Why:** To apply the crystal's orientation after calculating the base lattice vectors, following the C-code's logical flow. <br> **How:** The `compute_cell_tensors` method should check if `self.config.misset_deg` is non-zero. If so, calculate the orientation matrix and apply it to the calculated `a,b,c` and `a*,b*,c*` vectors before they are returned. |
| 1.D | **Update Crystal Properties** | `[D]` | **Why:** To make the crystal vectors accessible as properties that dynamically calculate from cell parameters. <br> **How:** Convert `self.a`, `self.b`, `self.c`, `self.a_star`, `self.b_star`, `self.c_star`, and `self.V` to `@property` methods that call `compute_cell_tensors()` and return the appropriate tensor. Use `@functools.lru_cache(maxsize=1)` to avoid redundant calculations. |
| **Section 2: Unit Testing** |
| 2.A | **Implement Cubic Regression Test** | `[D]` | **Why:** To ensure the new general formulas correctly reproduce the simple cubic case. <br> **How:** In `tests/test_crystal_geometry.py`, create `test_cubic_regression`. Call `compute_cell_tensors` with cubic parameters (100, 100, 100, 90, 90, 90). Assert that the returned `a_star` is `[0.01, 0, 0]`, etc., matching the old hard-coded values. |
| 2.B | **Implement Triclinic Correctness Test** | `[D]` | **Why:** To validate the new formulas against the C-code ground truth. <br> **How:** Create `test_triclinic_correctness`. Call `compute_cell_tensors` with the `triclinic_P1` parameters (70, 80, 90, 75, 85, 95). Assert that the returned `a,b,c,a*,b*,c*,V` tensors numerically match the values in `tests/golden_data/triclinic_P1/trace.log`. |
| 2.C | **Implement Metric Duality Test** | `[D]` | **Why:** To verify the fundamental relationship between real and reciprocal space. <br> **How:** Create `test_metric_duality`. For a general triclinic cell, assert that `dot(a_star, a) ≈ 1`, `dot(a_star, b) ≈ 0`, etc., for all 9 pairs. **Tolerance:** `atol=1e-12`. |
| 2.D | **Implement Volume Identity Test** | `[D]` | **Why:** To provide a redundant check on the volume calculation. <br> **How:** Create `test_volume_identity`. For a general triclinic cell, assert that the volume from the closed-form formula `V = abc*sqrt(1 + 2*cos(α)*cos(β)*cos(γ) - cos²(α) - cos²(β) - cos²(γ))` equals `dot(a, cross(b, c))`. **Tolerance:** `rtol=1e-12`. |
| 2.E | **Implement Resolution Shell Test** | `[D]` | **Why:** To verify the d-spacing convention |G|=1/d. <br> **How:** Create `test_resolution_shell_consistency`. For a random triclinic cell, calculate `G = h*a* + k*b* + l*c*` for a known `h,k,l`. Assert that `torch.norm(G) ≈ 1/d_hkl`. **Tolerance:** `rtol=5e-13`. |
| 2.F | **Implement Rotation Invariance Test** | `[D]` | **Why:** To prove that the magnitude of a reciprocal lattice vector is independent of crystal orientation. <br> **How:** Create `test_rotation_invariance`. Calculate `G = h*a* + k*b* + l*c*`. Apply a random rotation matrix `R` to `a,b,c` and re-calculate `G_rotated`. Assert that `torch.norm(G) ≈ torch.norm(G_rotated)`. **Tolerance:** `atol=1e-12`. |
| **Section 3: Edge Cases & Numerical Stability** |
| 3.A | **Test Degenerate Cell Handling** | `[D]` | **Why:** To ensure numerical stability for extreme cell parameters. <br> **How:** Create `test_degenerate_cells`. Test with nearly-zero angles (1°), nearly-180° angles (179°), and very small/large cell dimensions. Assert no NaN/Inf values in outputs. |
| 3.B | **Test Gradient Flow** | `[D]` | **Why:** To verify differentiability is maintained. <br> **How:** Create `test_gradient_flow`. Create a simple loss using cell parameters, call `.backward()`, and verify all cell parameter tensors have non-None gradients. |
| **Section 4: Finalization** |
| 4.A | **Code Formatting & Linting** | `[D]` | **Why:** To maintain code quality. <br> **How:** Run `black .` and `ruff . --fix` on all modified files. Ensure KMP_DUPLICATE_LIB_OK=TRUE is set for all PyTorch operations. |
| 4.B | **Run All Tests** | `[D]` | **Why:** To ensure no regressions and all new functionality works. <br> **How:** Run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_crystal_geometry.py -v` and verify all tests pass. |
| 4.C | **Commit Phase 2 Work** | `[D]` | **Why:** To checkpoint the completion of the core geometry engine. <br> **Commit Message:** `feat(geometry): Phase 2 - Implement differentiable triclinic geometry engine and unit tests` |

---

## 🎯 Success Criteria

**This phase is complete when:**
1. All tasks in the table above are marked `[D]` (Done).
2. The phase success test passes: All geometry unit tests pass with >1e-10 precision.
3. The `Crystal` class is fully refactored and no longer contains hard-coded lattice vectors.
4. All cell parameter tensors maintain gradient flow for differentiability.