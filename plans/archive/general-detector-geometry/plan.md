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

**Next Step:** Run `/implementation` to generate the phased implementation plan.