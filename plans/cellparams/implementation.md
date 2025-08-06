<!-- ACTIVE IMPLEMENTATION PLAN -->
<!-- DO NOT MISTAKE THIS FOR A TEMPLATE. THIS IS THE OFFICIAL SOURCE OF TRUTH FOR THE PROJECT'S PHASED PLAN. -->

# Phased Implementation Plan

**Project:** General and Differentiable Unit Cell Geometry (v4)

**Core Technologies:** PyTorch, Python, torch.autograd

---

## 📄 **DOCUMENT HIERARCHY**

This document orchestrates the implementation of the objective defined in the main R&D plan. The full set of documents for this initiative is:

*   **`plans/geometry/plan_geometry.md`** (The high-level R&D Plan)
    *   **`implementation_geometry.md`** (This file - The Phased Implementation Plan)
        *   `phase_1_checklist.md` (Detailed checklist for Phase 1)
        *   `phase_2_checklist.md` (Detailed checklist for Phase 2)
        *   `phase_3_checklist.md` (Detailed checklist for Phase 3)
        *   `phase_4_checklist.md` (Detailed checklist for Phase 4)

---

## 🎯 **PHASE-BASED IMPLEMENTATION**

**Overall Goal:** To replace the hard-coded simple cubic lattice with a fully general, differentiable triclinic lattice calculation, enabling the simulation and refinement of any crystal system.

---

## 📋 **IMPLEMENTATION PHASES**

### **Phase 1: Prerequisite Setup & Golden Data Generation**

**Goal:** To prepare the configuration, testing infrastructure, and ground-truth data required for the core implementation.

**Deliverable:** An updated `CrystalConfig`, a new reproducible `triclinic_P1` golden test case, and an updated test file structure.

**Implementation Checklist:**
*   The detailed, step-by-step implementation for this phase is tracked in: `[ ] phase_1_checklist.md`

**Key Tasks Summary:**
*   Expand `CrystalConfig` to include all six cell parameters and a `mosaic_seed`.
*   Generate a new `triclinic_P1` golden test case in `tests/golden_data/triclinic_P1/`, including:
    *   `params.json`: Exact C-code input parameters, compiler version, and commit hash.
    *   `image.bin`: The raw binary output image.
    *   `trace.log`: The detailed single-pixel trace.
    *   `regenerate_golden.sh`: A script to reproduce these artifacts.
*   Create a new test file `tests/test_crystal_geometry.py`.
*   Update `CLAUDE.md` with a formal "Crystallographic Conventions" section, detailing the `|G|=1/d` convention and its relation to `|Q|=2π/d`.

**Success Test (Acceptance Gate):** The `triclinic_P1` artifacts are produced, and the trace log contains numeric values for `a,b,c,a*,b*,c*,V` with ≥15 significant digits. `CLAUDE.md` is updated.

**Duration:** 1 day

---

### **Phase 2: Core Geometry Engine & Unit Testing**

**Goal:** To implement the core differentiable logic for calculating lattice vectors and validate it with a comprehensive suite of unit tests.

**Deliverable:** A refactored `Crystal` class with a fully implemented `compute_cell_tensors` method that passes all new geometry-specific unit tests.

**Implementation Checklist:**
*   The detailed, step-by-step implementation for this phase is tracked in: `[ ] phase_2_checklist.md`

**Key Tasks Summary:**
*   Refactor `Crystal` class to remove hard-coded vectors.
*   Implement the `compute_cell_tensors` method using the explicit, numerically stable formulas from the R&D plan.
*   Implement the application of an orientation matrix `R` to the calculated base real and reciprocal vectors.
*   Write and pass all new unit tests in `tests/test_crystal_geometry.py`.

**Success Test (Acceptance Gate):** All unit tests pass with specified tolerances:
*   Metric duality: `a*·a = 1`, `a*·b = 0`, etc., with absolute error ≤ `1e-12`.
*   Volume identity: Relative error between two volume calculation methods ≤ `1e-12`.
*   Resolution shell consistency: Max absolute error in `|G| - 1/d` ≤ `5e-13`.
*   Rotation invariance: `|G|` remains unchanged by an arbitrary rotation `R` (tolerance ≤ `1e-12`).

**Duration:** 2 days

---

### **Phase 3: Simulator Integration & End-to-End Validation**

**Goal:** To integrate the new dynamic `Crystal` model into the `Simulator` and validate the correctness of the full, end-to-end simulation.

**Deliverable:** An updated `Simulator` that correctly uses the general triclinic geometry, passing all integration and regression tests.

**Implementation Checklist:**
*   The detailed, step-by-step implementation for this phase is tracked in: `[ ] phase_3_checklist.md`

**Key Tasks Summary:**
*   Update the `Simulator` to call `crystal.compute_cell_tensors` at the start of each `run`.
*   Update HKL range derivation logic to enumerate HKLs satisfying `‖h a* + k b* + l c*‖ ≤ 1/d_min`.
*   Implement the new `triclinic_P1` integration test.
*   Run and ensure the `simple_cubic` regression test still passes.
*   Implement the sensitivity sign test.
*   Establish and run a performance benchmark gate, documenting any regression.

**Success Test (Acceptance Gate):**
*   Image agreement for `triclinic_P1`: Pearson correlation ≥ 0.990 and SSIM ≥ 0.98.
*   Peak localization check: Max position error for the top 50 peaks is ≤ 0.5 pixels.
*   Performance benchmark for `simple_cubic` case shows ≤ 10% regression.

**Duration:** 1-2 days

---

### **Phase 4: Differentiability Verification & Finalization**

**Goal:** To rigorously verify that all six unit cell parameters are fully differentiable and to finalize all related documentation.

**Deliverable:** A complete set of passing `gradcheck` and property-based tests, and updated project documentation.

**Implementation Checklist:**
*   The detailed, step-by-step implementation for this phase is tracked in: `[ ] phase_4_checklist.md`

**Key Tasks Summary:**
*   Implement individual and joint `gradcheck` tests for all six cell parameters.
*   Implement `gradgradcheck` on the 6-vector to ensure second-order stability.
*   Implement property-based tests using a randomized cell sampler (`Hypothesis` or similar).
*   Implement a simple optimization test to verify recovery of a known cell from "raw" parameters.
*   Update all relevant docstrings and the main `README.md`.

**Success Test (Acceptance Gate):**
*   `gradcheck` passes for all parameters and the joint 6-vector with `eps=1e-6`, `atol=1e-6`, `rtol=1e-4`, `check_undefined_grad=True`.
*   `gradgradcheck` passes for the 6-vector.
*   Randomized property-based tests (N=25) pass consistently.

**Duration:** 1 day

---

## 📝 **PHASE TRACKING**

- [ ] **Phase 1:** Prerequisite Setup & Golden Data Generation
- [ ] **Phase 2:** Core Geometry Engine & Unit Testing
- [ ] **Phase 3:** Simulator Integration & End-to-End Validation
- [ ] **Phase 4:** Differentiability Verification & Finalization

**Current Phase:** Phase 1: Prerequisite Setup & Golden Data Generation
**Next Milestone:** A reproducible `triclinic_P1` golden test case and an updated `CrystalConfig`.
