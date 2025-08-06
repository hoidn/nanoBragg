<!-- ACTIVE IMPLEMENTATION PLAN -->
<!-- DO NOT MISTAKE THIS FOR A TEMPLATE. THIS IS THE OFFICIAL SOURCE OF TRUTH FOR THE PROJECT'S PHASED PLAN. -->

# Phased Implementation Plan

**Project:** General and Differentiable Detector Geometry
**Initiative Path:** `plans/active/general-detector-geometry/`

---
## Git Workflow Information
**Feature Branch:** feature/general-detector-geometry
**Baseline Branch:** feature/crystal-orientation-misset
**Baseline Commit Hash:** ebac61b2631d444e6b9162b0bc1680b7b0f1a023
**Last Phase Commit Hash:** ec66e7d86cf6ea3ad7970fc9bb8d68bb1e7d3c11
---

**Created:** 2025-08-05
**Core Technologies:** Python, PyTorch, NumPy

---

## 📄 **DOCUMENT HIERARCHY**

This document orchestrates the implementation of the objective defined in the main R&D plan. The full set of documents for this initiative is:

- **`plan.md`** - The high-level R&D Plan
  - **`implementation.md`** - This file - The Phased Implementation Plan
    - `phase_1_checklist.md` - Detailed checklist for Phase 1
    - `phase_2_checklist.md` - Detailed checklist for Phase 2
    - `phase_3_checklist.md` - Detailed checklist for Phase 3
    - `phase_4_checklist.md` - Detailed checklist for Phase 4
    - `phase_final_checklist.md` - Checklist for the Final Phase

---

## 🎯 **PHASE-BASED IMPLEMENTATION**

**Overall Goal:** Replace the static detector model with a fully configurable, general-purpose detector that derives its geometry from user-provided parameters, enabling simulation of realistic experimental setups.

**Total Estimated Duration:** 4 days

---

## 📋 **IMPLEMENTATION PHASES**

### **Phase 1: DetectorConfig and Unit Conversion Foundation**

**Goal:** To implement a complete DetectorConfig dataclass with all necessary geometric parameters and establish the unit conversion framework.
**Deliverable:** A fully populated `DetectorConfig` class with unit conversion methods and basic validation.
**Estimated Duration:** 0.5 days

**Key Modules & APIs to Touch:**
- `src/nanobrag_torch/config.py`: Complete the `DetectorConfig` dataclass
- `src/nanobrag_torch/models/detector.py`: Update `__init__` to accept DetectorConfig
- `src/nanobrag_torch/utils/units.py`: Create new file for unit conversion utilities

**Potential Gotchas & Critical Conventions:**
- The DetectorConfig must accept user-friendly units (mm) but all internal calculations use Angstroms
- Parameters that need tensor support: distance, beam_center_s/f, all rotation angles
- The detector convention (MOSFLM vs XDS) affects the initial orientation of basis vectors
- Beam center can be specified as either (Xbeam, Ybeam) in mm or (ORGX, ORGY) in pixels

**Implementation Checklist:** `phase_1_checklist.md`
**Success Test:** `pytest tests/test_detector_config.py` - all configuration tests pass.

---

### **Phase 2: Dynamic Basis Vector Calculation**

**Goal:** To implement the _calculate_basis_vectors method that correctly applies all detector rotations and positioning.
**Deliverable:** A working implementation that matches C-code behavior for detector orientation and positioning.
**Estimated Duration:** 1 day

**Key Modules & APIs to Touch:**
- `src/nanobrag_torch/models/detector.py`: Implement `_calculate_basis_vectors()` method
- `src/nanobrag_torch/utils/geometry.py`: Use existing `rotate()` and `rotate_axis()` functions
- `golden_suite_generator/`: Generate C-code traces for basis vector validation

**Potential Gotchas & Critical Conventions:**
- Rotation order is critical: detector_rotx/y/z are applied first, then twotheta
- The detector pivot mode (SAMPLE vs BEAM) changes when pix0_vector is calculated
- The C-code uses 1-indexed arrays; PyTorch uses 0-indexed
- Initial basis vectors depend on detector convention (MOSFLM: f=[0,0,-1], s=[1,0,0] vs XDS: f=[1,0,0], s=[0,1,0])
- The twotheta rotation is around an arbitrary axis, not a coordinate axis

**Implementation Checklist:** `phase_2_checklist.md`
**Success Test:** Basis vectors from PyTorch match C-code trace output with atol=1e-9.

---

### **Phase 3: Golden Test Case Generation**

**Goal:** To generate the cubic_tilted_detector golden test case with comprehensive trace data.
**Deliverable:** Complete golden test artifacts including high-precision trace logs of detector geometry.
**Estimated Duration:** 0.5 days

**Key Modules & APIs to Touch:**
- `golden_suite_generator/nanoBragg.c`: Add trace statements for detector basis vectors
- `golden_suite_generator/generate_golden.sh`: Add cubic_tilted_detector case
- `tests/golden_data/cubic_tilted_detector/`: New directory for test artifacts

**Potential Gotchas & Critical Conventions:**
- Trace output must use %.15g format for full double precision
- Must trace: fdet_vec, sdet_vec, odet_vec, pix0_vector after all rotations
- Test parameters: twotheta=15°, beam_center offset by 10mm in both directions
- Include detector_rotx=5°, detector_roty=3°, detector_rotz=2° for comprehensive testing

**Implementation Checklist:** `phase_3_checklist.md`
**Success Test:** Golden data generated with complete trace.log containing detector vectors.

---

### **Phase 4: Integration and Backward Compatibility**

**Goal:** To integrate the new dynamic detector with the simulator while maintaining backward compatibility.
**Deliverable:** Updated Detector class that works for both simple_cubic and cubic_tilted_detector cases.
**Estimated Duration:** 1 day

**Key Modules & APIs to Touch:**
- `src/nanobrag_torch/models/detector.py`: Update `get_pixel_coords()` to use calculated basis
- `tests/test_suite.py`: Add `test_cubic_tilted_detector_reproduction`
- `src/nanobrag_torch/simulator.py`: Ensure simulator passes DetectorConfig correctly
- `scripts/verify_detector_geometry.py`: Create new script for visual validation

**Potential Gotchas & Critical Conventions:**
- The simple_cubic test uses hard-coded values that must still work
- When DetectorConfig is None or uses defaults, must reproduce hard-coded behavior exactly
- The pixel coordinate generation depends on correct basis vectors and pix0_vector
- Coordinate system convention: pixels are indexed as (slow, fast) matching fabio/matplotlib

**Implementation Checklist:** `phase_4_checklist.md`
**Success Test:** Both simple_cubic and cubic_tilted_detector achieve ≥0.990 correlation.

---

### **Final Phase: Validation, Gradients & Documentation**

**Goal:** Validate differentiability, add gradient tests, and document the complete detector geometry system.
**Deliverable:** Fully tested, differentiable detector geometry with comprehensive documentation.
**Estimated Duration:** 1 day

**Key Modules & APIs to Touch:**
- `tests/test_detector_geometry.py`: Create comprehensive unit and gradient tests
- `docs/detector_geometry.md`: Create visual documentation of rotation conventions
- `README.md`: Update with detector configuration examples

**Key Tasks Summary:**
- Create a visual verification script that generates images of the baseline and tilted detector configurations to provide an intuitive check of correctness.

**Potential Gotchas & Critical Conventions:**
- Gradient tests must use float64 for numerical stability
- Test gradients for: distance, beam_center_s/f, all rotation angles
- Document the rotation order and axis conventions clearly with diagrams
- Performance: cache basis vectors when config hasn't changed

**Implementation Checklist:** `phase_final_checklist.md`
**Success Test:** All gradient checks pass, documentation is complete, no performance regression.

---

## 📊 **PROGRESS TRACKING**

### Phase Status:
- [x] **Phase 1:** DetectorConfig and Unit Conversion Foundation - 100% complete ✅
- [x] **Phase 2:** Dynamic Basis Vector Calculation - 100% complete ✅
- [x] **Phase 3:** Golden Test Case Generation - 100% complete ✅
- [x] **Phase 4:** Integration and Backward Compatibility - 100% complete ✅
- [ ] **Final Phase:** Validation, Gradients & Documentation - 0% complete

**Current Phase:** Final Phase: Validation, Gradients & Documentation  
**Overall Progress:** ████████████████ 80%

---

## 🚀 **GETTING STARTED**

1. **Generate Phase 1 Checklist:** Run `/phase-checklist 1` to create the detailed checklist.
2. **Begin Implementation:** Follow the checklist tasks in order.
3. **Track Progress:** Update task states in the checklist as you work.
4. **Request Review:** Run `/complete-phase` when all Phase 1 tasks are done to generate a review request.

---

## ⚠️ **RISK MITIGATION**

**Potential Blockers:**
- **Risk:** The rotation conventions between C-code and PyTorch might differ (intrinsic vs extrinsic).
  - **Mitigation:** Create isolated rotation tests for each axis and compare with C-code output.
- **Risk:** Numerical precision differences between C doubles and PyTorch tensors.
  - **Mitigation:** Use torch.float64 throughout and set appropriate tolerances (1e-9 for positions, 1e-12 for unit vectors).
- **Risk:** The existing simple_cubic test might break with dynamic geometry.
  - **Mitigation:** Add a compatibility mode that exactly reproduces hard-coded values when using default config.

**Rollback Plan:**
- **Git:** Each phase will be a separate, reviewed commit on the feature branch, allowing for easy reverts.
- **Feature Flag:** Consider adding `use_dynamic_geometry` flag to DetectorConfig for gradual rollout.