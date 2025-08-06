# Review Request: Phase 2 - Dynamic Basis Vector Calculation

**Initiative:** General Detector Geometry
**Generated:** 2025-08-05 21:21:14

This document contains all necessary information to review the work completed for Phase 2.

## Instructions for Reviewer

1.  Analyze the planning documents and the code changes (`git diff`) below.
2.  Create a new file named `review_phase_2.md` in this same directory (`plans/active/general-detector-geometry/`).
3.  In your review file, you **MUST** provide a clear verdict on a single line: `VERDICT: ACCEPT` or `VERDICT: REJECT`.
4.  If rejecting, you **MUST** provide a list of specific, actionable fixes under a "Required Fixes" heading.

---
## 1. Planning Documents

### R&D Plan (`plan.md`)
```markdown
# R&D Plan: General Detector Geometry

*Created: 2025-08-05*

## 🎯 **OBJECTIVE & HYPOTHESIS**

**Project/Initiative Name:** General and Differentiable Detector Geometry

**Problem Statement:** The current PyTorch simulator is limited by a hard-coded, static detector model. This prevents the simulation of realistic experimental setups with varying detector distances, positions, and orientations, making it impossible to compare simulations against most real-world experimental data.

**Proposed Solution / Hypothesis:** We will replace the static detector with a fully configurable, general-purpose model that derives its geometry from user-provided parameters. We hypothesize that by implementing all geometric transformations as differentiable PyTorch operations, we will enable the refinement of experimental geometry parameters (e.g., distance, beam center, tilt), a critical capability for analyzing real diffraction data.

**Scope & Deliverables:**
- A completed `DetectorConfig` dataclass with all key geometric parameters
- A refactored `Detector` class that dynamically calculates its geometry from the config
- A new `cubic_tilted_detector` golden test case for validation, including all standard artifacts (`image.bin`, `trace.log`, `params.json`, `regenerate_golden.sh`)
- A full suite of unit, integration, and gradcheck tests to verify correctness and differentiability
- Updated documentation, including a visual schematic of the rotation order, on how to configure and use the general detector model
- A visual verification script (`scripts/verify_detector_geometry.py`) and its corresponding output images, demonstrating the effect of detector tilt

---

## 🔬 **EXPERIMENTAL DESIGN & CAPABILITIES**

**Core Capabilities (Must-have for this cycle):**
- **Configurable Geometry:** The Detector model must support user-defined distance, pixel size, pixel count, beam center, and orientation angles (twotheta, rotx, roty, rotz)
- **Correct Geometric Transformations:** The model must correctly implement the C-code's logic for applying detector rotations and positioning the detector plane in 3D space
- **Differentiability:** All key geometric parameters (distance, beam_center_s, beam_center_f, twotheta, rotx, roty, rotz) must be fully differentiable

**Future Work (Out of scope for now):**
- Complex Detector Models: Support for multi-panel or curved detectors
- Detector Physics: Quantum efficiency, point-spread function (PSF), and sensor thickness effects. This initiative is purely geometric

---

## 🛠️ **TECHNICAL IMPLEMENTATION DETAILS**

**Key Modules to Modify:**
- `src/nanobrag_torch/config.py`: Modify. Complete the `DetectorConfig` dataclass
- `src/nanobrag_torch/models/detector.py`: Major Refactor. Implement dynamic geometry calculation, separating configuration from computation
- `tests/test_suite.py`: Modify. Add the new integration test
- `tests/test_detector_geometry.py`: Create. A new file for detector-specific unit and gradient tests

**C-Code Reference Requirement:**
- The new `_calculate_basis_vectors` method in the `Detector` class MUST include a docstring with a verbatim quote from nanoBragg.c (lines 1319-1412) detailing the detector rotation and positioning logic. This is a mandatory project convention for traceability.

**Unit System Policy:**
- The `Detector` class will operate internally using Angstroms (Å) for all length-based calculations to maintain consistency with the `Crystal` model
- The `DetectorConfig` dataclass will accept user-friendly units (e.g., millimeters for distance and pixel size). The `Detector` class's `__init__` method will be responsible for converting these values into the internal Angstrom-based system

---

## ✅ **VALIDATION & VERIFICATION PLAN**

**Golden Test Case:**
- A new golden test case, `cubic_tilted_detector`, will be generated using the C code with a non-zero twotheta angle (e.g., 15 degrees) and an offset beam center
- This test case MUST include the full suite of artifacts: `image.bin`, `trace.log` (with full-precision vector values), `params.json`, and `regenerate_golden.sh`

**Unit Tests (`tests/test_detector_geometry.py`):**
- `test_calculate_basis_vectors`: Verify that the calculated `fdet_vec`, `sdet_vec`, and `pix0_vector` match the values from the C-code trace for the `cubic_tilted_detector` case with high precision (atol=1e-9)
- **Rotation Order Tests:** Implement tests for each individual rotation (rotx, roty, rotz, twotheta) to validate against the C-code's convention and prevent ambiguity

**Integration Tests (`tests/test_suite.py`):**
- `test_cubic_tilted_detector_reproduction`: The primary success criterion. The test must achieve:
  - A Pearson correlation of ≥ 0.990 with the new golden image
  - A Mean Absolute Error (MAE) check to ensure intensity scaling is correct
- `test_simple_cubic_regression`: The existing simple_cubic test MUST continue to pass to ensure backward compatibility
- **Reproducibility:** All integration tests will set `torch.manual_seed(0)` to ensure deterministic results

**Gradient Tests (`tests/test_detector_geometry.py`):**
- **gradcheck for all geometric parameters:** `torch.autograd.gradcheck` tests must pass for all configurable orientation and position parameters:
  - distance
  - beam_center_s, beam_center_f
  - detector_rotx, detector_roty, detector_rotz
  - twotheta
- **Performance:** Gradient tests will be performed on a smaller detector patch (e.g., 128x128 pixels) to ensure CI performance remains acceptable. These tests will be marked with `@pytest.mark.slow`
- **Parameters:** Tests will use `dtype=torch.float64`, `eps=1e-6`, `atol=1e-6`, `rtol=1e-4`

---

## 📁 **File Organization**

**Initiative Path:** `plans/active/general-detector-geometry/`

**Next Step:** Run `/implementation` to generate the phased implementation plan.```

### Implementation Plan (`implementation.md`)
```markdown
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
**Last Phase Commit Hash:** a70cee5
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
- [ ] **Phase 3:** Golden Test Case Generation - 0% complete
- [ ] **Phase 4:** Integration and Backward Compatibility - 0% complete
- [ ] **Final Phase:** Validation, Gradients & Documentation - 0% complete

**Current Phase:** Phase 3: Golden Test Case Generation
**Overall Progress:** ████████░░░░░░░░ 40%

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
- **Feature Flag:** Consider adding `use_dynamic_geometry` flag to DetectorConfig for gradual rollout.```

### Phase Checklist (`phase_2_checklist.md`)
```markdown
# Phase 2: Dynamic Basis Vector Calculation Checklist

**Initiative:** General and Differentiable Detector Geometry
**Created:** 2025-08-05
**Phase Goal:** To implement the _calculate_basis_vectors method that correctly applies all detector rotations and positioning.
**Deliverable:** A working implementation that matches C-code behavior for detector orientation and positioning.

---
## 🧠 **Critical Context for This Phase**

**Key Modules & APIs Involved:**
- `src/nanobrag_torch/models/detector.py`: Implement `_calculate_basis_vectors()` method
- `src/nanobrag_torch/utils/geometry.py`: Use existing `rotate()` and `rotate_axis()` functions
- `golden_suite_generator/nanoBragg.c`: Extract detector rotation logic (lines 1319-1412)

**⚠️ Potential Gotchas & Conventions to Respect:**
- Rotation order is critical: detector_rotx/y/z are applied first, then twotheta
- The detector pivot mode (SAMPLE vs BEAM) changes when pix0_vector is calculated
- The C-code uses 1-indexed arrays; PyTorch uses 0-indexed
- Initial basis vectors depend on detector convention (MOSFLM: f=[0,0,-1], s=[1,0,0] vs XDS: f=[1,0,0], s=[0,1,0])
- The twotheta rotation is around an arbitrary axis, not a coordinate axis
---

## ✅ Task List

### Instructions:
1.  Work through tasks in order. Dependencies are noted in the guidance column.
2.  The **"How/Why & API Guidance"** column contains all necessary details for implementation.
3.  Update the `State` column as you progress: `[ ]` (Open) -> `[P]` (In Progress) -> `[D]` (Done).

---

| ID  | Task Description                                   | State | How/Why & API Guidance                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| :-- | :------------------------------------------------- | :---- | :------------------------------------------------- |
| **Section 0: Preparation & Analysis** | | | |
| 0.A | **Review Critical Context**                        | `[D]` | **Why:** To prevent common errors by understanding the specific challenges of this phase. <br> **Action:** Carefully read the "Critical Context for This Phase" section above. Acknowledge that you understand the potential gotchas before proceeding. |
| 0.B | **Extract C-Code Reference (MANDATORY FIRST STEP)** | `[D]` | **Why:** This is a MANDATORY project convention per CLAUDE.md Rule #11. ALL ported functions MUST have C-code references BEFORE implementation. <br> **File:** `golden_suite_generator/nanoBragg.c` <br> **Action:** <br>1. Open the C file and locate lines 1319-1412 containing detector rotation logic <br>2. Extract the EXACT C-code including comments <br>3. Save this verbatim quote for use in Task 1.A <br>**Critical:** DO NOT paraphrase or summarize - copy EXACTLY as written |
| 0.C | **Analyze Rotation Conventions**                   | `[D]` | **Why:** To understand the exact order and conventions used in C-code. <br> **Action:** From the extracted C-code, identify: <br>1. Initial basis vector values for each convention <br>2. The exact order of rotations (rotx→roty→rotz→twotheta) <br>3. How pivot mode affects calculations <br>4. Which vectors get rotated when |
| **Section 1: Implementation Tasks** | | | |
| 1.A | **Create Function Stub with C-Code Reference**     | `[D]` | **Why:** MANDATORY per CLAUDE.md Rule #11 - C-code reference MUST be added BEFORE implementation. <br> **File:** `src/nanobrag_torch/models/detector.py` <br> **Action:** Replace the existing `_calculate_basis_vectors` method with: <br>```python<br>def _calculate_basis_vectors(self) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:<br>    """<br>    Calculate detector basis vectors from configuration.<br>    <br>    This method dynamically computes the detector's fast, slow, and<br>    normal basis vectors based on user-provided configuration, such as<br>    detector rotations (`-detector_rot*`) and the two-theta angle.<br>    <br>    C-Code Implementation Reference (from nanoBragg.c, lines 1319-1412):<br>    ```c<br>    [PASTE THE EXACT C-CODE EXTRACTED IN TASK 0.B HERE]<br>    ```<br>    <br>    Returns:<br>        Tuple of (fdet_vec, sdet_vec, odet_vec) basis vectors<br>    """<br>    # Implementation will go here in subsequent tasks<br>    raise NotImplementedError("To be implemented after C-code reference is added")<br>``` <br>**CRITICAL:** You MUST complete this task BEFORE any implementation |
| 1.B | **Implement Initial Basis Vector Setup**           | `[D]` | **Why:** Different conventions use different initial orientations. <br> **File:** `src/nanobrag_torch/models/detector.py` <br> **Action:** In `_calculate_basis_vectors`, implement: <br>```python<br>if self.config.detector_convention == DetectorConvention.MOSFLM:<br>    fdet = torch.tensor([0.0, 0.0, -1.0], device=self.device, dtype=self.dtype)<br>    sdet = torch.tensor([1.0, 0.0, 0.0], device=self.device, dtype=self.dtype)<br>    odet = torch.tensor([0.0, 1.0, 0.0], device=self.device, dtype=self.dtype)<br>else:  # XDS<br>    fdet = torch.tensor([1.0, 0.0, 0.0], device=self.device, dtype=self.dtype)<br>    sdet = torch.tensor([0.0, 1.0, 0.0], device=self.device, dtype=self.dtype)<br>    odet = torch.tensor([0.0, 0.0, 1.0], device=self.device, dtype=self.dtype)<br>``` |
| 1.C | **Import Geometry Functions**                      | `[D]` | **Why:** To use the rotation utilities from geometry module. <br> **File:** `src/nanobrag_torch/models/detector.py` <br> **Action:** Add at top of file: <br>`from ..utils.geometry import rotate, rotate_axis` |
| 1.D | **Implement Detector Rotations**                   | `[D]` | **Why:** Apply detector_rotx/y/z rotations in correct order. <br> **File:** `src/nanobrag_torch/models/detector.py` <br> **Action:** After initial setup, add: <br>```python<br># Convert rotation angles to radians<br>rotx = degrees_to_radians(self.config.detector_rotx_deg)<br>roty = degrees_to_radians(self.config.detector_roty_deg)<br>rotz = degrees_to_radians(self.config.detector_rotz_deg)<br><br># Apply detector rotations to all basis vectors<br>fdet = rotate(fdet, rotx, roty, rotz)<br>sdet = rotate(sdet, rotx, roty, rotz)<br>odet = rotate(odet, rotx, roty, rotz)<br>``` |
| 1.E | **Implement Two-theta Rotation**                   | `[D]` | **Why:** Apply rotation around arbitrary twotheta axis. <br> **File:** `src/nanobrag_torch/models/detector.py` <br> **Action:** After detector rotations, add: <br>```python<br># Apply two-theta rotation if non-zero<br>twotheta = degrees_to_radians(self.config.detector_twotheta_deg)<br>if torch.abs(twotheta) > 1e-10:  # Check for non-zero<br>    # Normalize twotheta axis<br>    axis = self.config.twotheta_axis / torch.norm(self.config.twotheta_axis)<br>    fdet = rotate_axis(fdet, axis, twotheta)<br>    sdet = rotate_axis(sdet, axis, twotheta)<br>    odet = rotate_axis(odet, axis, twotheta)<br>``` |
| 1.F | **Return Calculated Vectors**                      | `[D]` | **Why:** Complete the method implementation. <br> **Action:** At end of method: <br>`return fdet, sdet, odet` |
| **Section 2: Testing & Validation** | | | |
| 2.A | **Create Basic Rotation Tests**                    | `[D]` | **Why:** To verify individual rotations work correctly. <br> **File:** `tests/test_detector_geometry.py` (create new) <br> **Action:** Create tests for: <br>- Default vectors for MOSFLM and XDS conventions <br>- Single axis rotations (rotx only, roty only, etc.) <br>- Combined rotations match expected results |
| 2.B | **Test Two-theta Rotation**                        | `[D]` | **Why:** Two-theta uses arbitrary axis rotation. <br> **File:** `tests/test_detector_geometry.py` <br> **Action:** Add test: <br>```python<br>def test_twotheta_rotation():<br>    config = DetectorConfig(detector_twotheta_deg=15.0)<br>    detector = Detector(config)<br>    # Verify vectors are rotated by 15 degrees around Y axis<br>``` |
| 2.C | **Test Tensor Differentiability**                  | `[D]` | **Why:** Ensure gradients flow through rotations. <br> **File:** `tests/test_detector_geometry.py` <br> **Action:** Test that basis vectors maintain gradients when config parameters are tensors with requires_grad=True |
| 2.D | **Run Updated Tests**                              | `[D]` | **Why:** To verify the implementation works. <br> **Command:** `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_detector_geometry.py -v` <br> **Also run:** `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_detector_config.py -v` to ensure no regressions |
| **Section 3: Integration & Cleanup** | | | |
| 3.A | **Update Detector Tests**                          | `[D]` | **Why:** Remove skip decorators now that _calculate_basis_vectors is implemented. <br> **File:** `tests/test_detector_config.py` <br> **Action:** Remove `@pytest.mark.skip` from: <br>- `test_custom_config_initialization` <br>- `test_custom_config_not_default` |
| 3.B | **Verify Backward Compatibility**                  | `[D]` | **Why:** Ensure simple_cubic still works. <br> **Command:** `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_suite.py::TestTier1TranslationCorrectness::test_simple_cubic_reproduction -v` <br> **Expected:** Test should still pass with >0.99 correlation |
| **Section 4: Finalization** | | | |
| 4.A | **Code Formatting & Cleanup**                      | `[D]` | **Why:** Maintain code quality. <br> **Action:** <br>1. Remove the NotImplementedError from _calculate_basis_vectors <br>2. Ensure proper indentation and formatting <br>3. Remove any debug prints |
| 4.B | **Update Method Docstring**                        | `[D]` | **Why:** Document the implementation. <br> **Action:** Update the _calculate_basis_vectors docstring to include: <br>- Parameter descriptions (even though it takes no parameters) <br>- Detailed description of the rotation order <br>- Note about device and dtype preservation |
| 4.C | **Commit Phase 2 Changes**                         | `[D]` | **Why:** Create a clean checkpoint. <br> **Command:** <br>```bash<br>git add -A<br>git commit -m "feat(detector): Implement dynamic basis vector calculation<br><br>- Add _calculate_basis_vectors with full C-code reference<br>- Support MOSFLM and XDS detector conventions<br>- Apply detector rotations (rotx/y/z) in correct order<br>- Implement two-theta rotation around arbitrary axis<br>- Add comprehensive tests for rotations<br>- Maintain differentiability for all rotation parameters<br><br>Phase 2/5 of general detector geometry implementation."<br>``` |

---

## 🎯 Success Criteria

**This phase is complete when:**
1.  All tasks in the table above are marked `[D]` (Done).
2.  The C-code reference is properly included in the method docstring BEFORE implementation.
3.  Basis vectors are calculated dynamically based on DetectorConfig.
4.  All rotation parameters (rotx/y/z, twotheta) are applied in the correct order.
5.  Tests verify correct rotation behavior for individual and combined rotations.
6.  Backward compatibility is maintained (simple_cubic test still passes).
7.  Gradients flow correctly through tensor rotation parameters.```

---
## 2. Code Changes for This Phase

**Baseline Commit:** a70cee5
**Current Branch:** feature/general-detector-geometry

```diff
diff --git a/PROJECT_STATUS.md b/PROJECT_STATUS.md
new file mode 100644
index 0000000..f804dc6
--- /dev/null
+++ b/PROJECT_STATUS.md
@@ -0,0 +1,37 @@
+# Project Status
+
+## 📍 Current Active Initiative
+
+**Name:** General Detector Geometry
+**Path:** `plans/active/general-detector-geometry/`
+**Branch:** `feature/general-detector-geometry` (baseline: feature/crystal-orientation-misset)
+**Started:** 2025-08-05
+**Current Phase:** Phase 3: Golden Test Case Generation (Phase 2 Complete ✅)
+**Progress:** ████████░░░░░░░░ 40%
+**Next Milestone:** Generate cubic_tilted_detector golden test case with nanoBragg.c
+**R&D Plan:** `plans/active/general-detector-geometry/plan.md`
+**Implementation Plan:** `plans/active/general-detector-geometry/implementation.md`
+
+## 📋 Previous Initiative
+
+**Name:** Crystal Orientation Misset
+**Path:** `plans/active/crystal-orientation-misset/`
+**Branch:** `feature/crystal-orientation-misset` (baseline: feature/general-triclinic-cell-params)
+**Started:** 2025-01-20
+**Current Phase:** Phase 2: Crystal Integration & Trace Validation ✅ (Completed)
+**Progress:** ████████░░░░░░░░ 50%
+**Next Milestone:** Simulator integration with phi and misset rotations working together
+**R&D Plan:** `plans/active/crystal-orientation-misset/plan.md`
+**Implementation Plan:** `plans/active/crystal-orientation-misset/implementation.md`
+
+## 🎯 Current Initiative Objective
+
+Replace the static detector with a fully configurable, general-purpose model that derives its geometry from user-provided parameters. This will enable simulation of realistic experimental setups with varying detector distances, positions, and orientations, making it possible to compare simulations against real-world experimental data.
+
+## 📊 Key Success Metrics
+
+- cubic_tilted_detector test achieves ≥0.990 Pearson correlation with golden image
+- All detector geometry parameters (distance, beam center, rotations, twotheta) pass gradient checks
+- No regression in existing tests (simple_cubic must continue to pass)
+- Detector basis vectors match C-code trace values with atol=1e-9
+- Complete geometric transformation pipeline: detector rotations → twotheta → positioning in 3D space
\ No newline at end of file
diff --git a/plans/active/general-detector-geometry/phase_2_checklist.md b/plans/active/general-detector-geometry/phase_2_checklist.md
new file mode 100644
index 0000000..3578c81
--- /dev/null
+++ b/plans/active/general-detector-geometry/phase_2_checklist.md
@@ -0,0 +1,70 @@
+# Phase 2: Dynamic Basis Vector Calculation Checklist
+
+**Initiative:** General and Differentiable Detector Geometry
+**Created:** 2025-08-05
+**Phase Goal:** To implement the _calculate_basis_vectors method that correctly applies all detector rotations and positioning.
+**Deliverable:** A working implementation that matches C-code behavior for detector orientation and positioning.
+
+---
+## 🧠 **Critical Context for This Phase**
+
+**Key Modules & APIs Involved:**
+- `src/nanobrag_torch/models/detector.py`: Implement `_calculate_basis_vectors()` method
+- `src/nanobrag_torch/utils/geometry.py`: Use existing `rotate()` and `rotate_axis()` functions
+- `golden_suite_generator/nanoBragg.c`: Extract detector rotation logic (lines 1319-1412)
+
+**⚠️ Potential Gotchas & Conventions to Respect:**
+- Rotation order is critical: detector_rotx/y/z are applied first, then twotheta
+- The detector pivot mode (SAMPLE vs BEAM) changes when pix0_vector is calculated
+- The C-code uses 1-indexed arrays; PyTorch uses 0-indexed
+- Initial basis vectors depend on detector convention (MOSFLM: f=[0,0,-1], s=[1,0,0] vs XDS: f=[1,0,0], s=[0,1,0])
+- The twotheta rotation is around an arbitrary axis, not a coordinate axis
+---
+
+## ✅ Task List
+
+### Instructions:
+1.  Work through tasks in order. Dependencies are noted in the guidance column.
+2.  The **"How/Why & API Guidance"** column contains all necessary details for implementation.
+3.  Update the `State` column as you progress: `[ ]` (Open) -> `[P]` (In Progress) -> `[D]` (Done).
+
+---
+
+| ID  | Task Description                                   | State | How/Why & API Guidance                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
+| :-- | :------------------------------------------------- | :---- | :------------------------------------------------- |
+| **Section 0: Preparation & Analysis** | | | |
+| 0.A | **Review Critical Context**                        | `[D]` | **Why:** To prevent common errors by understanding the specific challenges of this phase. <br> **Action:** Carefully read the "Critical Context for This Phase" section above. Acknowledge that you understand the potential gotchas before proceeding. |
+| 0.B | **Extract C-Code Reference (MANDATORY FIRST STEP)** | `[D]` | **Why:** This is a MANDATORY project convention per CLAUDE.md Rule #11. ALL ported functions MUST have C-code references BEFORE implementation. <br> **File:** `golden_suite_generator/nanoBragg.c` <br> **Action:** <br>1. Open the C file and locate lines 1319-1412 containing detector rotation logic <br>2. Extract the EXACT C-code including comments <br>3. Save this verbatim quote for use in Task 1.A <br>**Critical:** DO NOT paraphrase or summarize - copy EXACTLY as written |
+| 0.C | **Analyze Rotation Conventions**                   | `[D]` | **Why:** To understand the exact order and conventions used in C-code. <br> **Action:** From the extracted C-code, identify: <br>1. Initial basis vector values for each convention <br>2. The exact order of rotations (rotx→roty→rotz→twotheta) <br>3. How pivot mode affects calculations <br>4. Which vectors get rotated when |
+| **Section 1: Implementation Tasks** | | | |
+| 1.A | **Create Function Stub with C-Code Reference**     | `[D]` | **Why:** MANDATORY per CLAUDE.md Rule #11 - C-code reference MUST be added BEFORE implementation. <br> **File:** `src/nanobrag_torch/models/detector.py` <br> **Action:** Replace the existing `_calculate_basis_vectors` method with: <br>```python<br>def _calculate_basis_vectors(self) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:<br>    """<br>    Calculate detector basis vectors from configuration.<br>    <br>    This method dynamically computes the detector's fast, slow, and<br>    normal basis vectors based on user-provided configuration, such as<br>    detector rotations (`-detector_rot*`) and the two-theta angle.<br>    <br>    C-Code Implementation Reference (from nanoBragg.c, lines 1319-1412):<br>    ```c<br>    [PASTE THE EXACT C-CODE EXTRACTED IN TASK 0.B HERE]<br>    ```<br>    <br>    Returns:<br>        Tuple of (fdet_vec, sdet_vec, odet_vec) basis vectors<br>    """<br>    # Implementation will go here in subsequent tasks<br>    raise NotImplementedError("To be implemented after C-code reference is added")<br>``` <br>**CRITICAL:** You MUST complete this task BEFORE any implementation |
+| 1.B | **Implement Initial Basis Vector Setup**           | `[D]` | **Why:** Different conventions use different initial orientations. <br> **File:** `src/nanobrag_torch/models/detector.py` <br> **Action:** In `_calculate_basis_vectors`, implement: <br>```python<br>if self.config.detector_convention == DetectorConvention.MOSFLM:<br>    fdet = torch.tensor([0.0, 0.0, -1.0], device=self.device, dtype=self.dtype)<br>    sdet = torch.tensor([1.0, 0.0, 0.0], device=self.device, dtype=self.dtype)<br>    odet = torch.tensor([0.0, 1.0, 0.0], device=self.device, dtype=self.dtype)<br>else:  # XDS<br>    fdet = torch.tensor([1.0, 0.0, 0.0], device=self.device, dtype=self.dtype)<br>    sdet = torch.tensor([0.0, 1.0, 0.0], device=self.device, dtype=self.dtype)<br>    odet = torch.tensor([0.0, 0.0, 1.0], device=self.device, dtype=self.dtype)<br>``` |
+| 1.C | **Import Geometry Functions**                      | `[D]` | **Why:** To use the rotation utilities from geometry module. <br> **File:** `src/nanobrag_torch/models/detector.py` <br> **Action:** Add at top of file: <br>`from ..utils.geometry import rotate, rotate_axis` |
+| 1.D | **Implement Detector Rotations**                   | `[D]` | **Why:** Apply detector_rotx/y/z rotations in correct order. <br> **File:** `src/nanobrag_torch/models/detector.py` <br> **Action:** After initial setup, add: <br>```python<br># Convert rotation angles to radians<br>rotx = degrees_to_radians(self.config.detector_rotx_deg)<br>roty = degrees_to_radians(self.config.detector_roty_deg)<br>rotz = degrees_to_radians(self.config.detector_rotz_deg)<br><br># Apply detector rotations to all basis vectors<br>fdet = rotate(fdet, rotx, roty, rotz)<br>sdet = rotate(sdet, rotx, roty, rotz)<br>odet = rotate(odet, rotx, roty, rotz)<br>``` |
+| 1.E | **Implement Two-theta Rotation**                   | `[D]` | **Why:** Apply rotation around arbitrary twotheta axis. <br> **File:** `src/nanobrag_torch/models/detector.py` <br> **Action:** After detector rotations, add: <br>```python<br># Apply two-theta rotation if non-zero<br>twotheta = degrees_to_radians(self.config.detector_twotheta_deg)<br>if torch.abs(twotheta) > 1e-10:  # Check for non-zero<br>    # Normalize twotheta axis<br>    axis = self.config.twotheta_axis / torch.norm(self.config.twotheta_axis)<br>    fdet = rotate_axis(fdet, axis, twotheta)<br>    sdet = rotate_axis(sdet, axis, twotheta)<br>    odet = rotate_axis(odet, axis, twotheta)<br>``` |
+| 1.F | **Return Calculated Vectors**                      | `[D]` | **Why:** Complete the method implementation. <br> **Action:** At end of method: <br>`return fdet, sdet, odet` |
+| **Section 2: Testing & Validation** | | | |
+| 2.A | **Create Basic Rotation Tests**                    | `[D]` | **Why:** To verify individual rotations work correctly. <br> **File:** `tests/test_detector_geometry.py` (create new) <br> **Action:** Create tests for: <br>- Default vectors for MOSFLM and XDS conventions <br>- Single axis rotations (rotx only, roty only, etc.) <br>- Combined rotations match expected results |
+| 2.B | **Test Two-theta Rotation**                        | `[D]` | **Why:** Two-theta uses arbitrary axis rotation. <br> **File:** `tests/test_detector_geometry.py` <br> **Action:** Add test: <br>```python<br>def test_twotheta_rotation():<br>    config = DetectorConfig(detector_twotheta_deg=15.0)<br>    detector = Detector(config)<br>    # Verify vectors are rotated by 15 degrees around Y axis<br>``` |
+| 2.C | **Test Tensor Differentiability**                  | `[D]` | **Why:** Ensure gradients flow through rotations. <br> **File:** `tests/test_detector_geometry.py` <br> **Action:** Test that basis vectors maintain gradients when config parameters are tensors with requires_grad=True |
+| 2.D | **Run Updated Tests**                              | `[D]` | **Why:** To verify the implementation works. <br> **Command:** `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_detector_geometry.py -v` <br> **Also run:** `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_detector_config.py -v` to ensure no regressions |
+| **Section 3: Integration & Cleanup** | | | |
+| 3.A | **Update Detector Tests**                          | `[D]` | **Why:** Remove skip decorators now that _calculate_basis_vectors is implemented. <br> **File:** `tests/test_detector_config.py` <br> **Action:** Remove `@pytest.mark.skip` from: <br>- `test_custom_config_initialization` <br>- `test_custom_config_not_default` |
+| 3.B | **Verify Backward Compatibility**                  | `[D]` | **Why:** Ensure simple_cubic still works. <br> **Command:** `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_suite.py::TestTier1TranslationCorrectness::test_simple_cubic_reproduction -v` <br> **Expected:** Test should still pass with >0.99 correlation |
+| **Section 4: Finalization** | | | |
+| 4.A | **Code Formatting & Cleanup**                      | `[D]` | **Why:** Maintain code quality. <br> **Action:** <br>1. Remove the NotImplementedError from _calculate_basis_vectors <br>2. Ensure proper indentation and formatting <br>3. Remove any debug prints |
+| 4.B | **Update Method Docstring**                        | `[D]` | **Why:** Document the implementation. <br> **Action:** Update the _calculate_basis_vectors docstring to include: <br>- Parameter descriptions (even though it takes no parameters) <br>- Detailed description of the rotation order <br>- Note about device and dtype preservation |
+| 4.C | **Commit Phase 2 Changes**                         | `[ ]` | **Why:** Create a clean checkpoint. <br> **Command:** <br>```bash<br>git add -A<br>git commit -m "feat(detector): Implement dynamic basis vector calculation<br><br>- Add _calculate_basis_vectors with full C-code reference<br>- Support MOSFLM and XDS detector conventions<br>- Apply detector rotations (rotx/y/z) in correct order<br>- Implement two-theta rotation around arbitrary axis<br>- Add comprehensive tests for rotations<br>- Maintain differentiability for all rotation parameters<br><br>Phase 2/5 of general detector geometry implementation."<br>``` |
+
+---
+
+## 🎯 Success Criteria
+
+**This phase is complete when:**
+1.  All tasks in the table above are marked `[D]` (Done).
+2.  The C-code reference is properly included in the method docstring BEFORE implementation.
+3.  Basis vectors are calculated dynamically based on DetectorConfig.
+4.  All rotation parameters (rotx/y/z, twotheta) are applied in the correct order.
+5.  Tests verify correct rotation behavior for individual and combined rotations.
+6.  Backward compatibility is maintained (simple_cubic test still passes).
+7.  Gradients flow correctly through tensor rotation parameters.
\ No newline at end of file
diff --git a/src/nanobrag_torch/utils/geometry.py b/src/nanobrag_torch/utils/geometry.py
index 8c437f8..9b2ca09 100644
--- a/src/nanobrag_torch/utils/geometry.py
+++ b/src/nanobrag_torch/utils/geometry.py
@@ -186,8 +186,24 @@ def angles_to_rotation_matrix(
         torch.Tensor: 3x3 rotation matrix that applies rotations in XYZ order
     """
     # Extract device and dtype from input angles
-    device = phi_x.device
-    dtype = phi_x.dtype
+    # Ensure all angles have the same dtype - convert to the highest precision dtype
+    if hasattr(phi_x, 'dtype') and hasattr(phi_y, 'dtype') and hasattr(phi_z, 'dtype'):
+        # All are tensors
+        dtype = torch.promote_types(torch.promote_types(phi_x.dtype, phi_y.dtype), phi_z.dtype)
+        device = phi_x.device
+        phi_x = phi_x.to(dtype=dtype)
+        phi_y = phi_y.to(dtype=dtype)
+        phi_z = phi_z.to(dtype=dtype)
+    else:
+        # Mixed or scalar inputs - default to float64
+        device = torch.device('cpu')
+        dtype = torch.float64
+        if not isinstance(phi_x, torch.Tensor):
+            phi_x = torch.tensor(phi_x, dtype=dtype, device=device)
+        if not isinstance(phi_y, torch.Tensor):
+            phi_y = torch.tensor(phi_y, dtype=dtype, device=device)
+        if not isinstance(phi_z, torch.Tensor):
+            phi_z = torch.tensor(phi_z, dtype=dtype, device=device)
 
     # Calculate sin and cos for all angles
     cos_x = torch.cos(phi_x)
diff --git a/tests/test_detector_basis_vectors.py b/tests/test_detector_basis_vectors.py
new file mode 100644
index 0000000..f307919
--- /dev/null
+++ b/tests/test_detector_basis_vectors.py
@@ -0,0 +1,200 @@
+"""
+Test detector basis vector calculations.
+"""
+
+import pytest
+import torch
+import numpy as np
+import os
+
+# Set environment variable before importing torch
+os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
+
+from src.nanobrag_torch.config import DetectorConfig, DetectorConvention
+from src.nanobrag_torch.models.detector import Detector
+from src.nanobrag_torch.utils.geometry import angles_to_rotation_matrix, rotate_axis
+
+
+class TestDetectorBasisVectors:
+    """Test calculation of detector basis vectors with rotations."""
+    
+    def test_default_mosflm_convention(self):
+        """Test MOSFLM convention basis vectors without rotation."""
+        config = DetectorConfig(
+            detector_convention=DetectorConvention.MOSFLM,
+            detector_rotx_deg=0.0,
+            detector_roty_deg=0.0,
+            detector_rotz_deg=0.0,
+            detector_twotheta_deg=0.0
+        )
+        detector = Detector(config)
+        
+        # Check basis vectors match expected MOSFLM convention
+        torch.testing.assert_close(detector.fdet_vec, torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64))
+        torch.testing.assert_close(detector.sdet_vec, torch.tensor([0.0, -1.0, 0.0], dtype=torch.float64))
+        torch.testing.assert_close(detector.odet_vec, torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64))
+        
+    def test_default_xds_convention(self):
+        """Test XDS convention basis vectors without rotation."""
+        config = DetectorConfig(
+            detector_convention=DetectorConvention.XDS,
+            detector_rotx_deg=0.0,
+            detector_roty_deg=0.0,
+            detector_rotz_deg=0.0,
+            detector_twotheta_deg=0.0
+        )
+        detector = Detector(config)
+        
+        # Check basis vectors match expected XDS convention
+        torch.testing.assert_close(detector.fdet_vec, torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64))
+        torch.testing.assert_close(detector.sdet_vec, torch.tensor([0.0, 1.0, 0.0], dtype=torch.float64))
+        torch.testing.assert_close(detector.odet_vec, torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64))
+        
+    def test_single_axis_rotations(self):
+        """Test basis vectors with single-axis rotations."""
+        # Test X-axis rotation (90 degrees)
+        config = DetectorConfig(
+            detector_rotx_deg=90.0,
+            detector_roty_deg=0.0,
+            detector_rotz_deg=0.0,
+            detector_twotheta_deg=0.0
+        )
+        detector = Detector(config)
+        
+        # After 90 degree rotation around X:
+        # - fdet (0,0,1) -> (0,-1,0)
+        # - sdet (0,-1,0) -> (0,0,-1)
+        # - odet (1,0,0) stays at (1,0,0)
+        torch.testing.assert_close(detector.fdet_vec, torch.tensor([0.0, -1.0, 0.0], dtype=torch.float64), rtol=1e-7, atol=1e-7)
+        torch.testing.assert_close(detector.sdet_vec, torch.tensor([0.0, 0.0, -1.0], dtype=torch.float64), rtol=1e-7, atol=1e-7)
+        torch.testing.assert_close(detector.odet_vec, torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64), rtol=1e-7, atol=1e-7)
+        
+        # Test Y-axis rotation (90 degrees)
+        config = DetectorConfig(
+            detector_rotx_deg=0.0,
+            detector_roty_deg=90.0,
+            detector_rotz_deg=0.0,
+            detector_twotheta_deg=0.0
+        )
+        detector = Detector(config)
+        
+        # After 90 degree rotation around Y:
+        # - fdet (0,0,1) -> (1,0,0)
+        # - sdet (0,-1,0) stays at (0,-1,0)
+        # - odet (1,0,0) -> (0,0,-1)
+        torch.testing.assert_close(detector.fdet_vec, torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64), rtol=1e-7, atol=1e-7)
+        torch.testing.assert_close(detector.sdet_vec, torch.tensor([0.0, -1.0, 0.0], dtype=torch.float64), rtol=1e-7, atol=1e-7)
+        torch.testing.assert_close(detector.odet_vec, torch.tensor([0.0, 0.0, -1.0], dtype=torch.float64), rtol=1e-7, atol=1e-7)
+        
+    def test_combined_rotations(self):
+        """Test basis vectors with combined rotations."""
+        # Test combined X and Y rotations
+        config = DetectorConfig(
+            detector_rotx_deg=30.0,
+            detector_roty_deg=45.0,
+            detector_rotz_deg=0.0,
+            detector_twotheta_deg=0.0
+        )
+        detector = Detector(config)
+        
+        # Manually calculate expected result
+        rotx_rad = np.radians(30.0)
+        roty_rad = np.radians(45.0)
+        
+        # Build rotation matrices (matching C-code order: X then Y then Z)
+        Rx = np.array([
+            [1, 0, 0],
+            [0, np.cos(rotx_rad), -np.sin(rotx_rad)],
+            [0, np.sin(rotx_rad), np.cos(rotx_rad)]
+        ])
+        Ry = np.array([
+            [np.cos(roty_rad), 0, np.sin(roty_rad)],
+            [0, 1, 0],
+            [-np.sin(roty_rad), 0, np.cos(roty_rad)]
+        ])
+        R = Ry @ Rx
+        
+        # Apply to initial vectors
+        fdet_expected = R @ np.array([0, 0, 1])
+        sdet_expected = R @ np.array([0, -1, 0])
+        odet_expected = R @ np.array([1, 0, 0])
+        
+        torch.testing.assert_close(detector.fdet_vec, torch.tensor(fdet_expected, dtype=torch.float64), rtol=1e-7, atol=1e-7)
+        torch.testing.assert_close(detector.sdet_vec, torch.tensor(sdet_expected, dtype=torch.float64), rtol=1e-7, atol=1e-7)
+        torch.testing.assert_close(detector.odet_vec, torch.tensor(odet_expected, dtype=torch.float64), rtol=1e-7, atol=1e-7)
+        
+    def test_twotheta_rotation(self):
+        """Test two-theta rotation around arbitrary axis."""
+        # Test two-theta rotation around Y axis
+        config = DetectorConfig(
+            detector_rotx_deg=0.0,
+            detector_roty_deg=0.0,
+            detector_rotz_deg=0.0,
+            detector_twotheta_deg=30.0,
+            twotheta_axis=torch.tensor([0.0, 1.0, 0.0])
+        )
+        detector = Detector(config)
+        
+        # Calculate expected vectors after 30 degree rotation around Y
+        angle_rad = np.radians(30.0)
+        cos_angle = np.cos(angle_rad)
+        sin_angle = np.sin(angle_rad)
+        
+        # For rotation around Y-axis:
+        # fdet (0,0,1) -> (sin(30), 0, cos(30))
+        # sdet (0,-1,0) stays at (0,-1,0)
+        # odet (1,0,0) -> (cos(30), 0, -sin(30))
+        fdet_expected = torch.tensor([sin_angle, 0.0, cos_angle], dtype=torch.float64)
+        sdet_expected = torch.tensor([0.0, -1.0, 0.0], dtype=torch.float64)
+        odet_expected = torch.tensor([cos_angle, 0.0, -sin_angle], dtype=torch.float64)
+        
+        torch.testing.assert_close(detector.fdet_vec, fdet_expected, rtol=1e-7, atol=1e-7)
+        torch.testing.assert_close(detector.sdet_vec, sdet_expected, rtol=1e-7, atol=1e-7)
+        torch.testing.assert_close(detector.odet_vec, odet_expected, rtol=1e-7, atol=1e-7)
+        
+    def test_all_rotations_combined(self):
+        """Test all rotations applied together."""
+        config = DetectorConfig(
+            detector_rotx_deg=10.0,
+            detector_roty_deg=20.0,
+            detector_rotz_deg=30.0,
+            detector_twotheta_deg=15.0,
+            twotheta_axis=torch.tensor([0.0, 1.0, 0.0])
+        )
+        detector = Detector(config)
+        
+        # Verify that basis vectors are orthonormal
+        # Check orthogonality
+        assert abs(torch.dot(detector.fdet_vec, detector.sdet_vec).item()) < 1e-9
+        assert abs(torch.dot(detector.fdet_vec, detector.odet_vec).item()) < 1e-9
+        assert abs(torch.dot(detector.sdet_vec, detector.odet_vec).item()) < 1e-9
+        
+        # Check unit length
+        assert abs(torch.norm(detector.fdet_vec).item() - 1.0) < 1e-9
+        assert abs(torch.norm(detector.sdet_vec).item() - 1.0) < 1e-9
+        assert abs(torch.norm(detector.odet_vec).item() - 1.0) < 1e-9
+        
+    def test_tensor_rotation_parameters(self):
+        """Test that tensor parameters work correctly."""
+        # Use float64 to match detector's default dtype
+        rotx = torch.tensor(15.0, dtype=torch.float64, requires_grad=True)
+        roty = torch.tensor(25.0, dtype=torch.float64, requires_grad=True)
+        rotz = torch.tensor(35.0, dtype=torch.float64, requires_grad=True)
+        twotheta = torch.tensor(45.0, dtype=torch.float64, requires_grad=True)
+        
+        config = DetectorConfig(
+            detector_rotx_deg=rotx,
+            detector_roty_deg=roty,
+            detector_rotz_deg=rotz,
+            detector_twotheta_deg=twotheta
+        )
+        detector = Detector(config)
+        
+        # Verify tensors preserve gradients
+        assert detector.fdet_vec.requires_grad
+        assert detector.sdet_vec.requires_grad
+        assert detector.odet_vec.requires_grad
+        
+        # Verify orthonormality
+        assert abs(torch.dot(detector.fdet_vec, detector.sdet_vec).item()) < 1e-9
+        assert abs(torch.norm(detector.fdet_vec).item() - 1.0) < 1e-9
\ No newline at end of file
```
