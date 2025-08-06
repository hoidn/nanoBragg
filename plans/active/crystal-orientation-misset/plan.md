# R&D Plan: Crystal Orientation Misset

*Created: 2025-01-20*

## 🎯 **OBJECTIVE & HYPOTHESIS**

**Initiative Name:** Crystal Orientation Misset

**Problem Statement:** The PyTorch simulator successfully models triclinic unit cells and applies dynamic phi and mosaic rotations. However, it lacks the ability to define the crystal's initial static orientation in the lab frame (the "missetting" or U matrix). This missing feature prevents accurate simulation of arbitrarily oriented crystals and blocks validation against the triclinic_P1 golden test case.

**Proposed Solution:** Implement a differentiable three-angle static orientation system (misset_deg tuple) applied to base lattice vectors before dynamic rotations. This follows the nanoBragg.c convention of sequential rotations around lab X, Y, then Z axes.

**Success Hypothesis:** With properly implemented misset rotations, the triclinic_P1 integration test will achieve ≥0.990 Pearson correlation with the golden reference image, validating the complete crystal geometry engine.

**Initiative Scope:**
- IN SCOPE: Three-angle misset rotation system, differentiability, integration with existing rotation pipeline
- OUT OF SCOPE: Alternative representations (quaternions, matrices), complex goniometer models, convenience constructors

---

## 🔬 **EXPERIMENTAL DESIGN & CAPABILITIES**

**Core Capabilities:**
1. **Static Orientation System**: Apply misset rotations to reciprocal space vectors (a*, b*, c*) using three Euler-like angles
2. **Rotation Order**: Follow nanoBragg.c convention - sequential rotations around fixed X→Y→Z axes (lines 1911-1916)
3. **Differentiability**: All three misset angles must support gradient computation for refinement
4. **Integration**: Correctly compose with existing phi and mosaic rotations in the proper order

**Technical Architecture:**
- Extend `CrystalConfig` with `misset_deg: Tuple[float, float, float]` parameter
- Add `_apply_static_orientation()` helper method in `Crystal` class
- Apply rotations to reciprocal vectors after their calculation in `compute_cell_tensors()`
- Maintain full differentiability through PyTorch tensor operations

**Key Design Decisions:**
- Apply misset to reciprocal space vectors (matching C-code behavior)
- Use active, right-hand rule rotations
- Implement as property-based recalculation to preserve gradients

---

## ✅ **VALIDATION & VERIFICATION PLAN**

**Unit Tests:**
- [ ] Test rotation matrix construction for standard 90° rotations
- [ ] Verify identity matrix for zero angles (tolerance 1e-12)
- [ ] Confirm XYZ rotation order with non-commutative test cases
- [ ] Validate reciprocal vector transformation matches trace.log values

**Integration Tests:**
- [ ] **PRIMARY**: triclinic_P1 test with misset=[-89.968546, -31.328953, 177.753396] achieves ≥0.990 correlation
- [ ] **REGRESSION**: simple_cubic test continues passing with default zero misset

**Gradient Tests:**
- [ ] torch.autograd.gradcheck passes for all three misset angles
- [ ] Test at non-zero angles to avoid degenerate Jacobian
- [ ] Parameters: dtype=float64, eps=1e-6, atol=1e-6, rtol=1e-4

**Documentation:**
- [ ] Update rotation pipeline docs: Unit Cell → Reciprocal Space → Static Misset → Dynamic Phi → Mosaic
- [ ] Add C-code references with line numbers to all rotation functions
- [ ] Update README.md with new crystal orientation capabilities

**Success Metrics:**
- triclinic_P1 correlation ≥ 0.990
- All gradient tests passing
- Zero regression in existing tests
- Complete rotation pipeline implemented

---

## 📁 **File Organization**

**Initiative Path:** `plans/active/crystal-orientation-misset/`

**Next Step:** Run `/implementation` to generate the phased implementation plan.