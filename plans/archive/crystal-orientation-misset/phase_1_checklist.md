# Phase 1: Core Rotation Logic & Unit Testing Checklist

**Initiative:** Crystal Orientation Misset
**Created:** 2025-01-20
**Phase Goal:** To implement the foundational rotation matrix construction logic and validate it with comprehensive unit tests.
**Deliverable:** A new `angles_to_rotation_matrix` function in `utils/geometry.py` with passing unit tests for rotation conventions and edge cases.

## ✅ Task List

### Instructions:
1.  Work through tasks in order. Dependencies are noted in the guidance column.
2.  The **"How/Why & API Guidance"** column contains all necessary details for implementation.
3.  Update the `State` column as you progress: `[ ]` (Open) -> `[P]` (In Progress) -> `[D]` (Done).

---

| ID  | Task Description                                   | State | How/Why & API Guidance |
| :-- | :------------------------------------------------- | :---- | :------------------------------------------------- |
| **Section 0: Preparation & Context Priming** |
| 0.A | **Review Key Documents & C-Code References**       | `[D]` | **Why:** To understand the exact rotation convention and implementation details from the C-code. <br> **Docs:** `plans/active/crystal-orientation-misset/implementation.md`, `nanoBragg.c` (lines 3295-3347 for rotate function, lines 1911-1916 for misset application). <br> **Key insight:** Misset is applied to reciprocal space vectors using XYZ Euler angles. |
| 0.B | **Review Existing Geometry Utilities**             | `[D]` | **Why:** To understand existing rotation functions and maintain consistency. <br> **Files:** `src/nanobrag_torch/utils/geometry.py` (review `rotate_axis`, `rotate_umat`). <br> **Note:** Check import structure and tensor handling patterns. |
| 0.C | **Identify Test Infrastructure**                   | `[D]` | **Why:** To determine where to add new tests and understand test patterns. <br> **Files:** `tests/test_crystal_geometry.py` (existing file with test infrastructure). <br> **Note:** Tests should use the existing `CrystalGeometryTest` class structure. |
| **Section 1: Implement Core Rotation Function** |
| 1.A | **Create `angles_to_rotation_matrix` Function**    | `[D]` | **Why:** This is the foundational function that converts three Euler angles to a rotation matrix. <br> **File:** `src/nanobrag_torch/utils/geometry.py` <br> **Function Signature:** `def angles_to_rotation_matrix(phi_x: torch.Tensor, phi_y: torch.Tensor, phi_z: torch.Tensor) -> torch.Tensor:` <br> **Docstring MUST include:** C-code reference from nanoBragg.c:3295-3347 |
| 1.B | **Implement X-axis Rotation Matrix**               | `[D]` | **Why:** First component of the XYZ Euler angle sequence. <br> **Formula:** <br> `Rx = [[1, 0, 0], [0, cos(phi_x), -sin(phi_x)], [0, sin(phi_x), cos(phi_x)]]` <br> **Note:** Use `torch.cos` and `torch.sin` for differentiability. |
| 1.C | **Implement Y-axis Rotation Matrix**               | `[D]` | **Why:** Second component of the XYZ Euler angle sequence. <br> **Formula:** <br> `Ry = [[cos(phi_y), 0, sin(phi_y)], [0, 1, 0], [-sin(phi_y), 0, cos(phi_y)]]` <br> **Note:** Pay attention to sign conventions for active rotations. |
| 1.D | **Implement Z-axis Rotation Matrix**               | `[D]` | **Why:** Third component of the XYZ Euler angle sequence. <br> **Formula:** <br> `Rz = [[cos(phi_z), -sin(phi_z), 0], [sin(phi_z), cos(phi_z), 0], [0, 0, 1]]` <br> **Note:** This completes the rotation sequence. |
| 1.E | **Compose Rotation Matrices in XYZ Order**         | `[D]` | **Why:** The C-code applies rotations in X→Y→Z order (extrinsic rotations). <br> **Implementation:** `R = Rz @ Ry @ Rx` <br> **Critical:** Matrix multiplication order matters! This gives the correct XYZ Euler angle convention. |
| 1.F | **Add Device and Dtype Handling**                  | `[D]` | **Why:** Ensure the function works with different tensor devices and dtypes. <br> **Implementation:** Extract device and dtype from input angles, construct matrices with same properties. <br> **Pattern:** `device = phi_x.device; dtype = phi_x.dtype` |
| **Section 2: Unit Tests for Rotation Function** |
| 2.A | **Create Test Class Structure**                    | `[D]` | **Why:** Organize rotation tests systematically. <br> **File:** `tests/test_crystal_geometry.py` <br> **Add:** New test methods to existing `CrystalGeometryTest` class. <br> **Import:** Add `from nanobrag_torch.utils.geometry import angles_to_rotation_matrix` |
| 2.B | **Implement Identity Rotation Test**               | `[D]` | **Why:** Verify the baseline case where no rotation is applied. <br> **Test Name:** `test_angles_to_rotation_matrix_identity` <br> **Implementation:** Call with angles (0, 0, 0), assert result equals identity matrix. <br> **Tolerance:** `torch.allclose(R, torch.eye(3), atol=1e-12)` |
| 2.C | **Test 90° X-axis Rotation**                       | `[D]` | **Why:** Verify correct rotation convention for X-axis. <br> **Test Name:** `test_angles_to_rotation_matrix_x_rotation` <br> **Test:** Rotate [0, 1, 0] by 90° around X → expect [0, 0, 1] <br> **Implementation:** `R @ torch.tensor([0., 1., 0.])` <br> **Tolerance:** `atol=1e-10` |
| 2.D | **Test 90° Y-axis Rotation**                       | `[D]` | **Why:** Verify correct rotation convention for Y-axis. <br> **Test Name:** `test_angles_to_rotation_matrix_y_rotation` <br> **Test:** Rotate [1, 0, 0] by 90° around Y → expect [0, 0, -1] <br> **Note:** Sign is critical for active vs passive rotation verification. |
| 2.E | **Test 90° Z-axis Rotation**                       | `[D]` | **Why:** Verify correct rotation convention for Z-axis. <br> **Test Name:** `test_angles_to_rotation_matrix_z_rotation` <br> **Test:** Rotate [1, 0, 0] by 90° around Z → expect [0, 1, 0] <br> **Pattern:** Similar to X and Y tests. |
| 2.F | **Test Non-Commutative Rotation Order**            | `[D]` | **Why:** Verify XYZ order is correctly implemented (not ZYX or other). <br> **Test Name:** `test_angles_to_rotation_matrix_order` <br> **Test:** Apply (30°, 45°, 60°) rotation and compare to known result. <br> **Alternative:** Apply X then Y rotation vs Y then X, verify different results. |
| 2.G | **Test Rotation Matrix Properties**                | `[D]` | **Why:** All rotation matrices must be orthogonal with determinant +1. <br> **Test Name:** `test_angles_to_rotation_matrix_properties` <br> **Tests:** <br> 1. `R @ R.T ≈ I` (orthogonality) <br> 2. `det(R) ≈ 1` (proper rotation) <br> **Test multiple angles:** (0,0,0), (45,30,60), (90,90,90) |
| 2.H | **Test Tensor Input Handling**                     | `[D]` | **Why:** Ensure function works with different tensor types. <br> **Test Name:** `test_angles_to_rotation_matrix_tensor_types` <br> **Test Cases:** <br> 1. Float tensors <br> 2. Double tensors (float64) <br> 3. GPU tensors (if available) <br> **Verify:** Output has same device/dtype as input |
| **Section 3: Integration Preparation** |
| 3.A | **Add Import to Crystal Module**                   | `[D]` | **Why:** Make the new function available for Phase 2 integration. <br> **File:** `src/nanobrag_torch/models/crystal.py` <br> **Add:** `from ..utils.geometry import angles_to_rotation_matrix` <br> **Location:** Add with other geometry imports near top of file. |
| 3.B | **Run All Geometry Tests**                         | `[D]` | **Why:** Ensure no regressions and all new tests pass. <br> **Command:** `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_crystal_geometry.py -v` <br> **Expected:** All tests pass, especially new rotation tests. |
| **Section 4: Documentation & Code Quality** |
| 4.A | **Add Type Hints**                                 | `[D]` | **Why:** Maintain code quality and enable static type checking. <br> **Verify:** All new functions have complete type hints for parameters and return values. <br> **Pattern:** Use `torch.Tensor` for tensor types. |
| 4.B | **Format Code with Black**                         | `[D]` | **Why:** Maintain consistent code formatting. <br> **Command:** `black src/nanobrag_torch/utils/geometry.py tests/test_crystal_geometry.py` <br> **Note:** Run on all modified files. |
| 4.C | **Run Linting Checks**                             | `[D]` | **Why:** Catch potential issues and maintain code quality. <br> **Commands:** <br> 1. `ruff src/nanobrag_torch/utils/geometry.py --fix` <br> 2. `ruff tests/test_crystal_geometry.py --fix` <br> **Fix:** Any reported issues. |
| **Section 5: Phase Completion** |
| 5.A | **Verify Success Criteria**                        | `[D]` | **Why:** Ensure phase deliverables are met before proceeding. <br> **Check:** <br> 1. `angles_to_rotation_matrix` function exists and is documented <br> 2. All rotation tests pass <br> 3. No regressions in existing tests |
| 5.B | **Commit Phase 1 Work**                            | `[D]` | **Why:** Create a clean checkpoint for Phase 1 completion. <br> **Git Commands:** <br> 1. `git add -A` <br> 2. `git status` (verify correct files) <br> 3. `git commit -m "feat(geometry): Phase 1 - Implement angles_to_rotation_matrix with comprehensive tests"` |

---

## 🎯 Success Criteria

**This phase is complete when:**
1.  All tasks in the table above are marked `[D]` (Done).
2.  The phase success test passes: `pytest tests/test_crystal_geometry.py::test_angles_to_rotation_matrix -v` completes with 100% pass rate.
3.  No regressions are introduced in the existing test suite.
4.  The `angles_to_rotation_matrix` function is properly documented with C-code references.