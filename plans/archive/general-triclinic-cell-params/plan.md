# R&D Plan: General Triclinic Cell Parameters

*Created: 2025-07-29*

## 🎯 **OBJECTIVE & HYPOTHESIS**

**Objective:** Replace the hard-coded simple cubic unit cell in the PyTorch nanoBragg implementation with a fully general, differentiable triclinic lattice calculation system.

**Hypothesis:** By implementing a differentiable geometry engine that transforms from 6 cell parameters (a, b, c, α, β, γ) to real and reciprocal space vectors, we can enable the simulation and gradient-based refinement of any crystal system while maintaining numerical stability and backward compatibility.

**Key Deliverables:**
1. Updated `CrystalConfig` with 6 cell parameters
2. Refactored `Crystal` class with dynamic geometry calculation
3. Triclinic test case with golden reference data
4. Comprehensive test suite including gradient verification
5. Documentation updates

---

## ✅ **VALIDATION & VERIFICATION PLAN**

### **Success Criteria:**
1. **Correctness:** Triclinic test case matches C-code golden reference with >0.99 correlation
2. **Backward Compatibility:** Simple cubic test case continues to pass
3. **Differentiability:** All 6 cell parameters pass `torch.autograd.gradcheck`
4. **Numerical Stability:** Edge cases (highly oblique cells) handled without NaN/Inf
5. **Performance:** <10% regression in simulation speed

### **Test Cases:**
- **Unit Tests:**
  - Metric tensor duality: G = (UB)ᵀ(UB)
  - Volume identity: V = abc√(1 + 2cosαcosβcosγ - cos²α - cos²β - cos²γ)
  - Resolution shell calculations
  - Rotation invariance of |G|
  
- **Integration Tests:**
  - Simple cubic regression test
  - Triclinic P1 golden test
  - Random cell property tests
  
- **Gradient Tests:**
  - Individual parameter gradcheck
  - Joint 6-parameter gradcheck
  - Second-order gradients (gradgradcheck)

### **Risk Mitigation:**
- **Numerical Instability:** Use float64 precision and careful clamping
- **Performance Regression:** Profile and optimize tensor operations
- **Breaking Changes:** Maintain backward-compatible defaults
- **Complex Debugging:** Create detailed trace logging for geometry calculations

---

## 📁 **File Organization**

**Initiative Path:** `plans/active/general-triclinic-cell-params/`

**Next Step:** Run `/implementation` to generate the phased implementation plan.