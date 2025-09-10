# Detailed Fix Implementation Plan for Detector Geometry Correlation Issues

**Date**: 2025-01-09  
**Objective**: Systematically fix all identified root causes to achieve >0.999 correlation  
**Current Status**: Multiple root causes identified through systematic testing  
**Target Completion**: 4-6 hours of focused implementation  

---

## Executive Summary

Systematic hypothesis testing has revealed **4 compounding root causes** creating the detector geometry correlation issues:
1. **CRITICAL**: Fundamental coordinate system error (192.67mm in identity configuration)
2. **HIGH**: Twotheta rotation axis mismatch (66.18mm error)
3. **MEDIUM**: MOSFLM beam center convention missing (up to 23.33mm error)
4. **MEDIUM**: Distance correction formula missing (2.8-6.4mm error)

This plan provides a surgical, incremental approach to fix each issue with validation at every step.

---

## PHASE 1: Fix Fundamental Coordinate System (CRITICAL)
**Timeline**: 1-2 hours  
**Risk**: HIGH - Core geometric calculations  
**Impact**: Resolves 192.67mm error in identity configuration  

### Pre-Implementation Checklist
- [ ] Create backup of current detector.py implementation
- [ ] Document current coordinate system assumptions
- [ ] Set up identity configuration test case
- [ ] Capture baseline measurements for rollback comparison

### Implementation Checklist

#### 1.1 Analyze Current Coordinate Mapping
- [ ] Trace current axis assignments in PyTorch Detector class
- [ ] Compare with C implementation coordinate system
- [ ] Document discrepancies in axis definitions
- [ ] Identify sign convention differences

#### 1.2 Fix Coordinate System Basis
- [ ] **PRIMARY FIX**: Update detector basis vectors in `_initialize_detector_frame()`
  ```python
  # Current (WRONG):
  self.fdet_vec = torch.tensor([0, 1, 0])  # Fast along Y
  self.sdet_vec = torch.tensor([0, 0, 1])  # Slow along Z
  self.odet_vec = torch.tensor([1, 0, 0])  # Origin along X
  
  # Fixed (CORRECT - matching C):
  self.fdet_vec = torch.tensor([0, -1, 0])  # Fast along negative Y
  self.sdet_vec = torch.tensor([0, 0, -1])  # Slow along negative Z  
  self.odet_vec = torch.tensor([1, 0, 0])  # Origin along X (beam direction)
  ```

- [ ] Update pixel coordinate calculations to match C convention
- [ ] Fix beam center application in detector frame
- [ ] Ensure rotation matrices apply to correct axes

#### 1.3 Fix pix0_vector Calculation
- [ ] Update `_calculate_pix0_vector()` method:
  ```python
  # Add proper coordinate transformation
  def _calculate_pix0_vector(self):
      # Apply MOSFLM convention if applicable
      if self.convention == "MOSFLM":
          # Swap axes and apply sign corrections
          beam_f = self.beam_center_s  # Note: S maps to F in MOSFLM
          beam_s = self.beam_center_f  # Note: F maps to S in MOSFLM
      else:
          beam_f = self.beam_center_f
          beam_s = self.beam_center_s
      
      # Calculate with correct basis vectors
      pix0 = (self.distance_m * self.odet_vec_rotated +
              beam_s * self.sdet_vec_rotated +
              beam_f * self.fdet_vec_rotated)
      return pix0
  ```

### Validation Checklist
- [ ] **Test 1**: Identity configuration (no rotations)
  - Expected: pix0_vector error < 0.1mm
  - Command: `python scripts/verify_detector_geometry.py --rotx 0 --roty 0 --rotz 0 --twotheta 0`
  
- [ ] **Test 2**: Verify basis vector orthonormality
  - Check: dot(fdet, sdet) = 0, dot(fdet, odet) = 0, dot(sdet, odet) = 0
  - Check: |fdet| = |sdet| = |odet| = 1
  
- [ ] **Test 3**: Baseline correlation unchanged
  - Run: Simple cubic test case
  - Expected: Correlation still >0.99

### Rollback Plan
- [ ] If validation fails, restore backup detector.py
- [ ] Document specific failure for debugging
- [ ] Consider incremental axis-by-axis fixes

---

## PHASE 2: Fix Twotheta Rotation Axis (HIGH)
**Timeline**: 30 minutes  
**Risk**: MEDIUM - Isolated rotation fix  
**Impact**: Resolves 66.18mm error (48mm Y, -42mm Z components)  

### Pre-Implementation Checklist
- [ ] Locate twotheta axis definition in code
- [ ] Create test with only twotheta rotation
- [ ] Document current axis vector

### Implementation Checklist

#### 2.1 Update Twotheta Axis Vector
- [ ] **PRIMARY FIX**: Change rotation axis in detector.py
  ```python
  # In get_twotheta_rotation_matrix() or equivalent:
  
  # Current (WRONG):
  twotheta_axis = torch.tensor([0.0, 1.0, 0.0])  # Y-axis
  
  # Fixed (CORRECT - matching C):
  twotheta_axis = torch.tensor([0.0, 0.0, -1.0])  # Negative Z-axis
  ```

#### 2.2 Verify Rotation Direction
- [ ] Confirm rotation follows right-hand rule around new axis
- [ ] Check sign of twotheta angle (positive = clockwise when looking along -Z)
- [ ] Update any dependent calculations

### Validation Checklist
- [ ] **Test 1**: Twotheta-only rotation
  - Command: `python scripts/verify_detector_geometry.py --rotx 0 --roty 0 --rotz 0 --twotheta 15`
  - Expected: Error reduced by ~66mm
  
- [ ] **Test 2**: Combined rotations
  - Command: `python scripts/verify_detector_geometry.py --rotx 5 --roty 3 --rotz 2 --twotheta 15`
  - Expected: Significant correlation improvement
  
- [ ] **Test 3**: Multiple twotheta angles
  - Test angles: [0, 5, 10, 15, 20, 30]
  - Verify error scales appropriately

### Rollback Plan
- [ ] Simple one-line revert if needed
- [ ] Document rotation matrix values for comparison

---

## PHASE 3: Implement MOSFLM Beam Center Convention (MEDIUM)
**Timeline**: 1 hour  
**Risk**: LOW - Additive correction  
**Impact**: Resolves up to 23.33mm scaling error  

### Pre-Implementation Checklist
- [ ] Review MOSFLM convention documentation
- [ ] Identify all beam center calculation points
- [ ] Create beam center sweep test

### Implementation Checklist

#### 3.1 Add MOSFLM 0.5-Pixel Adjustment
- [ ] **PRIMARY FIX**: Update beam center calculation
  ```python
  def _apply_mosflm_convention(self, beam_center_mm):
      # MOSFLM adds 0.5 pixel to beam center
      adjusted = beam_center_mm + 0.5 * self.pixel_size_mm
      return adjusted
  ```

#### 3.2 Implement Axis Swapping
- [ ] Apply F↔S axis swap for MOSFLM:
  ```python
  if self.convention == "MOSFLM":
      # MOSFLM convention swaps axes
      final_beam_f = self._apply_mosflm_convention(self.beam_center_s)
      final_beam_s = self._apply_mosflm_convention(self.beam_center_f)
  else:
      final_beam_f = self.beam_center_f
      final_beam_s = self.beam_center_s
  ```

#### 3.3 Update Default Beam Center
- [ ] Change default from 51.2mm to 51.25mm for MOSFLM
- [ ] Document convention in code comments

### Validation Checklist
- [ ] **Test 1**: Default beam center
  - Use beam center = 51.25mm
  - Expected: Better correlation than 51.2mm
  
- [ ] **Test 2**: Beam center sweep
  - Test centers: [0, 25.6, 51.2, 76.8, 102.4]
  - Verify linear error relationship eliminated
  
- [ ] **Test 3**: Convention switching
  - Test both MOSFLM and XDS conventions
  - Ensure each works correctly

### Rollback Plan
- [ ] Convention can be disabled via parameter
- [ ] Keep non-MOSFLM path intact

---

## PHASE 4: Add Distance Correction Formula (MEDIUM)
**Timeline**: 45 minutes  
**Risk**: LOW - Additional calculation  
**Impact**: Resolves 2.8-6.4mm tilt-dependent error  

### Pre-Implementation Checklist
- [ ] Review C implementation of distance correction
- [ ] Understand geometric basis for correction
- [ ] Create tilt angle test cases

### Implementation Checklist

#### 4.1 Implement Effective Distance Calculation
- [ ] **PRIMARY FIX**: Add distance correction method
  ```python
  def get_effective_distance(self):
      """Apply geometric distance correction for tilted detector"""
      # Get rotated detector normal (odet after all rotations)
      detector_normal = self.get_rotated_odet_vector()
      
      # Beam direction (along X-axis)
      beam_direction = torch.tensor([1.0, 0.0, 0.0], device=self.device)
      
      # Calculate cosine of angle between beam and detector normal
      cos_angle = torch.dot(beam_direction, detector_normal)
      
      # Apply correction: effective_distance = nominal_distance / cos(tilt)
      effective_distance = self.distance_m / cos_angle
      
      return effective_distance
  ```

#### 4.2 Apply Correction in Pixel Calculations
- [ ] Use effective distance in diffraction calculations
- [ ] Update pixel-to-lab coordinate transformations
- [ ] Ensure gradient flow maintained for differentiability

### Validation Checklist
- [ ] **Test 1**: Distance scaling
  - Test distances: [50, 100, 200, 400]
  - Verify correction scales appropriately
  
- [ ] **Test 2**: Tilt angle dependence
  - Test various rotation combinations
  - Error should decrease with correction applied
  
- [ ] **Test 3**: Edge cases
  - Near-perpendicular detector (cos_angle → 0)
  - Add appropriate bounds checking

### Rollback Plan
- [ ] Distance correction can be toggled via flag
- [ ] Original distance calculation preserved

---

## PHASE 5: Integration Testing & Final Validation
**Timeline**: 1 hour  
**Risk**: LOW - Validation only  
**Impact**: Confirms >0.999 correlation achieved  

### Pre-Integration Checklist
- [ ] All individual phases completed and validated
- [ ] Backup of all original code created
- [ ] Test suite ready for comprehensive validation

### Integration Testing Checklist

#### 5.1 Comprehensive Test Suite
- [ ] **Test 1**: Simple cubic (baseline)
  - Configuration: No rotations, standard parameters
  - Expected: >0.999 correlation maintained
  
- [ ] **Test 2**: Tilted detector (primary target)
  - Configuration: rotx=5, roty=3, rotz=2, twotheta=15
  - Expected: >0.999 correlation (up from 0.040)
  
- [ ] **Test 3**: Parameter sweep
  - Vary all parameters systematically
  - No configuration should have <0.99 correlation
  
- [ ] **Test 4**: Edge cases
  - Extreme rotations (45°, 90°)
  - Very close/far distances
  - Off-center beam positions

#### 5.2 Performance Validation
- [ ] Computation time comparable to original
- [ ] Memory usage not significantly increased
- [ ] Gradient flow maintained for all parameters

#### 5.3 Regression Testing
- [ ] All existing tests still pass
- [ ] No degradation in working configurations
- [ ] Crystal lattice calculations unaffected

### Final Validation Checklist
- [ ] **Correlation Targets Met**:
  - Simple cubic: >0.999 ✓
  - Tilted detector: >0.999 ✓
  - All test configs: >0.99 ✓
  
- [ ] **Error Magnitudes**:
  - Identity configuration: <0.1mm ✓
  - Maximum error any config: <1mm ✓
  - RMS error across tests: <0.5mm ✓

### Documentation Checklist
- [ ] Update detector.md architecture document
- [ ] Document all convention assumptions
- [ ] Create migration guide for existing code
- [ ] Update C-to-PyTorch mapping document
- [ ] Add comprehensive inline comments

---

## Success Criteria Summary

### Quantitative Metrics
| Metric | Current | Target | Phase |
|--------|---------|--------|-------|
| Identity config error | 192.67mm | <0.1mm | Phase 1 |
| Twotheta rotation error | 66.18mm | <1mm | Phase 2 |
| Beam center scaling error | 23.33mm | <1mm | Phase 3 |
| Distance correction error | 6.4mm | <0.5mm | Phase 4 |
| Tilted detector correlation | 0.040 | >0.999 | Phase 5 |

### Qualitative Criteria
- [ ] All fixes are surgical and isolated
- [ ] No regression in working configurations
- [ ] Code remains maintainable and documented
- [ ] Gradient flow preserved for optimization
- [ ] Performance comparable to original

---

## Risk Management

### High-Risk Items
1. **Coordinate system changes** - Could break many calculations
   - Mitigation: Incremental testing, comprehensive backups
   
2. **Sign convention changes** - May affect downstream code
   - Mitigation: Trace all dependencies first

### Rollback Strategy
1. Each phase independently revertible
2. Git commits after each validated phase
3. Backup files maintained until full validation
4. Test suite confirms no regression

---

## Implementation Schedule

```
Hour 1-2: Phase 1 (Coordinate System)
  ├── 30 min: Analysis and planning
  ├── 45 min: Implementation
  └── 45 min: Validation

Hour 2.5: Phase 2 (Twotheta Axis)
  ├── 10 min: Implementation
  └── 20 min: Validation

Hour 3.5: Phase 3 (MOSFLM Convention)
  ├── 30 min: Implementation
  └── 30 min: Validation

Hour 4.5: Phase 4 (Distance Correction)
  ├── 25 min: Implementation
  └── 20 min: Validation

Hour 5-6: Phase 5 (Integration)
  ├── 30 min: Full test suite
  ├── 20 min: Documentation
  └── 10 min: Final validation
```

---

## Conclusion

This plan provides a systematic, low-risk approach to fixing all identified root causes. Each phase is independently valuable and testable, allowing for incremental progress and easy rollback if issues arise. The surgical nature of the fixes, combined with comprehensive validation at each step, ensures we achieve the >0.999 correlation target while maintaining code quality and performance.