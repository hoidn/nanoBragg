### **Research & Development Plan: General and Differentiable Unit Cell Geometry (v3)**

## 🎯 **OBJECTIVE & HYPOTHESIS**

**Project/Initiative Name:** General and Differentiable Unit Cell Geometry

**Problem Statement:** The current PyTorch implementation is fundamentally limited by a hard-coded simple cubic unit cell. This prevents the simulation of the vast majority of crystal systems and makes it impossible to perform unit cell refinement, a core task in crystallography. The existing differentiable rotation features, while powerful, can only be applied to this single, non-representative crystal type.

**Proposed Solution / Hypothesis:** We will replace the hard-coded lattice with a fully general, triclinic lattice calculation derived from the six standard unit cell parameters (`a, b, c, α, β, γ`). We hypothesize that by implementing this transformation using exclusively differentiable PyTorch operations, we will enable the refinement of any crystal's unit cell against experimental data, transforming the simulator from a proof-of-concept into a scientifically versatile tool.

**Scope & Deliverables:**
*   An updated `CrystalConfig` dataclass that accepts all six unit cell parameters and a seed for reproducibility.
*   A modified `Crystal` class with a `compute_cell_tensors` method that dynamically calculates lattice vectors.
*   The `Simulator` class updated to use these dynamically generated vectors.
*   A comprehensive new set of tests, including unit tests for geometry, `gradcheck` tests for all cell parameters, and a new `triclinic_P1` golden test case.
*   Updated documentation, including a formal convention statement in `CLAUDE.md`.

---

## 🔬 **EXPERIMENTAL DESIGN & CAPABILITIES**

**Core Capabilities (Must-have for this cycle):**
1.  **General Triclinic Cell Support:** The `Crystal` class must correctly initialize from the six standard unit cell parameters.
2.  **Differentiable Reciprocal Vector Calculation:** The transformation from the six real-space cell parameters to the reciprocal-space vectors (`a*`, `b*`, `c*`) must be a fully differentiable function.
3.  **Full Simulator Integration:** The main simulation must seamlessly use these dynamically calculated vectors.

**Future Work (Out of scope for now):**
*   Symmetry-constrained refinement and space group operators.

---

## 🛠️ **TECHNICAL IMPLEMENTATION DETAILS**

**Key Modules to Modify:**
*   `src/nanobrag_torch/config.py`: **Modify.** Expand `CrystalConfig` to include all six cell parameters and a `mosaic_seed`.
*   `src/nanobrag_torch/models/crystal.py`: **Major Refactor.** Implement a new `compute_cell_tensors` method containing the core differentiable geometry logic.
*   `src/nanobrag_torch/simulator.py`: **Review & Verify.** Update HKL range derivation and interpolation bounds for general triclinic geometry.
*   `tests/test_suite.py`: **Modify.** Add new test class `TestCrystalGeometry` and new integration tests.

**C-Code Reference Requirement:**
All newly created or stubbed-out functions with a direct equivalent in `nanoBragg.c` **MUST** include a concise, verbatim quote (with line numbers) of the relevant C-code implementation in their docstring. This provides a clear "ground truth" reference.

**Crystallographic Conventions:**
*   **Reciprocal Space:** The convention `|G| = 1/d` where `G = h*a* + k*b* + l*c*` will be used, consistent with `nanoBragg.c`. This will be explicitly tested.
*   **Units:** Configuration will accept angles in degrees, which will be converted to radians for computation. All internal length calculations will be in Angstroms.

**Differentiable Formulas to Implement:**
The `compute_cell_tensors` method will implement the following, using `torch.float64` and a small `eps=1e-24` for numerical stability. Let `ca=cos(α)`, `cb=cos(β)`, `cg=cos(γ)`, `sg=sin(γ)`.

1.  **Real-Space Basis (Canonical Frame):**
    *   `a = (a, 0, 0)`
    *   `b = (b*cg, b*sg, 0)`
    *   `cx = c*cb`
    *   `cy = c*(ca - cb*cg) / sg`
    *   `cz = c * sqrt(clamp_min(1 - cb² - cy²/c², eps))`
    *   `c = (cx, cy, cz)`
2.  **Volume:**
    *   `V = dot(a, cross(b, c))`
3.  **Reciprocal Vectors:**
    *   `a* = cross(b, c) / V`
    *   `b* = cross(c, a) / V`
    *   `c* = cross(a, b) / V`

**Robust Parameterization for Optimization:**
The implementation will support reparameterization for stable refinement:
*   **Lengths:** `a = softplus(a_raw) + a_min`
*   **Angles:** `gamma = gamma_lo + sigmoid(gamma_raw) * (gamma_hi - gamma_lo)`

---

## ✅ **VALIDATION & VERIFICATION PLAN**

**Prerequisite:**
*   [ ] Generate a new `triclinic_P1` golden test case from the C code, including a `.bin` image and a single-pixel trace log with printed `a,b,c,a*,b*,c*,V` values.

**Unit Tests (`TestCrystalGeometry`):**
*   [ ] **Cubic Regression Test:** Verify that cubic parameters produce the previously hard-coded reciprocal vectors.
*   [ ] **Triclinic Correctness Test:** Verify that triclinic parameters produce reciprocal vectors matching the new golden trace.
*   [ ] **Metric Duality Test:** Assert `a*·a = 1`, `a*·b = 0`, etc., for a general triclinic cell (tolerance `1e-12`).
*   [ ] **Volume Identity Test:** Assert `V = a·(b x c)` matches the closed-form `sqrt` formula.
*   [ ] **Resolution Shell Consistency Test:** Verify that HKLs within a d-min cutoff satisfy `|h*a* + k*b* + l*c*| = 1/d`.

**Integration / Regression Tests:**
*   [ ] **`simple_cubic` Regression Test:** The existing `test_simple_cubic_reproduction` must continue to pass.
*   [ ] **New `triclinic_P1` Integration Test:** Reproduce the `triclinic_P1.bin` golden image with high correlation (>0.99).
*   [ ] **Sensitivity Sign Test:** Verify that small perturbations in cell angles shift Bragg spots in the expected direction.

**Gradient Tests:**
*   [ ] **`gradcheck` for all six cell parameters:**
    *   **Individual Tests:** Run `gradcheck` for each of the six parameters separately.
    *   **Joint Test:** Run a single `gradcheck` on the concatenated 6-vector of parameters to catch cross-couplings.
    *   **Parameters:** `dtype=torch.float64`, `eps=1e-6`, `atol=1e-6`, `rtol=1e-4`.
    *   **Geometries:** Test with random, well-conditioned cells and near-orthogonal/highly oblique edge cases.

**Success Criteria (How we know we're done):**
*   All new unit, integration, and gradient tests pass.
*   The `simple_cubic` regression test continues to pass.
*   The `Crystal` class no longer contains any hard-coded lattice vectors.
*   The simulator can successfully generate a diffraction pattern for a general triclinic cell that matches the C-code reference.

---

## 🚩 **RISKS TO TRACK**

*   **Numerical Instability:** Near-degenerate cells can lead to unstable gradients.
    *   **Mitigation:** Use robust parameterization and `torch.clamp_min` on denominators and `sqrt` arguments.
*   **Gradient Masking:** Hard clamping can zero out gradients.
    *   **Mitigation:** Monitor gradient magnitudes during testing. Consider smooth penalty functions if issues arise.
*   **Convention Mismatch:** A mismatch with C-code conventions could cause subtle bugs.
    *   **Mitigation:** Explicitly document and test the `|G| = 1/d` convention.
