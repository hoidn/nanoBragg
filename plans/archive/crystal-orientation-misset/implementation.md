<!-- ACTIVE IMPLEMENTATION PLAN -->
<!-- DO NOT MISTAKE THIS FOR A TEMPLATE. THIS IS THE OFFICIAL SOURCE OF TRUTH FOR THE PROJECT'S PHASED PLAN. -->

# Phased Implementation Plan

**Project:** Crystal Orientation Misset
**Initiative Path:** `plans/active/crystal-orientation-misset/`

---
## Git Workflow Information
**Feature Branch:** feature/crystal-orientation-misset
**Baseline Branch:** feature/general-triclinic-cell-params
**Baseline Commit Hash:** bacc503183303f8baa407db564c709d3f6ef2953
**Last Phase Commit Hash:** bacc503183303f8baa407db564c709d3f6ef2953
---

**Created:** 2025-01-20
**Core Technologies:** PyTorch, Python, torch.autograd

---

## 📄 **DOCUMENT HIERARCHY**

This document orchestrates the implementation of the objective defined in the main R&D plan. The full set of documents for this initiative is:

- **`plan.md`** - The high-level R&D Plan
  - **`implementation.md`** - This file - The Phased Implementation Plan
    - `phase_1_checklist.md` - Detailed checklist for Phase 1
    - `phase_2_checklist.md` - Detailed checklist for Phase 2
    - `phase_3_checklist.md` - Detailed checklist for Phase 3
    - `phase_final_checklist.md` - Checklist for the Final Phase

---

## 🎯 **PHASE-BASED IMPLEMENTATION**

**Overall Goal:** Implement a differentiable three-angle static orientation system for crystals, enabling accurate simulation of arbitrarily oriented crystals and validation against the triclinic_P1 golden test case.

**Total Estimated Duration:** 3-4 days

---

## 📋 **IMPLEMENTATION PHASES**

### **Phase 1: Core Rotation Logic & Unit Testing**

**Goal:** To implement the foundational rotation matrix construction logic and validate it with comprehensive unit tests.

**Deliverable:** A new `angles_to_rotation_matrix` function in `utils/geometry.py` with passing unit tests for rotation conventions and edge cases.

**Estimated Duration:** 1 day

**Key Tasks:**
- Implement `angles_to_rotation_matrix` function with C-code reference (nanoBragg.c:3295-3347)
- Create unit tests for identity matrix at zero angles (tolerance 1e-12)
- Test standard 90° rotations around each axis
- Verify XYZ rotation order with non-commutative test cases
- Test rotation matrices are orthogonal (R @ R.T = I) with determinant = 1

**Dependencies:** None (first phase)

**Implementation Checklist:** `phase_1_checklist.md`

**Success Test:** `pytest tests/test_geometry.py::test_angles_to_rotation_matrix -v` completes with 100% pass rate.

---

### **Phase 2: Crystal Integration & Trace Validation**

**Goal:** To integrate the rotation logic into the Crystal class and validate against known values from the C-code trace logs.

**Deliverable:** An updated `Crystal` class with `_apply_static_orientation` method that correctly transforms reciprocal space vectors.

**Estimated Duration:** 1 day

**Key Tasks:**
- Implement `_apply_static_orientation` helper method in `Crystal` class
- Update `compute_cell_tensors` to apply misset rotation to reciprocal vectors (a*, b*, c*)
- Add unit test verifying reciprocal vectors match triclinic_P1 trace.log values
- Test with both tensor and float inputs for misset_deg parameter
- Verify backward compatibility (zero misset produces unchanged vectors)

**Dependencies:** Requires Phase 1 completion

**Implementation Checklist:** `phase_2_checklist.md`

**Success Test:** `pytest tests/test_crystal_geometry.py::test_misset_orientation -v` passes with reciprocal vectors matching trace.log within 1e-6 tolerance.

---

### **Phase 3: Full Simulator Integration & Golden Test**

**Goal:** To complete the integration into the full simulation pipeline and achieve the primary validation goal against the golden test case.

**Deliverable:** A fully integrated simulator that passes the triclinic_P1 golden test with ≥0.990 correlation.

**Estimated Duration:** 1 day

**Key Tasks:**
- Update `test_triclinic_P1_reproduction` to use misset_deg=(-89.968546, -31.328953, 177.753396)
- Debug any correlation issues using parallel trace comparison if needed
- Verify simple_cubic regression test continues to pass
- Add intermediate debug logging for rotation matrices if correlation < 0.990
- Profile performance impact (target: <5% slowdown)

**Dependencies:** Requires Phase 2 completion

**Implementation Checklist:** `phase_3_checklist.md`

**Success Test:** `pytest tests/test_suite.py::test_triclinic_P1_reproduction -v` achieves ≥0.990 Pearson correlation on masked pixels.

---

### **Final Phase: Gradient Tests & Documentation**

**Goal:** Validate differentiability of all misset parameters and finalize project documentation.

**Deliverable:** Complete gradient tests, updated documentation, and a feature-complete crystal orientation system.

**Estimated Duration:** 1 day

**Key Tasks:**
- Implement gradcheck tests for each misset angle (misset_deg_x, _y, _z)
- Test at non-zero angles (30°, 45°, 60°) to avoid degenerate Jacobian
- Mark heavy tests with @pytest.mark.slow decorator
- Update all "Future Work" comments in crystal.py
- Update rotation pipeline documentation
- Update README.md with new crystal orientation capabilities
- Verify all C-code references include line numbers

**Dependencies:** All previous phases complete

**Implementation Checklist:** `phase_final_checklist.md`

**Success Test:** All gradcheck tests pass with specified parameters (dtype=float64, eps=1e-6, atol=1e-6, rtol=1e-4).

---

## 📊 **PROGRESS TRACKING**

### Phase Status:
- [x] **Phase 1:** Core Rotation Logic & Unit Testing - 100% complete
- [ ] **Phase 2:** Crystal Integration & Trace Validation - 0% complete
- [ ] **Phase 3:** Full Simulator Integration & Golden Test - 0% complete
- [ ] **Final Phase:** Gradient Tests & Documentation - 0% complete

**Current Phase:** Phase 2: Crystal Integration & Trace Validation
**Overall Progress:** ████░░░░░░░░░░░░ 25%

---

## 🚀 **GETTING STARTED**

1.  **Generate Phase 1 Checklist:** Run `/phase-checklist 1` to create the detailed checklist.
2.  **Begin Implementation:** Follow the checklist tasks in order.
3.  **Track Progress:** Update task states in the checklist as you work.
4.  **Request Review:** Run `/complete-phase` when all Phase 1 tasks are done to generate a review request.

---

## ⚠️ **RISK MITIGATION**

**Potential Blockers:**
- **Risk:** Rotation convention mismatch between PyTorch and C implementation
  - **Mitigation:** Extensive unit tests comparing against known C-code values from trace.log
- **Risk:** Numerical precision issues in rotation composition
  - **Mitigation:** Use float64 for critical tests, implement careful tolerance checks
- **Risk:** Performance regression from additional matrix operations
  - **Mitigation:** Profile early, consider caching rotation matrices if angles are constant

**Rollback Plan:**
- **Git:** Each phase will be a separate, reviewed commit on the feature branch
- **Feature Flag:** The existing TODO placeholder allows easy disabling if issues arise
- **Test Suite:** Comprehensive tests ensure no silent failures