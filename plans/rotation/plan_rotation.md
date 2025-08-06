Excellent. Following the `customplan.md` template, here is a detailed R&D plan for adding dynamic crystal rotation to the PyTorch implementation. This document is designed to be passed directly to the AI agent to kick off the `/implementation` command.

---

### **Research & Development Plan: Dynamic Crystal Rotation**

## 🎯 **OBJECTIVE & HYPOTHESIS**

**Project/Initiative Name:** Dynamic Crystal Rotation and Mosaicity

**Problem Statement:** The current PyTorch implementation only supports a static, axis-aligned crystal orientation, which prevents the simulation of realistic experimental conditions like sample rotation (phi scans) and crystal imperfections (mosaicity).

**Proposed Solution / Hypothesis:** By implementing a fully vectorized and differentiable rotation pipeline, we will enable the simulation of phi scans and mosaic spread. We hypothesize that this will allow the model to reproduce a wider range of golden test cases and unlock the ability to refine crystal orientation parameters against experimental data.

**Scope & Deliverables:**
*   A modified `Crystal` class that can apply phi and mosaic rotations.
*   An updated `Simulator` class that integrates these rotations into the main calculation.
*   New configuration options in `CrystalConfig` to control these rotations.
*   New tests in the test suite to validate the rotation logic and its gradients.
*   An updated demo script showcasing the new rotation capabilities.

---

## 🔬 **EXPERIMENTAL DESIGN & CAPABILITIES**

**Core Capabilities (Must-have for this cycle):**
1.  **Spindle Rotation (Phi):** Implement the ability to simulate a crystal rotated around a specified spindle axis by a given `phi` angle. This includes handling a range of angles for oscillation photography.
2.  **Mosaicity:** Implement the ability to simulate a distribution of crystal orientations (mosaic domains) around the central orientation, controlled by a `mosaic_spread` parameter.
3.  **Differentiability:** Ensure that all rotation parameters (`phi`, `mosaic_spread`, etc.) are differentiable, allowing for their refinement via gradient descent.

**Future Work (Out of scope for now):**
*   Anisotropic mosaicity (different spread values along different crystal axes).
*   Implementing `-misset` as a separate, initial static rotation. For this cycle, we will focus on the dynamic `phi` and `mosaic` rotations within the main simulation loop.

---

## 🛠️ **TECHNICAL IMPLEMENTATION DETAILS**

**Key Modules to Modify:**
*   `src/nanobrag_torch/config.py`: **Modify.** Add rotation parameters to `CrystalConfig`.
*   `src/nanobrag_torch/models/crystal.py`: **Modify.** Implement the core rotation logic in a new `get_rotated_real_vectors` method.
*   `src/nanobrag_torch/simulator.py`: **Modify.** Update the `run` method to use the rotated vectors and integrate over the new orientation dimensions.
*   `tests/test_suite.py`: **Modify.** Add new tests for rotation correctness and gradients.

**Key Dependencies / APIs:**
*   **Internal:**
    *   `utils.geometry.rotate_axis`: For applying spindle (phi) rotations.
    *   `utils.geometry.rotate_umat`: For applying mosaic domain rotations.
    *   `utils.geometry.dot_product`: For calculating Miller indices with the newly rotated vectors.
*   **External:**
    *   `torch`: For tensor creation, broadcasting, and `torch.autograd.gradcheck`.

**Data Requirements:**
*   **Input Data:** A new golden test case from the C code that includes mosaicity (e.g., `simple_cubic_mosaic`). This will be used for validation.
*   **Expected Output Format:** A 2D PyTorch tensor representing the diffraction image, correctly summed over all phi and mosaic steps.

---

## ✅ **VALIDATION & VERIFICATION PLAN**

**Unit Tests:**
*   [ ] **Test `get_rotated_real_vectors`:**
    *   Test with `phi=0` and `mosaic_spread=0`; should return the original, un-rotated vectors.
    *   Test with a 90-degree phi rotation around the Z-axis; `a=[1,0,0]` should become `[0,1,0]`.
    *   Test with a single, known mosaic rotation matrix; verify the output vector is correct.

**Integration / Regression Tests:**
*   [ ] **Test `Simulator.run` with rotation:**
    *   Run a simulation with a 90-degree phi rotation and verify that the entire diffraction pattern rotates as expected on the detector.
*   [ ] **Reproduce `simple_cubic_mosaic` golden case:**
    *   Create a new test that runs the simulator with mosaicity enabled and compares the output to a new golden image generated from the C code with the `-mosaic` flag.

**Gradient Tests:**
*   [ ] **Test `phi` gradient:** Use `torch.autograd.gradcheck` to verify the gradient of the loss with respect to the `phi` angle.
*   [ ] **Test `mosaic_spread` gradient:** Verify the gradient with respect to the `mosaic_spread_deg` parameter.

**Success Criteria (How we know we're done):**
*   The new `simple_cubic_mosaic` integration test passes, showing high correlation (>0.99) with the C-code's output.
*   All new unit and gradient tests pass.
*   The demo script can successfully generate an image with visible spot broadening when mosaicity is enabled.
*   The `get_rotated_real_vectors` method in `crystal.py` is fully implemented and no longer raises `NotImplementedError`.
