# Basis Vector Unification Fix Checklist

**Critical Issue**: Three different sets of basis vectors are being used in different code paths  
**Impact**: Tilted detector correlation only 34.7% instead of >99.9%  
**Root Cause**: Hardcoded path has correct vectors, calculated path has wrong vectors  
**Solution**: Unify all paths to use the correct basis vectors  

---

## 🔴 PHASE A: Unify Basis Vectors (CRITICAL - Main Fix)

### Pre-Fix Validation
- [ ] Run baseline test to confirm current state:
  ```bash
  python scripts/verify_detector_geometry.py --rotx 5 --roty 3 --rotz 2 --twotheta 15 --output pre_fix_baseline.json
  # Expected: ~0.347 correlation (current broken state)
  ```

- [ ] Test identity through calculated path (force non-default):
  ```bash
  python scripts/verify_detector_geometry.py --rotx 0.001 --roty 0 --rotz 0 --twotheta 0 --output pre_fix_calculated.json
  # Expected: Poor correlation (uses wrong initial vectors)
  ```

### Step 1: Fix `_calculate_basis_vectors()` Initial Vectors
**File**: `src/nanobrag_torch/models/detector.py`  
**Lines**: 606-616

- [ ] **FIND** these lines in `_calculate_basis_vectors()`:
```python
# Line 608-616 (WRONG vectors)
if c.detector_convention == DetectorConvention.MOSFLM:
    fdet_vec = torch.tensor(
        [0.0, -1.0, 0.0], device=self.device, dtype=self.dtype  # WRONG!
    )
    sdet_vec = torch.tensor(
        [0.0, 0.0, -1.0], device=self.device, dtype=self.dtype  # WRONG!
    )
    odet_vec = torch.tensor(
        [1.0, 0.0, 0.0], device=self.device, dtype=self.dtype
    )
```

- [ ] **REPLACE** with correct vectors (matching hardcoded path):
```python
# CORRECTED to match working hardcoded path
if c.detector_convention == DetectorConvention.MOSFLM:
    fdet_vec = torch.tensor(
        [0.0, 0.0, 1.0], device=self.device, dtype=self.dtype  # Fast along +Z (CORRECT)
    )
    sdet_vec = torch.tensor(
        [0.0, -1.0, 0.0], device=self.device, dtype=self.dtype  # Slow along -Y (CORRECT)
    )
    odet_vec = torch.tensor(
        [1.0, 0.0, 0.0], device=self.device, dtype=self.dtype   # Normal along +X (CORRECT)
    )
```

### Step 2: Fix SAMPLE Pivot Initial Vectors
**File**: `src/nanobrag_torch/models/detector.py`  
**Lines**: 376-380

- [ ] **FIND** these lines in `_calculate_pix0_vector()`:
```python
# Line 378-380 (WRONG vectors for SAMPLE pivot)
if self.config.detector_convention == DetectorConvention.MOSFLM:
    fdet_initial = torch.tensor([0.0, -1.0, 0.0], device=self.device, dtype=self.dtype)  # WRONG!
    sdet_initial = torch.tensor([0.0, 0.0, -1.0], device=self.device, dtype=self.dtype)  # WRONG!
    odet_initial = torch.tensor([1.0, 0.0, 0.0], device=self.device, dtype=self.dtype)
```

- [ ] **REPLACE** with correct vectors:
```python
# CORRECTED to match working vectors
if self.config.detector_convention == DetectorConvention.MOSFLM:
    fdet_initial = torch.tensor([0.0, 0.0, 1.0], device=self.device, dtype=self.dtype)   # Fast along +Z (CORRECT)
    sdet_initial = torch.tensor([0.0, -1.0, 0.0], device=self.device, dtype=self.dtype)  # Slow along -Y (CORRECT)
    odet_initial = torch.tensor([1.0, 0.0, 0.0], device=self.device, dtype=self.dtype)   # Normal along +X (CORRECT)
```

### Step 3: Verify Hardcoded Path Consistency
**Lines**: 88-96

- [ ] **CONFIRM** hardcoded path already has correct vectors:
```python
# This should already be correct (no change needed):
self.fdet_vec = torch.tensor([0.0, 0.0, 1.0], ...)   # ✓ Correct
self.sdet_vec = torch.tensor([0.0, -1.0, 0.0], ...)  # ✓ Correct
self.odet_vec = torch.tensor([1.0, 0.0, 0.0], ...)   # ✓ Correct
```

### Phase A Validation
- [ ] Test identity through calculated path (force non-default):
  ```bash
  python scripts/verify_detector_geometry.py --rotx 0.001 --roty 0 --rotz 0 --twotheta 0 --output phase_a_calculated.json
  # Expected: >0.99 correlation (now uses correct vectors)
  ```

- [ ] Test main tilted configuration:
  ```bash
  python scripts/verify_detector_geometry.py --rotx 5 --roty 3 --rotz 2 --twotheta 15 --output phase_a_tilted.json
  # Expected: SIGNIFICANT improvement from 0.347 → >0.9
  ```

**CHECKPOINT**: If correlation doesn't improve significantly, STOP and debug

---

## 🟠 PHASE B: Validate Rotation Pipeline

### Step 1: Test Individual Rotations
- [ ] Test rotx only:
  ```bash
  python scripts/verify_detector_geometry.py --rotx 5 --roty 0 --rotz 0 --twotheta 0 --output test_rotx.json
  ```

- [ ] Test roty only:
  ```bash
  python scripts/verify_detector_geometry.py --rotx 0 --roty 3 --rotz 0 --twotheta 0 --output test_roty.json
  ```

- [ ] Test rotz only:
  ```bash
  python scripts/verify_detector_geometry.py --rotx 0 --roty 0 --rotz 2 --twotheta 0 --output test_rotz.json
  ```

- [ ] Test twotheta only:
  ```bash
  python scripts/verify_detector_geometry.py --rotx 0 --roty 0 --rotz 0 --twotheta 15 --output test_twotheta.json
  ```

### Step 2: Verify Rotation Order
- [ ] Check that `angles_to_rotation_matrix()` applies: X → Y → Z
- [ ] Verify twotheta is applied AFTER rotx/roty/rotz
- [ ] Confirm rotation matrices are right-handed

### Phase B Validation
- [ ] All individual rotations should show >0.95 correlation
- [ ] Combined rotations should be consistent

---

## 🟡 PHASE C: Fix Beam Center Logic

### Step 1: Verify MOSFLM Convention in BEAM Pivot
**Lines**: 348-351

- [ ] **CHECK** beam center calculation:
```python
# Should have +0.5 pixel offset for MOSFLM
Fbeam_pixels = self.config.beam_center_f / self.config.pixel_size_mm
Sbeam_pixels = self.config.beam_center_s / self.config.pixel_size_mm
Fbeam = (Fbeam_pixels + 0.5) * self.pixel_size  # ✓ Has +0.5
Sbeam = (Sbeam_pixels + 0.5) * self.pixel_size  # ✓ Has +0.5
```

### Step 2: Fix SAMPLE Pivot Beam Center
**Lines**: 395-402

- [ ] **VERIFY** axis mapping is consistent:
```python
# Check that SAMPLE pivot uses same convention as BEAM pivot
# Fclose should map from beam_center_s (not beam_center_f)
# Sclose should map from beam_center_f (not beam_center_s)
```

- [ ] **FIX** if needed (swap the mappings):
```python
# MOSFLM convention with axis swap:
Fclose = (self.beam_center_f + 0.5) * self.pixel_size  # F comes from beam_f
Sclose = (self.beam_center_s + 0.5) * self.pixel_size  # S comes from beam_s
```

### Phase C Validation
- [ ] Test with different beam centers:
  ```bash
  python scripts/verify_detector_geometry.py --beam 51.25 51.25 --rotx 5 --roty 3 --rotz 2 --twotheta 15
  python scripts/verify_detector_geometry.py --beam 25.6 25.6 --rotx 5 --roty 3 --rotz 2 --twotheta 15
  ```

---

## ✅ PHASE D: Final Integration Testing

### Comprehensive Test Suite
- [ ] Simple cubic (identity):
  ```bash
  python scripts/verify_detector_geometry.py --rotx 0 --roty 0 --rotz 0 --twotheta 0 --output final_simple.json
  # Expected: >0.999 correlation
  ```

- [ ] Main tilted configuration:
  ```bash
  python scripts/verify_detector_geometry.py --rotx 5 --roty 3 --rotz 2 --twotheta 15 --beam 51.25 51.25 --output final_tilted.json
  # Expected: >0.999 correlation (SUCCESS!)
  ```

- [ ] Test both pivot modes:
  ```bash
  # BEAM pivot (default)
  python scripts/verify_detector_geometry.py --rotx 5 --roty 3 --rotz 2 --twotheta 15 --pivot beam --output final_beam.json
  
  # SAMPLE pivot
  python scripts/verify_detector_geometry.py --rotx 5 --roty 3 --rotz 2 --twotheta 15 --pivot sample --output final_sample.json
  ```

### Success Criteria
- [ ] **Identity correlation**: >0.999 ✓
- [ ] **Tilted correlation**: >0.999 ✓
- [ ] **All test cases**: >0.99 ✓
- [ ] **pix0_vector error**: <1mm ✓
- [ ] **Gradient flow**: Preserved ✓

### Final Verification
- [ ] Run gradient check:
  ```python
  import torch
  from src.nanobrag_torch.models.detector import Detector
  
  config = {
      'detector_rotx_deg': torch.tensor(5.0, requires_grad=True),
      'detector_roty_deg': torch.tensor(3.0, requires_grad=True),
      'detector_rotz_deg': torch.tensor(2.0, requires_grad=True),
      'detector_twotheta_deg': torch.tensor(15.0, requires_grad=True)
  }
  detector = Detector(config)
  positions = detector.get_pixel_positions()
  loss = positions.sum()
  loss.backward()
  print("Gradients exist!" if config['detector_rotx_deg'].grad is not None else "BROKEN!")
  ```

---

## 🚨 Emergency Rollback

If anything breaks:
```bash
# Restore backup
cp src/nanobrag_torch/models/detector.py.backup src/nanobrag_torch/models/detector.py
```

---

## 📊 Expected Timeline

- **Phase A**: 10 minutes (main fix - basis vector unification)
- **Phase B**: 5 minutes (rotation validation)
- **Phase C**: 5 minutes (beam center verification)
- **Phase D**: 10 minutes (integration testing)
- **Total**: 30 minutes

---

## 🎯 Success Indicators

| Metric | Current | After Phase A | Final Target |
|--------|---------|---------------|--------------|
| Identity | 0.993 | >0.99 | >0.999 |
| Tilted | 0.347 | >0.9 | >0.999 |
| Basis Vector Match | 3 different sets | Unified | Unified |
| Code Path Consistency | Broken | Fixed | Fixed |

---

## 📝 Critical Notes

1. **Phase A is the KEY FIX** - unifying basis vectors should resolve 90% of the issue
2. **Test after EACH phase** - don't batch changes
3. **The hardcoded vectors are PROVEN CORRECT** by 99.3% correlation
4. **Don't change the hardcoded path** - it's already working
5. **Focus on making calculated path match hardcoded path**

**PRIMARY GOAL**: Make all three code paths use the SAME correct basis vectors:
- `fdet = [0, 0, 1]` (Fast along +Z)
- `sdet = [0, -1, 0]` (Slow along -Y)  
- `odet = [1, 0, 0]` (Normal along +X)