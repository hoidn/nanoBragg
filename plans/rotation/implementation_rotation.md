<!-- ACTIVE IMPLEMENTATION PLAN -->
<!-- DO NOT MISTAKE THIS FOR A TEMPLATE. THIS IS THE OFFICIAL SOURCE OF TRUTH FOR THE PROJECT'S PHASED PLAN. -->

# Phased Implementation Plan

**Project:** Dynamic Crystal Rotation and Mosaicity

**Core Technologies:** PyTorch, Python, C interop, torch.autograd

---

## 📄 **DOCUMENT HIERARCHY**

This document orchestrates the implementation of the objective defined in the main R&D plan. The full set of documents for this initiative is:

*   **`plans/rotation/plan_rotation.md`** (The high-level R&D Plan)
    *   **`implementation_rotation.md`** (This file - The Phased Implementation Plan)
        *   `phase_1_checklist.md` (Detailed checklist for Phase 1)
        *   `phase_2_checklist.md` (Detailed checklist for Phase 2)
        *   `phase_3_checklist.md` (Detailed checklist for Phase 3)

---

## 🎯 **PHASE-BASED IMPLEMENTATION**

**Overall Goal:** To implement fully vectorized and differentiable crystal rotation capabilities (phi scans and mosaicity) in the PyTorch nanoBragg implementation, enabling realistic experimental simulation and parameter refinement.

---

## 📋 **IMPLEMENTATION PHASES**

### **Phase 1: Core Rotation Infrastructure**

**Goal:** To establish the foundational rotation mathematics and data structures required for dynamic crystal orientation changes.

**Deliverable:** A modified `Crystal` class with implemented `get_rotated_real_vectors` method and updated `CrystalConfig` with rotation parameters.

**Implementation Checklist:**
*   The detailed, step-by-step implementation for this phase is tracked in: `[ ] phase_1_checklist.md`

**Key Tasks Summary:**
*   Add rotation parameters (`phi`, `mosaic_spread_deg`, `n_phi_steps`, `n_mosaic_domains`) to `CrystalConfig`
*   Implement `get_rotated_real_vectors` method in `Crystal` class to handle phi and mosaic rotations
*   Create utility functions for spindle rotation (`rotate_axis`) and mosaic domain generation (`rotate_umat`)
*   Add comprehensive unit tests for rotation mathematics and gradient correctness

**Success Test:** All tasks in `phase_1_checklist.md` are marked as done. The `get_rotated_real_vectors` method correctly applies phi rotations and generates mosaic domains. Unit tests pass including `torch.autograd.gradcheck` for all rotation parameters.

**Duration:** 2-3 days

---

### **Phase 2: Simulator Integration**

**Goal:** To integrate the rotation capabilities into the main simulation pipeline, enabling multi-orientation diffraction calculations.

**Deliverable:** An updated `Simulator` class that processes rotated crystal orientations and properly sums contributions across phi steps and mosaic domains.

**Implementation Checklist:**
*   The detailed, step-by-step implementation for this phase is tracked in: `[ ] phase_2_checklist.md`

**Key Tasks Summary:**
*   Modify `Simulator.run` method to iterate over phi angles and mosaic domains
*   Update the Miller index calculation to use rotated real-space vectors
*   Implement proper averaging/summing of intensities across all orientations
*   Add configuration validation for rotation parameters

**Success Test:** All tasks in `phase_2_checklist.md` are marked as done. The simulator can process rotation parameters and generate diffraction images that show expected rotation effects. Integration tests demonstrate correct phi rotation behavior.

**Duration:** 2-3 days

---

### **Phase 3: Validation and Golden Test Integration**

**Goal:** To validate the rotation implementation against C-code reference data and establish comprehensive test coverage.

**Deliverable:** A complete validation suite with golden test case reproduction and demonstrated gradient correctness for rotation parameters.

**Implementation Checklist:**
*   The detailed, step-by-step implementation for this phase is tracked in: `[ ] phase_3_checklist.md`

**Key Tasks Summary:**
*   Generate new golden reference data from C code with mosaicity enabled (`simple_cubic_mosaic`)
*   Implement integration test to reproduce golden case with >0.99 correlation
*   Add gradient tests for `phi` and `mosaic_spread_deg` parameters
*   Create demo script showcasing rotation capabilities and spot broadening effects
*   Update documentation with rotation usage examples

**Success Test:** All tasks in `phase_3_checklist.md` are marked as done. The `simple_cubic_mosaic` integration test passes with high correlation. All gradient tests pass. The demo script successfully generates images showing mosaicity effects.

**Duration:** 2-3 days

---

## 📝 **PHASE TRACKING**

- ✅ **Phase 1:** Core Rotation Infrastructure (see `phase_1_checklist.md`)
- ✅ **Phase 2:** Simulator Integration (see `phase_2_checklist.md`)
- [ ] **Phase 3:** Validation and Golden Test Integration (see `phase_3_checklist.md`)

**Current Phase:** Phase 3: Validation and Golden Test Integration
**Next Milestone:** A complete validation suite with golden test case reproduction and demonstrated gradient correctness for rotation parameters.