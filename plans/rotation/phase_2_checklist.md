### **Agent Implementation Checklist: Phase 2 - Simulator Integration**

**Overall Goal for this Phase:** To integrate the rotation capabilities into the main simulation pipeline, enabling multi-orientation diffraction calculations.

**Instructions for Agent:**
1.  Copy this checklist into your working memory.
2.  Update the `State` for each item as you progress: `[ ]` (Open) -> `[P]` (In Progress) -> `[D]` (Done).
3.  Follow the `How/Why & API Guidance` column carefully for implementation details.

---

| ID | Task Description | State | How/Why & API Guidance |
| :--- | :--- | :--- | :--- |
| **Section 0: Preparation & Context Priming** |
| 0.A | **Review Key Documents & APIs** | `[D]` | **Why:** To load the necessary context from the previous phase and the overall plan. <br> **Docs:** `plans/rotation/implementation_rotation.md`, `src/nanobrag_torch/models/crystal.py` (review the new `get_rotated_real_vectors` method). <br> **APIs:** `torch.sum`, `torch.unsqueeze`, `torch.view`. |
| 0.B | **Identify Target Files for Modification** | `[D]` | **Why:** To have a clear list of files that will be touched during this phase. <br> **Files:** `src/nanobrag_torch/simulator.py` (Modify), `tests/test_suite.py` (Modify). |
| **Section 1: Simulator Integration** |
| 1.A | **Update Simulator.__init__** | `[D]` | **Why:** To accept and store the new `CrystalConfig` object, which contains the rotation parameters. <br> **How:** Modify the `Simulator`'s `__init__` method to accept a `crystal_config: CrystalConfig` argument and store it as `self.crystal_config`. <br> **File:** `src/nanobrag_torch/simulator.py`. |
| 1.B | **Call get_rotated_real_vectors** | `[D]` | **Why:** To obtain the dynamically rotated lattice vectors for the simulation. <br> **How:** In `Simulator.run()`, call `self.crystal.get_rotated_real_vectors(self.crystal_config)` to get the `rot_a`, `rot_b`, and `rot_c` tensors. These will have a shape like `(N_phi, N_mos, 3)`. <br> **File:** `src/nanobrag_torch/simulator.py`. |
| 1.C | **Broadcast Tensors for Rotation** | `[D]` | **Why:** To prepare all tensors for vectorized calculation across pixel, phi, and mosaic dimensions. <br> **How:** Use `unsqueeze` or `view` to expand the dimensions of the `scattering_vector` so it can broadcast with the rotated lattice vectors. <br> **Example:** `scattering_vector` (shape `S, F, 3`) should be reshaped to `(S, F, 1, 1, 3)` to be compatible with `rot_a` (shape `1, 1, N_phi, N_mos, 3`). <br> **File:** `src/nanobrag_torch/simulator.py`. |
| 1.D | **Update Miller Index Calculation** | `[D]` | **Why:** To use the newly rotated vectors in the physics calculation. <br> **How:** Replace the use of `self.crystal.a` with `rot_a` (and similarly for `b` and `c`) in the `dot_product` calls. The resulting `h`, `k`, `l` tensors will now have dimensions for phi and mosaic, e.g., `(S, F, N_phi, N_mos)`. <br> **File:** `src/nanobrag_torch/simulator.py`. |
| 1.E | **Integrate over Orientations** | `[D]` | **Why:** To combine the contributions from all phi steps and mosaic domains into a single final image, correctly modeling the physical integration process. <br> **How:** After calculating the intensity contributions (which will be a 4D tensor), use `torch.sum` to sum over the phi and mosaic dimensions. The final result should be a 2D tensor of shape `(S, F)`. <br> **File:** `src/nanobrag_torch/simulator.py`. |
| **Section 2: Integration Testing** |
| 2.A | **Update Existing Tests** | `[D]` | **Why:** The `Simulator`'s `__init__` signature has changed, which will break existing tests. <br> **How:** In `tests/test_suite.py`, find all instantiations of `Simulator` and pass in a default `CrystalConfig()` object. <br> **File:** `tests/test_suite.py`. |
| 2.B | **Create a Basic Rotation Test** | `[D]` | **Why:** To verify that the integrated rotation logic produces a physically plausible result. <br> **How:** Create a new test `test_simulator_phi_rotation` in `TestTier1TranslationCorrectness`. <br> 1. Run the simulator with `phi_start_deg=0`. Store the argmax (position of the brightest pixel). <br> 2. Create a new `CrystalConfig` with `phi_start_deg=90`. <br> 3. Run the simulator again. <br> 4. Assert that the new argmax position is different from the original one, proving the pattern has moved. <br> **File:** `tests/test_suite.py`. |
| **Section 3: Finalization** |
| 3.A | **Code Formatting & Linting** | `[D]` | **Why:** To maintain code quality. <br> **How:** Run `black .` and `ruff . --fix` on all modified files. |
| 3.B | **Update Docstrings** | `[D]` | **Why:** To document the new functionality and signature changes. <br> **How:** Update the docstrings for `Simulator.__init__` and `Simulator.run` to reflect the new `crystal_config` parameter and the handling of rotation dimensions. |