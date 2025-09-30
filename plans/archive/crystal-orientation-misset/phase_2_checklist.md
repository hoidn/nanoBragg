# Phase 2: Crystal Integration & Trace Validation Checklist

**Initiative:** Crystal Orientation Misset
**Created:** 2025-01-29
**Phase Goal:** To integrate the rotation logic into the Crystal class and validate against known values from the C-code trace logs.
**Deliverable:** An updated `Crystal` class with `_apply_static_orientation` method that correctly transforms reciprocal space vectors.

## ✅ Task List

### Instructions:
1.  Work through tasks in order. Dependencies are noted in the guidance column.
2.  The **"How/Why & API Guidance"** column contains all necessary details for implementation.
3.  Update the `State` column as you progress: `[ ]` (Open) -> `[P]` (In Progress) -> `[D]` (Done).

---

| ID  | Task Description                                   | State | How/Why & API Guidance |
| :-- | :------------------------------------------------- | :---- | :------------------------------------------------- |
| **Section 0: Preparation & Context Loading** |
| 0.A | **Review triclinic_P1 trace.log values**           | `[D]` | **Why:** To understand the expected reciprocal vector values after misset rotation. <br> **File:** Look for trace.log or golden reference data in tests/golden_data/. <br> **Key values:** Find reciprocal vectors (a*, b*, c*) after misset=(-89.968546, -31.328953, 177.753396) degrees. |
| 0.B | **Study Crystal class structure**                  | `[D]` | **Why:** To understand where to integrate the misset rotation logic. <br> **File:** `src/nanobrag_torch/models/crystal.py` <br> **Focus on:** `compute_cell_tensors()` method, property definitions for a_star, b_star, c_star. |
| 0.C | **Review CrystalConfig parameters**                | `[D]` | **Why:** To understand how to add misset_deg parameter. <br> **File:** `src/nanobrag_torch/config.py` <br> **Check:** Existing parameter structure, default values pattern. |
| **Section 1: Add misset_deg to CrystalConfig** |
| 1.A | **Add misset_deg parameter to CrystalConfig**      | `[D]` | **Why:** The Crystal class needs access to misset angles through its config. <br> **File:** `src/nanobrag_torch/config.py` <br> **Add:** `misset_deg: Tuple[float, float, float] = (0.0, 0.0, 0.0)` <br> **Type:** Support both float tuples and tensor tuples for differentiability. |
| 1.B | **Update CrystalConfig docstring**                 | `[D]` | **Why:** Document the new parameter for users. <br> **Add:** Description of misset_deg as "Static crystal orientation angles (degrees) applied as XYZ rotations to reciprocal space vectors." <br> **Note:** Emphasize that angles are in degrees, not radians. |
| **Section 2: Implement Crystal Misset Logic** |
| 2.A | **Create _apply_static_orientation helper method** | `[D]` | **Why:** Encapsulate the misset rotation logic in a dedicated method. <br> **File:** `src/nanobrag_torch/models/crystal.py` <br> **Signature:** `def _apply_static_orientation(self, vectors: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:` <br> **C-Code Reference:** Include reference to nanoBragg.c lines 1911-1916 in docstring. |
| 2.B | **Convert misset angles to radians**               | `[D]` | **Why:** angles_to_rotation_matrix expects radians but config uses degrees. <br> **Implementation:** Convert each misset_deg component using `torch.deg2rad()` <br> **Handle:** Both tensor and float inputs from config. |
| 2.C | **Apply rotation to reciprocal vectors**           | `[D]` | **Why:** The C-code applies misset to a_star, b_star, c_star (not real space). <br> **Implementation:** Use `rotate_umat` with the rotation matrix from `angles_to_rotation_matrix`. <br> **Apply to:** vectors["a_star"], vectors["b_star"], vectors["c_star"]. |
| 2.D | **Integrate into compute_cell_tensors**            | `[D]` | **Why:** The misset rotation must be applied after reciprocal vector calculation. <br> **Location:** After reciprocal vectors are calculated but before cross products. <br> **Pattern:** `if any(m != 0 for m in self.config.misset_deg): vectors = self._apply_static_orientation(vectors)` |
| **Section 3: Create Comprehensive Unit Tests** |
| 3.A | **Create test_misset_orientation test method**     | `[D]` | **Why:** Primary validation test against C-code trace values. <br> **File:** `tests/test_crystal_geometry.py` <br> **Test name:** `test_misset_orientation` in TestCrystalGeometry class. <br> **Setup:** Use triclinic_P1 parameters with misset=(-89.968546, -31.328953, 177.753396). |
| 3.B | **Add expected reciprocal vectors from trace**     | `[D]` | **Why:** Need ground truth values for comparison. <br> **Source:** Extract from triclinic_P1 trace.log or golden reference. <br> **Format:** `expected_a_star = torch.tensor([...], dtype=torch.float64)` <br> **Tolerance:** Use 1e-6 for comparison with C-code values. |
| 3.C | **Test zero misset backward compatibility**        | `[D]` | **Why:** Ensure no rotation is applied when misset_deg=(0,0,0). <br> **Test name:** `test_misset_zero_rotation` <br> **Verify:** Reciprocal vectors unchanged when misset is zero. <br> **Use:** Existing triclinic test case for comparison. |
| 3.D | **Test tensor input compatibility**                | `[D]` | **Why:** Ensure misset_deg works with both float tuples and tensor tuples. <br> **Test name:** `test_misset_tensor_inputs` <br> **Cases:** 1) Float tuple: (30.0, 45.0, 60.0), 2) Tensor tuple with requires_grad=True. <br> **Verify:** Same results regardless of input type. |
| **Section 4: Validate Rotation Order** |
| 4.A | **Create rotation order validation test**          | `[D]` | **Why:** Confirm XYZ rotation order matches C-code exactly. <br> **Test name:** `test_misset_rotation_order` <br> **Method:** Apply known angles and compare to manually computed result. <br> **Key:** Test with non-commutative angles like (30°, 45°, 60°). |
| 4.B | **Add debug output for trace comparison**          | `[D]` | **Why:** Help debug any mismatches with C-code values. <br> **Add:** Optional print statements showing computed vs expected vectors. <br> **Format:** Match trace.log format for easy comparison. |
| **Section 5: Property and Gradient Flow** |
| 5.A | **Verify properties use rotated vectors**          | `[D]` | **Why:** Crystal.a_star property must return the rotated vector. <br> **Test:** Access crystal.a_star after setting misset and verify rotation applied. <br> **Critical:** Properties must not cache pre-rotation values. |
| 5.B | **Test gradient flow through misset**              | `[D]` | **Why:** Ensure differentiability is maintained. <br> **Test name:** `test_misset_gradient_flow` <br> **Setup:** Create misset angles with requires_grad=True, compute loss using rotated vectors. <br> **Verify:** Gradients flow back to misset_deg parameters. |
| **Section 6: Documentation and Code Quality** |
| 6.A | **Update Crystal class docstring**                 | `[D]` | **Why:** Document the new misset functionality. <br> **Add:** Explanation of misset rotation in class docstring. <br> **Include:** Reference to rotation pipeline order. |
| 6.B | **Run formatter and linter**                       | `[D]` | **Why:** Maintain code quality standards. <br> **Commands:** `black` on modified files, `ruff` for linting. <br> **Fix:** Any formatting or linting issues. |
| **Section 7: Final Validation** |
| 7.A | **Run all crystal geometry tests**                 | `[D]` | **Why:** Ensure no regressions in existing functionality. <br> **Command:** `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src:$PYTHONPATH pytest tests/test_crystal_geometry.py -v` <br> **Expected:** All tests pass including new misset tests. |
| 7.B | **Verify success criteria**                        | `[D]` | **Why:** Confirm phase deliverables are met. <br> **Check:** 1) _apply_static_orientation implemented, 2) test_misset_orientation passes, 3) Vectors match trace.log within 1e-6. |

---

## 🎯 Success Criteria

**This phase is complete when:**
1.  All tasks in the table above are marked `[D]` (Done).
2.  The phase success test passes: `pytest tests/test_crystal_geometry.py::test_misset_orientation -v` passes with reciprocal vectors matching trace.log within 1e-6 tolerance.
3.  No regressions are introduced in the existing test suite.
4.  Gradient flow is maintained through misset parameters.