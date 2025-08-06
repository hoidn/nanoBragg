# Review Request: Phase 3 - Golden Test Case Generation

**Initiative:** General Detector Geometry
**Generated:** 2025-08-05 21:42:51

This document contains all necessary information to review the work completed for Phase 3.

## Instructions for Reviewer

1.  Analyze the planning documents and the code changes (`git diff`) below.
2.  Create a new file named `review_phase_3.md` in this same directory (`plans/active/general-detector-geometry/`).
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
**Last Phase Commit Hash:** 9dd9d22
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

### Phase Checklist (`phase_3_checklist.md`)
```markdown
# Phase 3: Golden Test Case Generation Checklist

**Initiative:** General and Differentiable Detector Geometry
**Created:** 2025-08-06
**Phase Goal:** To generate the cubic_tilted_detector golden test case with comprehensive trace data.
**Deliverable:** Complete golden test artifacts including high-precision trace logs of detector geometry.

---
## 🧠 **Critical Context for This Phase**

**Key Modules & APIs Involved:**
- `golden_suite_generator/nanoBragg.c`: Add trace statements for detector basis vectors
- `golden_suite_generator/generate_golden.sh`: Add cubic_tilted_detector case
- `tests/golden_data/cubic_tilted_detector/`: New directory for test artifacts

**⚠️ Potential Gotchas & Conventions to Respect:**
- Trace output must use %.15g format for full double precision
- Must trace: fdet_vec, sdet_vec, odet_vec, pix0_vector after all rotations
- Test parameters: twotheta=15°, beam_center offset by 10mm in both directions
- Include detector_rotx=5°, detector_roty=3°, detector_rotz=2° for comprehensive testing
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
| 0.A | **Review Critical Context**                        | `[ ]` | **Why:** To prevent common errors by understanding the specific challenges of this phase. <br> **Action:** Carefully read the "Critical Context for This Phase" section above. Acknowledge that you understand the potential gotchas before proceeding. |
| 0.B | **Analyze Source Code**                            | `[ ]` | **Why:** To understand the existing code before modification. <br> **Action:** Open and read the files listed in the "Key Modules & APIs" section. Pay close attention to the function signatures, data flow, and any existing comments. |
| 0.C | **Check Existing Golden Test Structure**           | `[ ]` | **Why:** To understand the existing golden test pattern to replicate. <br> **Action:** Examine `tests/golden_data/simple_cubic/` directory structure and files. Note the file formats and naming conventions used (image.bin, trace.log, params.json, regenerate_golden.sh). |
| **Section 1: Implementation Tasks** | | | |
| 1.A | **Create Golden Test Directory**                   | `[ ]` | **Why:** To establish the directory structure for the new test case. <br> **File:** `tests/golden_data/cubic_tilted_detector/` <br> **API Guidance:** Create the directory using: `mkdir -p tests/golden_data/cubic_tilted_detector`. This follows the existing pattern from simple_cubic. |
| 1.B | **Add Detector Trace Statements to nanoBragg.c**   | `[ ]` | **Why:** To capture detector basis vectors for validation. <br> **File:** `golden_suite_generator/nanoBragg.c` <br> **API Guidance:** After line 1412 (after all detector rotations), add: <br>```c<br>printf("DETECTOR_FAST_AXIS %.15g %.15g %.15g\n", fdet_vector[1], fdet_vector[2], fdet_vector[3]);<br>printf("DETECTOR_SLOW_AXIS %.15g %.15g %.15g\n", sdet_vector[1], sdet_vector[2], sdet_vector[3]);<br>printf("DETECTOR_NORMAL_AXIS %.15g %.15g %.15g\n", odet_vector[1], odet_vector[2], odet_vector[3]);<br>printf("DETECTOR_PIX0_VECTOR %.15g %.15g %.15g\n", pix0_vector[1], pix0_vector[2], pix0_vector[3]);<br>``` <br>**Note:** C arrays are 1-indexed in nanoBragg.c |
| 1.C | **Create regenerate_golden.sh Script**             | `[ ]` | **Why:** To document exact parameters for reproducibility. <br> **File:** `tests/golden_data/cubic_tilted_detector/regenerate_golden.sh` <br> **API Guidance:** Create script with: <br>```bash<br>#!/bin/bash<br># Parameters: cubic cell, tilted detector with rotations<br>../../../golden_suite_generator/nanoBragg \<br>    -lambda 6.2 \<br>    -N 5 \<br>    -cell 100 100 100 90 90 90 \<br>    -hkl ../simple_cubic.hkl \<br>    -distance 100 \<br>    -detsize 102.4 \<br>    -detpixels 1024 \<br>    -Xbeam 61.2 -Ybeam 61.2 \<br>    -detector_rotx 5 -detector_roty 3 -detector_rotz 2 \<br>    -twotheta 15 \<br>    -oversample 1 \<br>    -floatfile image.bin \<br>    > trace.log 2>&1<br>``` <br>**Note:** Beam center offset by 10mm (61.2 - 51.2 = 10mm) |
| 1.D | **Create params.json File**                        | `[ ]` | **Why:** To store test parameters in machine-readable format. <br> **File:** `tests/golden_data/cubic_tilted_detector/params.json` <br> **API Guidance:** Create JSON with all parameters: <br>```json<br>{<br>  "wavelength_A": 6.2,<br>  "crystal_size_cells": 5,<br>  "unit_cell": {"a": 100, "b": 100, "c": 100, "alpha": 90, "beta": 90, "gamma": 90},<br>  "detector_distance_mm": 100,<br>  "detector_size_mm": 102.4,<br>  "detector_pixels": 1024,<br>  "beam_center_mm": {"x": 61.2, "y": 61.2},<br>  "detector_rotations_deg": {"x": 5, "y": 3, "z": 2},<br>  "twotheta_deg": 15,<br>  "oversample": 1<br>}<br>``` |
| 1.E | **Update generate_golden.sh Main Script**          | `[ ]` | **Why:** To add cubic_tilted_detector to the main generation script. <br> **File:** `golden_suite_generator/generate_golden.sh` <br> **API Guidance:** Add a new section after the simple_cubic case: <br>```bash<br>echo "Generating cubic_tilted_detector..."<br>cd ../tests/golden_data/cubic_tilted_detector<br>bash regenerate_golden.sh<br>cd ../../../golden_suite_generator<br>``` |
| 1.F | **Compile Updated nanoBragg.c**                    | `[ ]` | **Why:** To include the new trace statements. <br> **Command:** `cd golden_suite_generator && gcc -O3 -o nanoBragg nanoBragg.c -lm -fopenmp` <br> **Verify:** Check that compilation succeeds without warnings. |
| **Section 2: Testing & Validation** | | | |
| 2.A | **Generate Golden Test Data**                      | `[ ]` | **Why:** To create the reference data for the new test case. <br> **Command:** `cd tests/golden_data/cubic_tilted_detector && bash regenerate_golden.sh` <br> **Verify:** Check that image.bin and trace.log are created. |
| 2.B | **Verify Trace Output Format**                     | `[ ]` | **Why:** To ensure trace statements are working correctly. <br> **Command:** `grep "DETECTOR_" tests/golden_data/cubic_tilted_detector/trace.log` <br> **Verify:** You should see 4 lines with detector vectors, each with 3 numbers in %.15g format. |
| 2.C | **Validate Image File**                            | `[ ]` | **Why:** To ensure the golden image was generated correctly. <br> **Command:** `ls -la tests/golden_data/cubic_tilted_detector/image.bin` <br> **Verify:** File size should be 1024*1024*4 = 4,194,304 bytes (4 bytes per float). |
| 2.D | **Extract and Save Detector Vectors**              | `[ ]` | **Why:** To create a separate file for easy vector comparison. <br> **File:** `tests/golden_data/cubic_tilted_detector/detector_vectors.txt` <br> **Command:** `grep "DETECTOR_" trace.log > detector_vectors.txt` <br> **Note:** This makes it easier for PyTorch tests to load and compare vectors. |
| **Section 3: Finalization** | | | |
| 3.A | **Code Formatting & Cleanup**                      | `[ ]` | **Why:** To maintain code quality and project standards. <br> **How:** Review the added C code for consistent indentation. Ensure the trace statements follow the existing code style. |
| 3.B | **Document Trace Format**                          | `[ ]` | **Why:** To help future developers understand the trace output. <br> **File:** `tests/golden_data/README.md` <br> **Action:** Add a section documenting the new DETECTOR_* trace format and what each vector represents. |
| 3.C | **Verify All Files Present**                       | `[ ]` | **Why:** To ensure the test case is complete. <br> **Command:** `ls tests/golden_data/cubic_tilted_detector/` <br> **Expected files:** image.bin, trace.log, params.json, regenerate_golden.sh, detector_vectors.txt |

---

## 🎯 Success Criteria

**This phase is complete when:**
1.  All tasks in the table above are marked `[D]` (Done).
2.  The phase success test passes: Golden data generated with complete trace.log containing detector vectors.
3.  No regressions are introduced in the existing test suite.
4.  The cubic_tilted_detector directory contains all required artifacts: image.bin, trace.log, params.json, regenerate_golden.sh, and detector_vectors.txt
5.  The trace.log file contains high-precision (%.15g) detector basis vectors after all rotations have been applied```

---
## 2. Code Changes for This Phase

**Baseline Commit:** 9dd9d22
**Current Branch:** feature/general-detector-geometry

Note: The following shows both tracked modifications and newly created files that were staged for this review.
diff --git a/tests/golden_data/cubic_tilted_detector/detector_vectors.txt b/tests/golden_data/cubic_tilted_detector/detector_vectors.txt
new file mode 100644
index 0000000..c63cb15
--- /dev/null
+++ b/tests/golden_data/cubic_tilted_detector/detector_vectors.txt
@@ -0,0 +1,4 @@
+DETECTOR_FAST_AXIS 0.0311947630447082 -0.096650175316428 0.994829447880333
+DETECTOR_SLOW_AXIS -0.228539518954453 -0.969636205471835 -0.0870362988312832
+DETECTOR_NORMAL_AXIS 0.973034724475264 -0.224642766741965 -0.0523359562429438
+DETECTOR_PIX0_VECTOR 0.112087366299472 0.0653100408232811 -0.0556023303792543
diff --git a/tests/golden_data/cubic_tilted_detector/params.json b/tests/golden_data/cubic_tilted_detector/params.json
new file mode 100644
index 0000000..62ffdab
--- /dev/null
+++ b/tests/golden_data/cubic_tilted_detector/params.json
@@ -0,0 +1,26 @@
+{
+  "wavelength_A": 6.2,
+  "crystal_size_cells": 5,
+  "unit_cell": {
+    "a": 100,
+    "b": 100,
+    "c": 100,
+    "alpha": 90,
+    "beta": 90,
+    "gamma": 90
+  },
+  "detector_distance_mm": 100,
+  "detector_size_mm": 102.4,
+  "detector_pixels": 1024,
+  "beam_center_mm": {
+    "x": 61.2,
+    "y": 61.2
+  },
+  "detector_rotations_deg": {
+    "x": 5,
+    "y": 3,
+    "z": 2
+  },
+  "twotheta_deg": 15,
+  "oversample": 1
+}
\ No newline at end of file
diff --git a/tests/golden_data/cubic_tilted_detector/regenerate_golden.sh b/tests/golden_data/cubic_tilted_detector/regenerate_golden.sh
new file mode 100755
index 0000000..cdd3a22
--- /dev/null
+++ b/tests/golden_data/cubic_tilted_detector/regenerate_golden.sh
@@ -0,0 +1,22 @@
+#!/bin/bash
+# Parameters: cubic cell, tilted detector with rotations
+# This script regenerates the golden test data for the cubic_tilted_detector test case
+
+# Navigate to the test directory
+cd "$(dirname "$0")"
+
+# Run nanoBragg with tilted detector parameters
+../../../golden_suite_generator/nanoBragg \
+    -lambda 6.2 \
+    -N 5 \
+    -cell 100 100 100 90 90 90 \
+    -default_F 100 \
+    -distance 100 \
+    -detsize 102.4 \
+    -detpixels 1024 \
+    -Xbeam 61.2 -Ybeam 61.2 \
+    -detector_rotx 5 -detector_roty 3 -detector_rotz 2 \
+    -twotheta 15 \
+    -oversample 1 \
+    -floatfile image.bin \
+    > trace.log 2>&1
\ No newline at end of file
```


### Additional Code Changes:

```diff
diff --git a/golden_suite_generator/nanoBragg.c b/golden_suite_generator/nanoBragg.c
index 6edc0f3..4420680 100644
--- a/golden_suite_generator/nanoBragg.c
+++ b/golden_suite_generator/nanoBragg.c
@@ -1730,6 +1730,11 @@ int main(int argc, char** argv)
     rotate_axis(fdet_vector,fdet_vector,twotheta_axis,detector_twotheta);
     rotate_axis(sdet_vector,sdet_vector,twotheta_axis,detector_twotheta);
     rotate_axis(odet_vector,odet_vector,twotheta_axis,detector_twotheta);
+    
+    /* Trace detector basis vectors after all rotations */
+    printf("DETECTOR_FAST_AXIS %.15g %.15g %.15g\n", fdet_vector[1], fdet_vector[2], fdet_vector[3]);
+    printf("DETECTOR_SLOW_AXIS %.15g %.15g %.15g\n", sdet_vector[1], sdet_vector[2], sdet_vector[3]);
+    printf("DETECTOR_NORMAL_AXIS %.15g %.15g %.15g\n", odet_vector[1], odet_vector[2], odet_vector[3]);
 
     /* make sure beam center is preserved */
     if(detector_pivot == BEAM){
@@ -1743,6 +1748,9 @@ int main(int argc, char** argv)
     Fclose         = -dot_product(pix0_vector,fdet_vector);
     Sclose         = -dot_product(pix0_vector,sdet_vector);
     close_distance =  dot_product(pix0_vector,odet_vector);
+    
+    /* Trace pix0_vector after all transformations */
+    printf("DETECTOR_PIX0_VECTOR %.15g %.15g %.15g\n", pix0_vector[1], pix0_vector[2], pix0_vector[3]);
 
     /* where is the direct beam now? */
     /* difference between beam impact vector and detector origin */
diff --git a/tests/golden_data/README.md b/tests/golden_data/README.md
index 4f2279d..8c79d21 100644
--- a/tests/golden_data/README.md
+++ b/tests/golden_data/README.md
@@ -89,4 +89,57 @@ This test validates the implementation of general triclinic unit cells. It uses
 - Detector: 512x512 pixels, 100mm distance, 0.1mm pixel size (defaults)
 - Structure factors: all reflections set to F=100
 
-Note: The misset angles were generated randomly and saved for reproducibility. To regenerate this data, use the script at `tests/golden_data/triclinic_P1/regenerate_golden.sh`.
\ No newline at end of file
+Note: The misset angles were generated randomly and saved for reproducibility. To regenerate this data, use the script at `tests/golden_data/triclinic_P1/regenerate_golden.sh`.
+
+---
+
+### 4. `cubic_tilted_detector` Test Case
+
+This test validates the implementation of general detector geometry with rotations and tilts. It uses a cubic cell with a detector that has been rotated and positioned at a twotheta angle.
+
+**Generated Files:**
+- `cubic_tilted_detector/image.bin`
+- `cubic_tilted_detector/trace.log`
+- `cubic_tilted_detector/params.json`
+- `cubic_tilted_detector/detector_vectors.txt`
+
+**Command:**
+```bash
+./nanoBragg -lambda 6.2 \
+  -N 5 \
+  -cell 100 100 100 90 90 90 \
+  -default_F 100 \
+  -distance 100 \
+  -detsize 102.4 \
+  -detpixels 1024 \
+  -Xbeam 61.2 -Ybeam 61.2 \
+  -detector_rotx 5 -detector_roty 3 -detector_rotz 2 \
+  -twotheta 15 \
+  -oversample 1 \
+  -floatfile tests/golden_data/cubic_tilted_detector/image.bin
+```
+
+**Parameters:**
+- Unit cell: 100Å cubic cell
+- Crystal size: 5x5x5 unit cells
+- Wavelength: 6.2 Å
+- Detector: 1024x1024 pixels, 100mm distance, 0.1mm pixel size
+- Beam center: (61.2, 61.2) mm - offset by 10mm from detector center
+- Detector rotations: rotx=5°, roty=3°, rotz=2° applied in that order
+- Two-theta angle: 15° - detector swing around the sample
+- Structure factors: all reflections set to F=100
+
+To regenerate this data, use the script at `tests/golden_data/cubic_tilted_detector/regenerate_golden.sh`.
+
+---
+
+## Detector Trace Format
+
+When nanoBragg.c is compiled with detector tracing enabled, it outputs the following vectors after all rotations have been applied:
+
+- **DETECTOR_FAST_AXIS**: The unit vector pointing in the fast (x) direction of the detector
+- **DETECTOR_SLOW_AXIS**: The unit vector pointing in the slow (y) direction of the detector  
+- **DETECTOR_NORMAL_AXIS**: The unit vector normal to the detector plane (pointing from detector to sample)
+- **DETECTOR_PIX0_VECTOR**: The 3D position of the first pixel (0,0) in the detector
+
+All vectors are output in high precision (%.15g format) to enable accurate validation of the PyTorch implementation.
\ No newline at end of file
```
