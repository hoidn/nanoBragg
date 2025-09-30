<!-- ACTIVE IMPLEMENTATION PLAN -->
<!-- DO NOT MISTAKE THIS FOR A TEMPLATE. THIS IS THE OFFICIAL SOURCE OF TRUTH FOR THE PROJECT'S PHASED PLAN. -->

# Phased Implementation Plan

**Project:** General Triclinic Cell Parameters
**Initiative Path:** `plans/active/general-triclinic-cell-params/`

---
## Git Workflow Information
**Feature Branch:** feature/general-triclinic-cell-params
**Baseline Branch:** devel
**Baseline Commit Hash:** 8d42cff01d0a26178d17e885fba7615e1200e20a
**Last Phase Commit Hash:** 8d42cff01d0a26178d17e885fba7615e1200e20a
---

**Created:** 2025-07-29
**Core Technologies:** Python, PyTorch, NumPy

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

**Overall Goal:** Enable simulation and refinement of any crystal system by implementing a differentiable geometry engine for triclinic lattice calculations.

**Total Estimated Duration:** 5-6 days

---

## 📋 **IMPLEMENTATION PHASES**

### **Phase 1: Prerequisite Setup & Golden Data Generation**

**Goal:** Expand the configuration system and generate triclinic golden reference data from the C code.

**Deliverable:** Extended `CrystalConfig` with 6 cell parameters and a triclinic_P1 golden test case.

**Estimated Duration:** 1 day

**Key Tasks:**
- Extend `CrystalConfig` to include `cell_a`, `cell_b`, `cell_c`, `cell_alpha`, `cell_beta`, `cell_gamma`
- Generate triclinic P1 structure factors using refmac5 or similar tool
- Run C-code nanoBragg with triclinic parameters to create golden reference image
- Create test infrastructure for the new triclinic test case
- Update CLAUDE.md with crystallographic conventions

**Dependencies:** None (first phase)

**Implementation Checklist:** `phase_1_checklist.md`

**Success Test:** Golden reference data exists and can be loaded by test infrastructure.

---

### **Phase 2: Core Geometry Engine & Unit Testing**

**Goal:** Implement the differentiable geometry calculations that transform cell parameters to vectors.

**Deliverable:** A working `compute_cell_tensors` method with comprehensive unit tests.

**Estimated Duration:** 2 days

**Key Tasks:**
- Implement `compute_cell_tensors` method in Crystal class
- Replace hard-coded vectors with dynamic calculation
- Create unit tests for metric tensor duality
- Implement volume calculation and verification
- Add resolution shell calculations
- Test rotation invariance of reciprocal vector magnitudes

**Dependencies:** Requires Phase 1 completion.

**Implementation Checklist:** `phase_2_checklist.md`

**Success Test:** All geometry unit tests pass with >1e-10 precision.

---

### **Phase 3: Simulator Integration & End-to-End Validation**

**Goal:** Integrate the dynamic geometry into the Simulator and validate against golden data.

**Deliverable:** A fully integrated simulator that passes both simple cubic and triclinic test cases.

**Estimated Duration:** 1-2 days

**Key Tasks:**
- Update Simulator to use dynamic crystal geometry
- Modify HKL range calculation for non-cubic cells
- Implement triclinic_P1 integration test
- Verify simple_cubic backward compatibility
- Performance profiling and optimization
- Debug any discrepancies with C-code output

**Dependencies:** Requires Phase 2 completion.

**Implementation Checklist:** `phase_3_checklist.md`

**Success Test:** Both simple_cubic and triclinic_P1 tests achieve >0.99 correlation with C-code.

---

### **Final Phase: Differentiability Verification & Documentation**

**Goal:** Validate gradient correctness and update all documentation for the new capability.

**Deliverable:** A fully tested and documented triclinic cell parameter system ready for production use.

**Estimated Duration:** 1 day

**Key Tasks:**
- Individual gradcheck tests for each of the 6 cell parameters
- Joint gradcheck on concatenated parameter vector
- Second-order gradient verification (gradgradcheck)
- Property-based testing with random unit cells
- Update README.md with triclinic examples
- Create tutorial notebook demonstrating cell refinement
- Update API documentation

**Dependencies:** All previous phases complete.

**Implementation Checklist:** `phase_final_checklist.md`

**Success Test:** All gradcheck tests pass and documentation accurately reflects new capabilities.

---

## 📊 **PROGRESS TRACKING**

### Phase Status:
- [ ] **Phase 1:** Prerequisite Setup & Golden Data Generation - 0% complete
- [ ] **Phase 2:** Core Geometry Engine & Unit Testing - 0% complete
- [ ] **Phase 3:** Simulator Integration & End-to-End Validation - 0% complete
- [ ] **Final Phase:** Differentiability Verification & Documentation - 0% complete

**Current Phase:** Phase 1: Prerequisite Setup & Golden Data Generation
**Overall Progress:** ░░░░░░░░░░░░░░░░ 0%

---

## 🚀 **GETTING STARTED**

1.  **Generate Phase 1 Checklist:** Run `/phase-checklist 1` to create the detailed checklist.
2.  **Begin Implementation:** Follow the checklist tasks in order.
3.  **Track Progress:** Update task states in the checklist as you work.
4.  **Request Review:** Run `/complete-phase` when all Phase 1 tasks are done to generate a review request.

---

## ⚠️ **RISK MITIGATION**

**Potential Blockers:**
- **Risk:** Numerical instability in highly oblique unit cells
  - **Mitigation:** Use float64 precision and implement careful clamping with epsilon=1e-24
- **Risk:** Performance regression from dynamic calculations
  - **Mitigation:** Profile early and optimize tensor operations, consider caching invariant calculations
- **Risk:** Gradient instability near degenerate cells
  - **Mitigation:** Implement robust parameterization (softplus for lengths, sigmoid for angles)

**Rollback Plan:**
- **Git:** Each phase will be a separate, reviewed commit on the feature branch, allowing for easy reverts.
- **Backward Compatibility:** Simple cubic test case ensures existing functionality remains intact.